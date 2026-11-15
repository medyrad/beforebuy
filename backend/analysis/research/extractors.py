import json
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import urlsplit


EXTRACTOR_VERSION = "MARKET-OFFER-v2"


class ExtractionError(Exception):
    pass


@dataclass(frozen=True)
class ExtractedProduct:
    brand: str | None
    model_name: str


@dataclass(frozen=True)
class ExtractedVariant:
    identifiers: dict
    attributes: dict


@dataclass(frozen=True)
class ExtractedOffer:
    item_price_minor: int | None
    currency: str | None
    price_toman: int | None
    shipping_minor: int | None
    mandatory_charges_minor: int | None
    total_payable_minor: int | None
    seller: str | None
    availability: str
    merchant_url: str | None
    observation_kind: str
    warranty: str | None = None
    condition: str = "NEW"


@dataclass(frozen=True)
class ExtractedClaim:
    field: str
    value: object
    source_url: str
    source_role: str
    source_location: str


@dataclass(frozen=True)
class ExtractionResult:
    product: ExtractedProduct
    variant: ExtractedVariant
    offers: tuple[ExtractedOffer, ...]
    claims: tuple[ExtractedClaim, ...]

    @property
    def offer(self):
        return self.offers[0] if self.offers else None


class _JsonLdParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = False
        self.buffer = []
        self.documents = []

    def handle_starttag(self, tag, attrs):
        if tag == "script" and dict(attrs).get("type", "").lower() == "application/ld+json":
            self.active = True
            self.buffer = []

    def handle_endtag(self, tag):
        if tag == "script" and self.active:
            self.documents.append("".join(self.buffer))
            self.active = False

    def handle_data(self, data):
        if self.active:
            self.buffer.append(data)


class _VisibleTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.fragments = []

    def handle_data(self, data):
        value = " ".join(data.split())
        if value:
            self.fragments.append(value)


class _NextDataParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = False
        self.buffer = []
        self.documents = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "script" and values.get("id") == "__NEXT_DATA__":
            self.active = True
            self.buffer = []

    def handle_endtag(self, tag):
        if tag == "script" and self.active:
            self.documents.append("".join(self.buffer))
            self.active = False

    def handle_data(self, data):
        if self.active:
            self.buffer.append(data)


def _digits(value):
    table = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    return value.translate(table).replace("٬", ",").replace("٫", ",").replace("،", ",")


def parse_money(value):
    text = _digits(str(value)).strip()
    lowered = text.lower()
    if any(marker in lowered for marker in (" usd", "$", "ناموجود", " تا ", "از ")):
        raise ExtractionError("AMBIGUOUS_OR_UNSUPPORTED_MONEY")
    if "." in text:
        raise ExtractionError("AMBIGUOUS_DECIMAL_SEPARATOR")
    match = re.fullmatch(r"\s*([0-9]{1,3}(?:,[0-9]{3})*|[0-9]+)\s*(تومان|ریال|irt|irr)\s*", lowered)
    if not match:
        raise ExtractionError("INVALID_MONEY")
    amount = int(match.group(1).replace(",", ""))
    currency = match.group(2)
    if currency in {"ریال", "irr"}:
        if amount % 10:
            raise ExtractionError("RIAL_NOT_WHOLE_TOMAN")
        amount //= 10
    return amount, "TOMAN"


def _parse_source_money(value, currency):
    code = str(currency).strip().upper()
    if code not in {"IRR", "IRT", "TOMAN"}:
        raise ExtractionError("AMBIGUOUS_OR_UNSUPPORTED_MONEY")
    text = _digits(str(value)).strip().replace(",", "")
    if not re.fullmatch(r"[0-9]+", text):
        raise ExtractionError("INVALID_MONEY")
    original = int(text)
    if code == "IRR":
        if original % 10:
            raise ExtractionError("RIAL_NOT_WHOLE_TOMAN")
        normalized = original // 10
    else:
        normalized = original
    return original, code, normalized


def _model_code(name):
    match = re.search(r"\b([A-Za-z]{1,8}[- ]?\d{2,6}(?:/[A-Za-z0-9]+)?)\b", name)
    return match.group(1).replace(" ", "-").upper() if match else None


def _normalized_brand(value, name):
    text = " ".join(str(value or "").split())
    haystack = f"{text} {name}".casefold()
    aliases = {
        "فیلیپس": "Philips", "philips": "Philips", "سامسونگ": "Samsung", "samsung": "Samsung",
        "نوکیا": "Nokia", "nokia": "Nokia", "پاکشوما": "Pakshoma", "pakshoma": "Pakshoma",
    }
    for marker, canonical in aliases.items():
        if marker in haystack:
            return canonical
    return text or None


def _extract_torob(text, *, source_url, source_role):
    match = re.search(r'<script[^>]*id=["\']__NEXT_DATA__["\'][^>]*>(.*?)(?:</script>|\Z)', text, re.S)
    if not match:
        raise ExtractionError("TOROB_NEXT_DATA_MISSING")
    raw = match.group(1)
    try:
        try:
            document = json.loads(raw)
        except json.JSONDecodeError as first_error:
            if first_error.pos < len(raw) - 1 or not raw.rstrip().endswith("}"):
                raise
            document = json.loads(raw + "}}")
        page = document["props"]["pageProps"]
        product = page["baseProduct"]
        rows = (page.get("products_info") or product.get("products_info"))["result"]
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ExtractionError("TOROB_LAYOUT_CHANGED") from exc
    name = str(product.get("name1") or product.get("name") or "").strip()
    if not name or not isinstance(rows, list) or not rows:
        raise ExtractionError("TOROB_LAYOUT_CHANGED")
    specifications = product.get("structural_specs") or {}
    general = next((item.get("specs", {}) for item in specifications.get("headers", [])
                    if item.get("header") == "مشخصات کلی"), {})
    brand = _normalized_brand(product.get("brand_name") or product.get("brand") or general.get("سازنده"), name)
    model = str(product.get("model") or general.get("مدل") or "").strip()
    identifiers = {"torob_product": str(product.get("random_key") or urlsplit(source_url).path.split("/")[2])}
    code = _model_code(model or name)
    if code and "mpn" not in identifiers:
        identifiers["model_code"] = code
    offers = []
    claims = [ExtractedClaim("name", name, source_url, source_role, "next:baseProduct.name1")]
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ExtractionError("TOROB_LAYOUT_CHANGED")
        seller = str(row.get("shop_name") or "").strip()
        label = str(row.get("price_string") or "").strip()
        if not seller or "تومان" not in label:
            raise ExtractionError("TOROB_PRICE_UNIT_MISSING")
        normalized, _ = parse_money(label)
        raw = row.get("price")
        if raw is not None and int(raw) != normalized:
            raise ExtractionError("TOROB_PRICE_CONFLICT")
        availability = "IN_STOCK" if row.get("availability") not in {False, 0, "false"} else "OUT_OF_STOCK"
        offers.append(ExtractedOffer(
            normalized, "IRT", normalized, None, None, None, seller, availability,
            str(row.get("page_url") or "").strip() or None, "COMPARISON_OBSERVED",
            str(row.get("warranty") or "").strip() or None,
        ))
        claims.append(ExtractedClaim("item_price", {"value": normalized, "unit": "TOMAN"}, source_url,
                                     source_role, f"next:products_info.result[{index}].price_string"))
    return ExtractionResult(ExtractedProduct(brand, name), ExtractedVariant(identifiers, {}), tuple(offers), tuple(claims))


def _product_documents(value):
    if isinstance(value, list):
        for item in value:
            yield from _product_documents(item)
    elif isinstance(value, dict):
        if value.get("@type") == "Product" or "Product" in value.get("@type", []):
            yield value
        for item in value.get("@graph", []):
            yield from _product_documents(item)


def extract_product_document(document, *, source_url, source_role, retrieved_at):
    try:
        text = document.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ExtractionError("INVALID_UTF8") from exc
    if urlsplit(source_url).hostname in {"torob.com", "www.torob.com"}:
        return _extract_torob(text, source_url=source_url, source_role=source_role)
    parser = _JsonLdParser()
    parser.feed(text)
    products = []
    for raw in parser.documents:
        try:
            products.extend(_product_documents(json.loads(raw)))
        except json.JSONDecodeError:
            continue
    if len(products) != 1:
        raise ExtractionError("PRODUCT_SCHEMA_MISSING_OR_AMBIGUOUS")
    data = products[0]
    name = str(data.get("name", "")).strip()
    if not name:
        raise ExtractionError("PRODUCT_NAME_MISSING")
    brand_value = data.get("brand")
    brand = brand_value.get("name") if isinstance(brand_value, dict) else brand_value
    brand = _normalized_brand(brand, name)
    identifiers = {
        key: str(data[key]).strip()
        for key in ("sku", "mpn", "gtin13", "gtin")
        if data.get(key) not in (None, "")
    }
    code = _model_code(name)
    if code and "mpn" not in identifiers:
        identifiers["model_code"] = code
    claims = [ExtractedClaim("name", name, source_url, source_role, "jsonld:Product.name")]
    for key, value in identifiers.items():
        claims.append(ExtractedClaim(key, value, source_url, source_role, f"jsonld:Product.{key}"))
    offer_data = data.get("offers")
    if isinstance(offer_data, list):
        if len(offer_data) != 1:
            raise ExtractionError("PRICE_RANGE_OR_MULTIPLE_OFFERS")
        offer_data = offer_data[0]
    offers = []
    if isinstance(offer_data, dict):
        price = currency = price_toman = None
        if offer_data.get("price") is not None:
            raw_currency = str(offer_data.get("priceCurrency", "")).upper()
            price, currency, price_toman = _parse_source_money(offer_data["price"], raw_currency)
        availability_url = str(offer_data.get("availability", ""))
        availability = {
            "InStock": "IN_STOCK",
            "OutOfStock": "OUT_OF_STOCK",
            "PreOrder": "PREORDER",
        }.get(availability_url.rsplit("/", 1)[-1], "UNKNOWN")
        seller_data = offer_data.get("seller")
        seller = seller_data.get("name") if isinstance(seller_data, dict) else None
        merchant_url = str(offer_data.get("url") or source_url).strip()
        offers.append(ExtractedOffer(price, currency, price_toman, None, None, None, seller, availability,
                                     merchant_url, "MERCHANT_PAGE_VERIFIED"))
        if price is not None:
            claims.append(ExtractedClaim("item_price", {"value": price_toman, "unit": "TOMAN", "source_value": price,
                                                        "source_currency": currency}, source_url, source_role, "jsonld:Product.offers.price"))
    elif urlsplit(source_url).hostname == "www.technolife.com":
        visible = _VisibleTextParser()
        visible.feed(text)
        if "ناموجود" in visible.fragments:
            offers.append(ExtractedOffer(None, None, None, None, None, None, None, "OUT_OF_STOCK",
                                         source_url, "MERCHANT_PAGE_VERIFIED"))
            claims.append(
                ExtractedClaim(
                    "availability", "OUT_OF_STOCK", source_url, source_role,
                    'html:text-node[exact="ناموجود"]',
                )
            )
    return ExtractionResult(
        ExtractedProduct(brand, name),
        ExtractedVariant(identifiers, {}),
        tuple(offers),
        tuple(claims),
    )

import json
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import urlsplit


EXTRACTOR_VERSION = "JSONLD-PRODUCT-v1"


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
    shipping_minor: int | None
    total_payable_minor: int | None
    seller: str | None
    availability: str


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
    offer: ExtractedOffer | None
    claims: tuple[ExtractedClaim, ...]


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


def _digits(value):
    table = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    return value.translate(table).replace("٬", ",").replace("،", ",")


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
    identifiers = {
        key: str(data[key]).strip()
        for key in ("sku", "mpn", "gtin13", "gtin")
        if data.get(key) not in (None, "")
    }
    claims = [ExtractedClaim("name", name, source_url, source_role, "jsonld:Product.name")]
    for key, value in identifiers.items():
        claims.append(ExtractedClaim(key, value, source_url, source_role, f"jsonld:Product.{key}"))
    offer_data = data.get("offers")
    if isinstance(offer_data, list):
        if len(offer_data) != 1:
            raise ExtractionError("PRICE_RANGE_OR_MULTIPLE_OFFERS")
        offer_data = offer_data[0]
    offer = None
    if isinstance(offer_data, dict):
        price = currency = None
        if offer_data.get("price") is not None:
            raw_currency = str(offer_data.get("priceCurrency", "")).upper()
            price, currency = parse_money(f"{offer_data['price']} {raw_currency}")
        availability_url = str(offer_data.get("availability", ""))
        availability = {
            "InStock": "IN_STOCK",
            "OutOfStock": "OUT_OF_STOCK",
            "PreOrder": "PREORDER",
        }.get(availability_url.rsplit("/", 1)[-1], "UNKNOWN")
        seller_data = offer_data.get("seller")
        seller = seller_data.get("name") if isinstance(seller_data, dict) else None
        offer = ExtractedOffer(price, currency, None, None, seller, availability)
        if price is not None:
            claims.append(ExtractedClaim("item_price", {"value": price, "unit": currency}, source_url, source_role, "jsonld:Product.offers.price"))
    elif urlsplit(source_url).hostname == "www.technolife.com":
        visible = _VisibleTextParser()
        visible.feed(text)
        if "ناموجود" in visible.fragments:
            offer = ExtractedOffer(None, None, None, None, None, "OUT_OF_STOCK")
            claims.append(
                ExtractedClaim(
                    "availability", "OUT_OF_STOCK", source_url, source_role,
                    'html:text-node[exact="ناموجود"]',
                )
            )
    return ExtractionResult(
        ExtractedProduct(str(brand).strip() if brand else None, name),
        ExtractedVariant(identifiers, {}),
        offer,
        tuple(claims),
    )

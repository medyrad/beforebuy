from datetime import datetime, UTC
import json
from pathlib import Path
from unittest import TestCase

from analysis.research.extractors import ExtractionError, extract_product_document, parse_money


class ExtractorTests(TestCase):
    def test_jsonld_product_extracts_literal_expected_identity_and_provenance(self):
        document = '''<script type="application/ld+json">{
          "@context":"https://schema.org", "@type":"Product",
          "name":"Galaxy A56", "sku":"99474", "mpn":"SM-A566B",
          "brand":{"@type":"Brand","name":"Samsung"},
          "offers":{"@type":"Offer","price":"۱۱۳٬۸۰۰٬۰۰۰","priceCurrency":"IRT","availability":"https://schema.org/OutOfStock","seller":{"name":"فروشنده نمونه"}}
        }</script>'''.encode("utf-8")
        result = extract_product_document(
            document,
            source_url="https://merchant.example/p/a56",
            source_role="MERCHANT",
            retrieved_at=datetime(2026, 11, 15, tzinfo=UTC),
        )
        self.assertEqual(result.product.brand, "Samsung")
        self.assertEqual(result.variant.identifiers, {"sku": "99474", "mpn": "SM-A566B"})
        self.assertEqual(result.offer.item_price_minor, 113_800_000)
        self.assertEqual(result.offer.currency, "IRT")
        self.assertEqual(result.offer.price_toman, 113_800_000)
        self.assertEqual(result.offer.availability, "OUT_OF_STOCK")
        self.assertIsNone(result.offer.shipping_minor)
        self.assertIsNone(result.offer.total_payable_minor)
        self.assertEqual(result.claims[0].source_url, "https://merchant.example/p/a56")
        self.assertEqual(result.claims[0].source_location, "jsonld:Product.name")

    def test_money_handles_persian_arabic_latin_rial_toman_and_rejects_ambiguity(self):
        self.assertEqual(parse_money("۱٬۲۵۰٬۰۰۰ تومان"), (1_250_000, "TOMAN"))
        self.assertEqual(parse_money("۱۲,۵۰۰,۰۰۰ ریال"), (1_250_000, "TOMAN"))
        self.assertEqual(parse_money("1,250,000 IRT"), (1_250_000, "TOMAN"))
        for value in ("1.250.000", "از ۱ تا ۲ میلیون تومان", "120 USD", "ناموجود"):
            with self.subTest(value=value), self.assertRaises(ExtractionError):
                parse_money(value)

    def test_malformed_or_missing_product_schema_fails_explicitly(self):
        for document in (b"<html></html>", b'<script type="application/ld+json">{broken</script>'):
            with self.assertRaises(ExtractionError):
                extract_product_document(
                    document,
                    source_url="https://manufacturer.example/p/1",
                    source_role="MANUFACTURER",
                    retrieved_at=datetime(2026, 11, 15, tzinfo=UTC),
                )

    def test_captured_real_fixtures_have_independently_authored_expected_values(self):
        fixture_dir = Path(__file__).parents[1] / "fixtures" / "research"
        philips = extract_product_document(
            (fixture_dir / "philips-ep5934-minimal.html").read_bytes(),
            source_url="https://www.philips.com/c-p/EP5934_10R1/series-5000-fully-automatic-espresso-machines/overview",
            source_role="MANUFACTURER",
            retrieved_at=datetime(2026, 11, 15, tzinfo=UTC),
        )
        technolife = extract_product_document(
            (fixture_dir / "technolife-a56-minimal.html").read_bytes(),
            source_url="https://www.technolife.com/product-99474/galaxy-a56-5g-256-8",
            source_role="MERCHANT",
            retrieved_at=datetime(2026, 11, 15, tzinfo=UTC),
        )
        self.assertEqual(philips.variant.identifiers["mpn"], "EP5934/10R1")
        self.assertEqual(philips.product.brand, "Philips")
        self.assertIsNone(philips.offer)
        self.assertEqual(technolife.variant.identifiers["sku"], "99474")
        self.assertEqual(technolife.offer.availability, "OUT_OF_STOCK")
        self.assertIsNone(technolife.offer.item_price_minor)

    def test_direct_offer_keeps_original_currency_and_converts_explicit_rial(self):
        document = b'''<script type="application/ld+json">{
          "@type":"Product", "name":"Philips NA230", "mpn":"NA230/00",
          "brand":{"name":"Philips"},
          "offers":{"@type":"Offer","price":"239900000","priceCurrency":"IRR",
          "availability":"https://schema.org/InStock","seller":{"name":"Takkalaban"},
          "url":"https://takkalaban.com/product/philips-na230/"}
        }</script>'''
        result = extract_product_document(
            document, source_url="https://takkalaban.com/product/philips-na230/",
            source_role="MERCHANT", retrieved_at=datetime(2026, 11, 15, tzinfo=UTC),
        )
        self.assertEqual(result.offer.currency, "IRR")
        self.assertEqual(result.offer.item_price_minor, 239_900_000)
        self.assertEqual(result.offer.price_toman, 23_990_000)
        self.assertEqual(result.offer.merchant_url, "https://takkalaban.com/product/philips-na230/")
        self.assertEqual(result.offer.observation_kind, "MERCHANT_PAGE_VERIFIED")
        self.assertIsNone(result.offer.shipping_minor)
        self.assertIsNone(result.offer.mandatory_charges_minor)
        self.assertIsNone(result.offer.total_payable_minor)

    def test_direct_product_uses_explicit_name_brand_and_model_code_without_merchant_sku(self):
        document = '''<script type="application/ld+json">{
          "@type":"Product", "name":"سرخ کن بدون روغن فیلیپس مدل NA230",
          "sku":"merchant-only-77",
          "offers":{"@type":"Offer","price":"24466434","priceCurrency":"IRT"}
        }</script>'''.encode()
        result = extract_product_document(
            document, source_url="https://bkalaa.com/product/na230/", source_role="MERCHANT",
            retrieved_at=datetime(2026, 11, 15, tzinfo=UTC),
        )
        self.assertEqual(result.product.brand, "Philips")
        self.assertEqual(result.variant.identifiers["model_code"], "NA230")
        self.assertEqual(result.variant.identifiers["sku"], "merchant-only-77")

    def test_torob_next_data_extracts_distinct_comparison_sellers(self):
        payload = {
            "props": {"pageProps": {
                "baseProduct": {"name1": "تلویزیون سامسونگ Q60D 55", "brand_name": "Samsung", "model": "Q60D 55"},
                "products_info": {"result": [
                    {"shop_name": "فروشگاه یک", "price": 52_300_000, "price_string": "۵۲٬۳۰۰٬۰۰۰ تومان", "availability": True, "page_url": "https://torob.com/redirect/a"},
                    {"shop_name": "فروشگاه دو", "price": 53_100_000, "price_string": "۵۳٬۱۰۰٬۰۰۰ تومان", "availability": True, "page_url": "https://torob.com/redirect/b"}
                ]}
            }}
        }
        document = f'<script id="__NEXT_DATA__" type="application/json">{json.dumps(payload, ensure_ascii=False)}</script>'.encode()
        result = extract_product_document(
            document, source_url="https://torob.com/p/bb037069-fba8-4964-a758-6adcec22898f/q60d/",
            source_role="COMPARISON", retrieved_at=datetime(2026, 11, 15, tzinfo=UTC),
        )
        self.assertEqual(result.product.brand, "Samsung")
        self.assertEqual(len(result.offers), 2)
        self.assertEqual([offer.seller for offer in result.offers], ["فروشگاه یک", "فروشگاه دو"])
        self.assertTrue(all(offer.observation_kind == "COMPARISON_OBSERVED" for offer in result.offers))
        self.assertEqual(result.offers[0].price_toman, 52_300_000)

    def test_torob_layout_drift_and_invalid_money_fail_explicitly(self):
        cases = [
            b'<script id="__NEXT_DATA__" type="application/json">{"props":{"pageProps":{}}}</script>',
            '<script id="__NEXT_DATA__" type="application/json">{"props":{"pageProps":{"baseProduct":{"name1":"x"},"products_info":{"result":[{"shop_name":"s","price":10,"price_string":"10 USD"}]}}}}</script>'.encode(),
        ]
        for document in cases:
            with self.subTest(document=document), self.assertRaises(ExtractionError):
                extract_product_document(
                    document, source_url="https://torob.com/p/11111111-1111-4111-8111-111111111111/x/",
                    source_role="COMPARISON", retrieved_at=datetime(2026, 11, 15, tzinfo=UTC),
                )

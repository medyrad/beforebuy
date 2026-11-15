from datetime import datetime, UTC
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
        self.assertEqual(result.offer.currency, "TOMAN")
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

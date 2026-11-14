from django.test import SimpleTestCase

from analysis.domain import money


class MoneyNormalizationTests(SimpleTestCase):
    def api(self, name):
        self.assertTrue(hasattr(money, name), f"money.{name} is not implemented")
        return getattr(money, name)

    def test_equivalent_valid_groupings_normalize_to_literal_toman(self):
        normalize_toman = self.api("normalize_toman")
        for raw in ["۱۲٬۵۰۰٬۰۰۰", "12,500,000", "12 500 000", "۱۲۵۰۰۰۰۰"]:
            with self.subTest(raw=raw):
                self.assertEqual(normalize_toman(raw, allow_zero=False), 12_500_000)

    def test_zero_budget_is_valid_but_zero_price_is_rejected(self):
        normalize_toman = self.api("normalize_toman")
        error = self.api("MoneyValidationError")
        self.assertEqual(normalize_toman(0, allow_zero=True), 0)
        with self.assertRaises(error) as caught:
            normalize_toman(0, allow_zero=False)
        self.assertEqual(caught.exception.code, "NON_POSITIVE_PRICE")

    def test_unknown_budget_is_not_zero(self):
        normalize_budget = self.api("normalize_budget")
        self.assertIsNone(normalize_budget(None))
        self.assertEqual(normalize_budget("UNKNOWN"), None)

    def test_invalid_classes_are_not_silently_corrected(self):
        cases = {
            "12,50,000": "MALFORMED_AMOUNT",
            "12,۵۰۰,000": "MIXED_GROUPING",
            "1.5": "DECIMAL_AMOUNT",
            "1e7": "SCIENTIFIC_NOTATION",
            "100 دلار": "AMBIGUOUS_CURRENCY",
            "-20": "NEGATIVE_AMOUNT",
        }
        normalize_toman = self.api("normalize_toman")
        error = self.api("MoneyValidationError")
        for raw, code in cases.items():
            with self.subTest(raw=raw), self.assertRaises(error) as caught:
                normalize_toman(raw, allow_zero=True)
            self.assertEqual(caught.exception.code, code)

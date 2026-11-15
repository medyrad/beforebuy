from django.test import SimpleTestCase

from analysis.conversation.brief import normalize_digits, normalize_money_toman, validate_brief_changes


class BriefBuilderTests(SimpleTestCase):
    def test_persian_arabic_and_latin_digits_normalize(self):
        self.assertEqual(normalize_digits("۷۰٬٥٠٠,000"), "70٬500,000")
        self.assertEqual(normalize_money_toman("۷۰٬٥٠٠,000 تومان"), 70_500_000)

    def test_zero_is_not_unknown(self):
        self.assertEqual(normalize_money_toman("۰"), 0)
        self.assertIsNone(normalize_money_toman(""))

    def test_category_neutral_context_and_contradictions_are_explicit(self):
        for context in ("SELF", "GIFT", "HOUSEHOLD"):
            with self.subTest(context=context):
                changes = validate_brief_changes({
                    "recipient_context": context,
                    "category": "کالای انتخابی",
                    "budget_toman": 0,
                    "use_cases": ["کاربرد ثبت‌شده"],
                    "hard_constraints": ["سبک", "سنگین"],
                    "contradictions": ["سبک و سنگین هم‌زمان"],
                    "unknowns": ["مدل هدف نامعلوم"],
                })
                self.assertEqual(changes["recipient_context"], context)
                self.assertEqual(changes["budget_toman"], 0)
                self.assertEqual(changes["hard_constraints"], ["سبک", "سنگین"])
                self.assertEqual(changes["contradictions"], ["سبک و سنگین هم‌زمان"])
                self.assertEqual(changes["unknowns"], ["مدل هدف نامعلوم"])

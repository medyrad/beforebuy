from datetime import timedelta

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from analysis import models


class PersistenceConstraintTests(TestCase):
    def setUp(self):
        self.assertTrue(hasattr(models, "GuestContext"), "GuestContext is not implemented")
        self.guest = models.GuestContext.objects.create(access_expires_at=timezone.now() + timedelta(days=90))

    def analysis(self, **overrides):
        values = {
            "guest_context": self.guest,
            "product_label": "گوشی نمونه",
            "price_toman": 10,
            "budget_toman": 0,
            "answers": {},
            "expires_at": timezone.now() + timedelta(days=90),
        }
        values.update(overrides)
        return models.Analysis.objects.create(**values)

    def test_guest_defaults_to_generation_epoch_zero(self):
        self.assertEqual(self.guest.generation_epoch, 0)

    def test_price_must_be_positive(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.analysis(price_toman=0)

    def test_budget_is_null_or_nonnegative(self):
        self.assertIsNone(self.analysis(budget_toman=None).budget_toman)
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.analysis(budget_toman=-1)

    def test_product_label_is_limited_to_120_characters_by_validation(self):
        item = models.Analysis(
            guest_context=self.guest, product_label="م" * 121, price_toman=1, budget_toman=None,
            answers={}, expires_at=timezone.now() + timedelta(days=90)
        )
        with self.assertRaises(Exception):
            item.full_clean()

    def test_feedback_rating_must_be_between_one_and_five(self):
        analysis = self.analysis()
        report = models.CurrentReport.objects.create(
            analysis=analysis, input_revision=1, rubric_id="PDA-CAT-v0.3", mode="MOCK_ASSISTED",
            primary_outcome="INSUFFICIENT_CONTEXT", dimensions={}, matched_rule_ids=[], evidence=[],
            unknowns=[], actions=[], headline_fa="آزمایشی", explanation_blocks=[], canonical_hash="x" * 64,
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            models.UsefulnessFeedback.objects.create(
                analysis=analysis, report_revision_id=report.report_revision_id,
                report_mode=report.mode, rating=6,
            )

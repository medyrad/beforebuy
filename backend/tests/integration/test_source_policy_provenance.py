from datetime import datetime, timezone
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from analysis.models import SourcePolicy


class SourceReviewProvenanceTests(TestCase):
    def test_toggles_preserve_real_review_dates_and_readiness(self):
        reviewed = datetime(2026, 11, 14, 10, tzinfo=timezone.utc)
        source = SourcePolicy.objects.create(
            hostname='torob.com', source_role='COMPARISON', readiness='CAPTURED_REAL_FIXTURE',
            robots_observed_at=reviewed, terms_observed_at=reviewed,
            access_notes='Original reviewed evidence and unresolved questions')
        for flag in ('--enable', '--disable', '--enable', '--disable'):
            call_command('configure_market_sources', flag, stdout=StringIO())
            source.refresh_from_db()
            self.assertEqual(source.robots_observed_at, reviewed)
            self.assertEqual(source.terms_observed_at, reviewed)
            self.assertEqual(source.readiness, 'CAPTURED_REAL_FIXTURE')
            self.assertEqual(source.access_notes, 'Original reviewed evidence and unresolved questions')
            self.assertEqual(source.live_enabled, flag == '--enable')

    def test_new_policy_has_no_invented_exact_observation_timestamp(self):
        call_command('configure_market_sources', '--disable', stdout=StringIO())
        source = SourcePolicy.objects.get(hostname='torob.com')
        self.assertIsNone(source.robots_observed_at)
        self.assertIsNone(source.terms_observed_at)
        self.assertIn('2026-11-15', source.access_notes)

import threading

from django.db import close_old_connections
from django.test import TransactionTestCase
from django.utils import timezone

from analysis.ai.contracts import ExplanationResponse
from analysis.models import GuestContext, UsefulnessFeedback
from analysis import services
from tests.api.payloads import valid_analysis_payload


class BlockingGenerator:
    def __init__(self, started, release, headline="جدید"):
        self.started = started
        self.release = release
        self.headline = headline

    def generate(self, request):
        self.started.set()
        if not self.release.wait(timeout=10):
            raise AssertionError("test barrier was not released")
        return ExplanationResponse(
            mode="MOCK_ASSISTED", outcome_id=request.primary_outcome,
            acknowledged_unknown_ids=request.unknowns, headline_fa=self.headline, claims=[]
        )


class ImmediateGenerator:
    def __init__(self, headline):
        self.headline = headline

    def generate(self, request):
        return ExplanationResponse(
            mode="MOCK_ASSISTED", outcome_id=request.primary_outcome,
            acknowledged_unknown_ids=request.unknowns, headline_fa=self.headline, claims=[]
        )


class PublicationRaceTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.guest = GuestContext.objects.create(access_expires_at=timezone.now() + timezone.timedelta(days=90))

    def run_thread(self, target):
        errors = []
        def runner():
            close_old_connections()
            try:
                target()
            except Exception as exc:  # captured for deterministic assertion in the main thread
                errors.append(exc)
            finally:
                close_old_connections()
        thread = threading.Thread(target=runner)
        thread.start()
        return thread, errors

    def test_clear_history_invalidates_initial_create_without_analysis_row(self):
        self.assertTrue(hasattr(services, "clear_history"), "clear_history is not implemented")
        started, release = threading.Event(), threading.Event()
        thread, errors = self.run_thread(lambda: services.create_analysis(
            self.guest, services.normalize_input(valid_analysis_payload()), BlockingGenerator(started, release)
        ))
        self.assertTrue(started.wait(timeout=10))
        services.clear_history(self.guest)
        release.set(); thread.join(timeout=10)
        self.assertFalse(thread.is_alive())
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], services.OperationConflict)
        self.assertEqual(self.guest.analyses.count(), 0)

    def test_older_retry_cannot_overwrite_newer_retry_or_feedback(self):
        self.assertTrue(hasattr(services, "reanalyze_analysis"), "reanalyze_analysis is not implemented")
        item = services.create_analysis(self.guest, services.normalize_input(valid_analysis_payload()))
        UsefulnessFeedback.objects.create(
            analysis=item, report_revision_id=item.report.report_revision_id,
            report_mode=item.report.mode, rating=4,
        )
        old_report_id = item.report.report_revision_id
        started, release = threading.Event(), threading.Event()
        thread, errors = self.run_thread(lambda: services.reanalyze_analysis(
            self.guest, item.id, 1, old_report_id, BlockingGenerator(started, release, "قدیمی")
        ))
        self.assertTrue(started.wait(timeout=10))
        winner = services.reanalyze_analysis(self.guest, item.id, 1, old_report_id, ImmediateGenerator("جدید"))
        release.set(); thread.join(timeout=10)
        self.assertEqual(winner.report.headline_fa, "جدید")
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], services.OperationConflict)
        self.assertFalse(UsefulnessFeedback.objects.filter(analysis=item).exists())

    def test_delete_during_retry_prevents_resurrection(self):
        item = services.create_analysis(self.guest, services.normalize_input(valid_analysis_payload()))
        old_report_id = item.report.report_revision_id
        started, release = threading.Event(), threading.Event()
        thread, errors = self.run_thread(lambda: services.reanalyze_analysis(
            self.guest, item.id, 1, old_report_id, BlockingGenerator(started, release)
        ))
        self.assertTrue(started.wait(timeout=10))
        services.delete_analysis(self.guest, item.id)
        release.set(); thread.join(timeout=10)
        self.assertFalse(thread.is_alive())
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], services.AnalysisNotFound)
        self.assertFalse(self.guest.analyses.filter(id=item.id).exists())

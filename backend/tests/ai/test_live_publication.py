import json
import threading

from django.db import close_old_connections
from django.test import TransactionTestCase
from django.utils import timezone

from analysis import services
from analysis.ai.openai_adapter import OpenAIExplanationGenerator, ProviderResult, ProviderUsage
from analysis.models import GuestContext
from tests.ai.test_openai_adapter import valid_payload
from tests.api.payloads import valid_analysis_payload


class BlockingProviderTransport:
    def __init__(self, started, release):
        self.started = started
        self.release = release

    def create(self, **kwargs):
        self.started.set()
        if not self.release.wait(timeout=10):
            raise AssertionError("provider test barrier was not released")
        return ProviderResult(json.dumps(valid_payload()), ProviderUsage(100, 20))


class LiveAdapterPublicationTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.guest = GuestContext.objects.create(access_expires_at=timezone.now() + timezone.timedelta(days=90))
        self.data = services.normalize_input(valid_analysis_payload())

    def start_operation(self, operation):
        errors = []

        def runner():
            close_old_connections()
            try:
                operation()
            except Exception as exc:
                errors.append(exc)
            finally:
                close_old_connections()

        thread = threading.Thread(target=runner)
        thread.start()
        return thread, errors

    def blocking_generator(self, started, release):
        return OpenAIExplanationGenerator(
            transport=BlockingProviderTransport(started, release), sleeper=lambda _seconds: None
        )

    def test_clear_history_during_live_initial_call_prevents_late_publication(self):
        started, release = threading.Event(), threading.Event()
        thread, errors = self.start_operation(lambda: services.create_analysis(
            self.guest, self.data, self.blocking_generator(started, release)
        ))
        self.assertTrue(started.wait(timeout=10))
        services.clear_history(self.guest)
        release.set()
        thread.join(timeout=10)
        self.assertIsInstance(errors[0], services.OperationConflict)
        self.assertFalse(self.guest.analyses.exists())

    def test_delete_during_live_retry_prevents_resurrection(self):
        item = services.create_analysis(self.guest, self.data)
        started, release = threading.Event(), threading.Event()
        thread, errors = self.start_operation(lambda: services.reanalyze_analysis(
            self.guest, item.id, item.input_revision, item.report.report_revision_id,
            self.blocking_generator(started, release),
        ))
        self.assertTrue(started.wait(timeout=10))
        services.delete_analysis(self.guest, item.id)
        release.set()
        thread.join(timeout=10)
        self.assertIsInstance(errors[0], services.AnalysisNotFound)
        self.assertFalse(self.guest.analyses.filter(id=item.id).exists())

    def test_expiry_during_live_retry_prevents_late_publication(self):
        item = services.create_analysis(self.guest, self.data)
        started, release = threading.Event(), threading.Event()
        thread, errors = self.start_operation(lambda: services.reanalyze_analysis(
            self.guest, item.id, item.input_revision, item.report.report_revision_id,
            self.blocking_generator(started, release),
        ))
        self.assertTrue(started.wait(timeout=10))
        item.expires_at = timezone.now() - timezone.timedelta(seconds=1)
        item.save(update_fields=["expires_at"])
        release.set()
        thread.join(timeout=10)
        self.assertIsInstance(errors[0], services.AnalysisNotFound)
        item.report.refresh_from_db()
        self.assertEqual(item.report.mode, "MOCK_ASSISTED")

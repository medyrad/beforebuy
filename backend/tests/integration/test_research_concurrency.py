import threading
from datetime import timedelta
from unittest.mock import patch

from django.test import Client, TransactionTestCase, override_settings
from django.utils import timezone

from analysis.models import Conversation, GuestContext, ResearchJob


@override_settings(BEFOREBUY_RESEARCH_MODE="FIXTURE")
class ResearchAdmissionConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.guest = GuestContext.objects.create(access_expires_at=timezone.now() + timedelta(days=90))
        self.first = Conversation.objects.create_for_guest(self.guest)
        self.second = Conversation.objects.create_for_guest(self.guest)
        for conversation in (self.first, self.second):
            conversation.brief.confirmed = True
            conversation.brief.save(update_fields=["confirmed"])
        client = Client()
        session = client.session
        session["guest_context_id"] = str(self.guest.id)
        session.save()
        self.session_cookie = client.cookies["sessionid"].value

    def test_two_real_api_requests_admit_only_one_guest_wide_job(self):
        barrier = threading.Barrier(2)
        results = []
        lock = threading.Lock()

        def start(conversation, key, source):
            client = Client()
            client.cookies["sessionid"] = self.session_cookie
            barrier.wait(timeout=5)
            response = client.post(
                f"/api/v1/conversations/{conversation.id}/research",
                {"expected_brief_revision": 0, "targets": [{"source_id": source}]},
                content_type="application/json", HTTP_IDEMPOTENCY_KEY=key,
            )
            with lock:
                results.append(response.status_code)

        with (patch("analysis.api.research.reserve_research_slot", return_value=True),
              patch("analysis.api.research.release_research_slot"),
              patch("analysis.api.research.submit_research_reserved", return_value=True)):
            threads = [
                threading.Thread(target=start, args=(self.first, "concurrent-research-key-001", "synthetic-appliance-v1")),
                threading.Thread(target=start, args=(self.second, "concurrent-research-key-002", "synthetic-electronics-v1")),
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(10)
                self.assertFalse(thread.is_alive())

        self.assertEqual(sorted(results), [202, 429])
        self.assertEqual(ResearchJob.objects.filter(status__in=["PENDING", "RUNNING"]).count(), 1)

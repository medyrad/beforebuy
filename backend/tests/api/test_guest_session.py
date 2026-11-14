from datetime import timedelta

from django.test import Client, TestCase
from django.utils import timezone

from analysis.models import GuestContext
from .payloads import valid_analysis_payload
from .test_analysis_create_read import csrf_client


class GuestSessionLifetimeTests(TestCase):
    def test_bootstrap_creates_opaque_context_and_90_day_access(self):
        before = timezone.now()
        client = Client()
        response = client.get("/api/v1/session")
        self.assertEqual(response.status_code, 200, "session bootstrap is not implemented")
        guest = GuestContext.objects.get()
        self.assertGreaterEqual(guest.access_expires_at, before + timedelta(days=90) - timedelta(seconds=2))
        self.assertNotIn("guest_context_id", response.json())
        self.assertIn("sessionid", client.cookies)

    def test_independent_clients_receive_different_guest_contexts(self):
        first, second = Client(), Client()
        self.assertEqual(first.get("/api/v1/session").status_code, 200)
        self.assertEqual(second.get("/api/v1/session").status_code, 200)
        self.assertEqual(GuestContext.objects.count(), 2)
        self.assertNotEqual(first.session["guest_context_id"], second.session["guest_context_id"])

    def test_day_89_successful_new_analysis_extends_access_about_90_more_days(self):
        client, token = csrf_client()
        guest = GuestContext.objects.get(id=client.session["guest_context_id"])
        guest.access_expires_at = timezone.now() + timedelta(days=1)
        guest.save(update_fields=["access_expires_at"])

        response = client.post(
            "/api/v1/analyses", valid_analysis_payload(), content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 201)
        guest.refresh_from_db()
        self.assertGreaterEqual(guest.access_expires_at, timezone.now() + timedelta(days=90) - timedelta(seconds=2))

    def test_reads_edits_retries_and_feedback_do_not_slide_guest_access(self):
        client, token = csrf_client()
        created = client.post(
            "/api/v1/analyses", valid_analysis_payload(), content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        ).json()
        guest = GuestContext.objects.get(id=client.session["guest_context_id"])
        marker = timezone.now() + timedelta(days=10)
        guest.access_expires_at = marker
        guest.save(update_fields=["access_expires_at"])
        client.get(f"/api/v1/analyses/{created['id']}")
        client.patch(
            f"/api/v1/analyses/{created['id']}", valid_analysis_payload() | {"expected_input_revision": 1},
            content_type="application/json", HTTP_X_CSRFTOKEN=token,
        )
        refreshed = client.get(f"/api/v1/analyses/{created['id']}").json()
        report_id = refreshed["report"]["report_revision_id"]
        client.post(
            f"/api/v1/analyses/{created['id']}/reanalysis",
            {"expected_input_revision": 2, "expected_report_revision_id": report_id},
            content_type="application/json", HTTP_X_CSRFTOKEN=token,
        )
        client.put(
            f"/api/v1/analyses/{created['id']}/feedback",
            {"report_revision_id": report_id, "rating": 4},
            content_type="application/json", HTTP_X_CSRFTOKEN=token,
        )
        guest.refresh_from_db()
        self.assertEqual(guest.access_expires_at, marker)

    def test_losing_cookie_creates_a_new_context_without_recovery(self):
        owner, token = csrf_client()
        created = owner.post(
            "/api/v1/analyses", valid_analysis_payload(), content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        ).json()
        replacement, _ = csrf_client()
        self.assertEqual(replacement.get(f"/api/v1/analyses/{created['id']}").status_code, 404)

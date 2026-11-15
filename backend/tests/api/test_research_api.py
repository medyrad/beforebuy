from unittest.mock import patch

from django.test import Client, TestCase, override_settings

from analysis.models import ResearchJob, StreamOperation
from analysis.research.jobs import perform_research


def csrf_client():
    client = Client(enforce_csrf_checks=True)
    response = client.get("/api/v1/session")
    assert response.status_code == 200
    return client, client.cookies["csrftoken"].value


@override_settings(BEFOREBUY_RESEARCH_MODE="FIXTURE")
class ResearchApiTests(TestCase):
    def setUp(self):
        self.client, self.token = csrf_client()
        response = self.client.post(
            "/api/v1/conversations", {}, content_type="application/json", HTTP_X_CSRFTOKEN=self.token
        )
        self.conversation = response.json()
        self.client.patch(
            f"/api/v1/conversations/{self.conversation['id']}/brief",
            {
                "expected_revision": 0,
                "changes": {
                    "recipient_context": "SELF",
                    "category": "لوازم خانگی",
                    "budget_toman": 50_000_000,
                    "use_cases": ["مصرف خانگی"],
                },
            },
            content_type="application/json",
            HTTP_X_CSRFTOKEN=self.token,
        )
        self.client.post(
            f"/api/v1/conversations/{self.conversation['id']}/brief/confirm",
            {"expected_revision": 1},
            content_type="application/json",
            HTTP_X_CSRFTOKEN=self.token,
        )

    def post(self, path, data, **extra):
        return self.client.post(
            path, data, content_type="application/json", HTTP_X_CSRFTOKEN=self.token, **extra
        )

    @patch("analysis.api.research.submit_research_reserved", return_value=True)
    @patch("analysis.api.research.release_research_slot")
    @patch("analysis.api.research.reserve_research_slot", return_value=True)
    def test_explicit_start_is_idempotent_and_get_does_not_execute(self, _reserve, _release, submit):
        path = f"/api/v1/conversations/{self.conversation['id']}/research"
        payload = {"expected_brief_revision": 1, "source_ids": ["synthetic-appliance-v1"]}
        with self.captureOnCommitCallbacks(execute=True):
            first = self.post(path, payload, HTTP_IDEMPOTENCY_KEY="research-start-key-001")
        second = self.post(path, payload, HTTP_IDEMPOTENCY_KEY="research-start-key-001")
        self.assertEqual(first.status_code, 202, first.content)
        self.assertEqual(second.status_code, 202, second.content)
        self.assertTrue(second.json()["idempotent_replay"])
        self.assertEqual(first.json()["job"]["id"], second.json()["job"]["id"])
        self.assertEqual(submit.call_count, 1)
        status_response = self.client.get(f"/api/v1/research-jobs/{first.json()['job']['id']}")
        self.assertEqual(status_response.status_code, 200)
        self.assertEqual(submit.call_count, 1)

        from analysis.conversation.streaming import claim_operation
        job = ResearchJob.objects.get(id=first.json()["job"]["id"])
        self.assertTrue(claim_operation(job.operation_id, "api-evidence-worker"))
        self.assertTrue(perform_research(job.id, "api-evidence-worker"))
        completed = self.client.get(f"/api/v1/research-jobs/{job.id}")
        self.assertEqual(completed.status_code, 200)
        claim = completed.json()["snapshots"][0]["claims"][0]
        self.assertEqual(claim["variant"]["canonical_identifier"], "SYN-A1")
        self.assertEqual(claim["variant"]["model_name"], "قهوه‌ساز آزمایشی A1")

    @patch("analysis.api.research.submit_research_reserved", return_value=True)
    @patch("analysis.api.research.release_research_slot")
    @patch("analysis.api.research.reserve_research_slot", return_value=True)
    def test_one_active_job_per_guest_and_foreign_owner_is_hidden(self, _reserve, _release, _submit):
        path = f"/api/v1/conversations/{self.conversation['id']}/research"
        first = self.post(
            path,
            {"expected_brief_revision": 1, "source_ids": ["synthetic-appliance-v1"]},
            HTTP_IDEMPOTENCY_KEY="research-active-key-001",
        )
        second = self.post(
            path,
            {"expected_brief_revision": 1, "source_ids": ["synthetic-electronics-v1"]},
            HTTP_IDEMPOTENCY_KEY="research-active-key-002",
        )
        self.assertEqual(first.status_code, 202)
        self.assertEqual(second.status_code, 429)
        foreign = Client()
        foreign.get("/api/v1/session")
        self.assertEqual(foreign.get(f"/api/v1/research-jobs/{first.json()['job']['id']}").status_code, 404)

    @patch("analysis.api.research.submit_research_reserved", return_value=True)
    @patch("analysis.api.research.release_research_slot")
    @patch("analysis.api.research.reserve_research_slot", return_value=True)
    def test_cancel_is_csrf_protected_and_terminal(self, _reserve, _release, _submit):
        started = self.post(
            f"/api/v1/conversations/{self.conversation['id']}/research",
            {"expected_brief_revision": 1, "source_ids": ["synthetic-appliance-v1"]},
            HTTP_IDEMPOTENCY_KEY="research-cancel-key-001",
        ).json()
        job_id = started["job"]["id"]
        no_csrf = Client(enforce_csrf_checks=True)
        no_csrf.get("/api/v1/session")
        self.assertEqual(no_csrf.post(f"/api/v1/research-jobs/{job_id}/cancel").status_code, 403)
        cancelled = self.post(f"/api/v1/research-jobs/{job_id}/cancel", {})
        self.assertEqual(cancelled.status_code, 202, cancelled.content)
        self.assertEqual(cancelled.json()["operation"]["status"], "CANCELLED")


@override_settings(BEFOREBUY_RESEARCH_MODE="OFFLINE")
class OfflineResearchApiTests(TestCase):
    def test_offline_default_returns_unavailable_without_job_or_operation(self):
        client, token = csrf_client()
        conversation = client.post(
            "/api/v1/conversations", {}, content_type="application/json", HTTP_X_CSRFTOKEN=token
        ).json()
        response = client.post(
            f"/api/v1/conversations/{conversation['id']}/research",
            {"expected_brief_revision": 0, "source_ids": []},
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
            HTTP_IDEMPOTENCY_KEY="research-offline-key-001",
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "RESEARCH_OFFLINE")
        self.assertEqual(ResearchJob.objects.count(), 0)
        self.assertEqual(StreamOperation.objects.filter(operation_kind="RESEARCH").count(), 0)

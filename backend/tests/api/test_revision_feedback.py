from django.test import TestCase

from .payloads import valid_analysis_payload
from .test_analysis_create_read import csrf_client


class RevisionAndFeedbackApiTests(TestCase):
    def setUp(self):
        self.client, self.token = csrf_client()
        created = self.client.post(
            "/api/v1/analyses", valid_analysis_payload(), content_type="application/json",
            HTTP_X_CSRFTOKEN=self.token,
        )
        self.assertEqual(created.status_code, 201)
        self.item = created.json()

    def test_edit_recomputes_and_stale_input_revision_conflicts(self):
        payload = valid_analysis_payload(budget_toman="۰") | {"expected_input_revision": 1}
        updated = self.client.patch(
            f"/api/v1/analyses/{self.item['id']}", payload, content_type="application/json",
            HTTP_X_CSRFTOKEN=self.token,
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["input_revision"], 2)
        self.assertEqual(updated.json()["report"]["primary_outcome"], "BUDGET_MISMATCH")

        stale = self.client.patch(
            f"/api/v1/analyses/{self.item['id']}", payload, content_type="application/json",
            HTTP_X_CSRFTOKEN=self.token,
        )
        self.assertEqual(stale.status_code, 409)
        self.assertEqual(stale.json()["error"]["code"], "REVISION_CONFLICT")

    def test_feedback_is_mutable_and_identical_retry_preserves_it(self):
        report_id = self.item["report"]["report_revision_id"]
        feedback_url = f"/api/v1/analyses/{self.item['id']}/feedback"
        first = self.client.put(
            feedback_url, {"report_revision_id": report_id, "rating": 3}, content_type="application/json",
            HTTP_X_CSRFTOKEN=self.token,
        )
        self.assertEqual(first.status_code, 200)
        changed = self.client.put(
            feedback_url, {"report_revision_id": report_id, "rating": 5}, content_type="application/json",
            HTTP_X_CSRFTOKEN=self.token,
        )
        self.assertEqual(changed.json()["rating"], 5)

        retry = self.client.post(
            f"/api/v1/analyses/{self.item['id']}/reanalysis",
            {"expected_input_revision": 1, "expected_report_revision_id": report_id},
            content_type="application/json", HTTP_X_CSRFTOKEN=self.token,
        )
        self.assertEqual(retry.status_code, 200)
        self.assertEqual(retry.json()["report"]["report_revision_id"], report_id)
        self.assertEqual(retry.json()["report"]["feedback"]["rating"], 5)

        removed = self.client.delete(
            f"{feedback_url}?report_revision_id={report_id}", HTTP_X_CSRFTOKEN=self.token,
        )
        self.assertEqual(removed.status_code, 204)

    def test_feedback_for_stale_report_revision_conflicts(self):
        response = self.client.put(
            f"/api/v1/analyses/{self.item['id']}/feedback",
            {"report_revision_id": "00000000-0000-0000-0000-000000000001", "rating": 4},
            content_type="application/json", HTTP_X_CSRFTOKEN=self.token,
        )
        self.assertEqual(response.status_code, 409)

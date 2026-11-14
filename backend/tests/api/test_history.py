from django.test import TestCase

from analysis.models import Analysis, GuestContext

from .payloads import valid_analysis_payload
from .test_analysis_create_read import csrf_client


class HistoryDeletionTests(TestCase):
    def setUp(self):
        self.client, self.token = csrf_client()

    def create(self, label):
        response = self.client.post(
            "/api/v1/analyses", valid_analysis_payload(product_label=label), content_type="application/json",
            HTTP_X_CSRFTOKEN=self.token,
        )
        self.assertEqual(response.status_code, 201)
        return response.json()

    def test_delete_one_cascades_report_and_hides_direct_access(self):
        item = self.create("اول")
        response = self.client.delete(f"/api/v1/analyses/{item['id']}", HTTP_X_CSRFTOKEN=self.token)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.client.get(f"/api/v1/analyses/{item['id']}").status_code, 404)

    def test_clear_history_advances_epoch_and_removes_only_current_guest_data(self):
        self.create("اول")
        second_client, second_token = csrf_client()
        second_client.post(
            "/api/v1/analyses", valid_analysis_payload(product_label="مهمان دوم"),
            content_type="application/json", HTTP_X_CSRFTOKEN=second_token,
        )
        guest_id = self.client.session["guest_context_id"]
        before = GuestContext.objects.get(id=guest_id).generation_epoch

        response = self.client.post("/api/v1/analyses/clear", {}, content_type="application/json", HTTP_X_CSRFTOKEN=self.token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["deleted_count"], 1)
        self.assertEqual(GuestContext.objects.get(id=guest_id).generation_epoch, before + 1)
        self.assertEqual(Analysis.objects.count(), 1)

    def test_history_is_newest_first(self):
        first = self.create("اول")
        second = self.create("دوم")
        ids = [item["id"] for item in self.client.get("/api/v1/analyses").json()["items"]]
        self.assertEqual(ids, [second["id"], first["id"]])

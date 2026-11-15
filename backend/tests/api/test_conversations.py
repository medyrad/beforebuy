from datetime import timedelta
from unittest.mock import patch

from django.test import Client, TestCase
from django.utils import timezone

from analysis.models import Conversation, GuestContext, ShoppingBrief, StreamOperation, UploadedImage


def csrf_client():
    client = Client(enforce_csrf_checks=True)
    response = client.get("/api/v1/session")
    assert response.status_code == 200
    return client, client.cookies["csrftoken"].value


class ConversationApiTests(TestCase):
    def setUp(self):
        self.client, self.token = csrf_client()

    def post(self, path, data, **extra):
        return self.client.post(path, data, content_type="application/json", HTTP_X_CSRFTOKEN=self.token, **extra)

    def test_create_list_read_and_foreign_owner_boundary(self):
        created = self.post("/api/v1/conversations", {"title": "انتخاب لپ‌تاپ"})
        self.assertEqual(created.status_code, 201)
        body = created.json()
        self.assertEqual(body["brief"]["revision"], 0)
        self.assertEqual(self.client.get("/api/v1/conversations").json()["items"][0]["id"], body["id"])
        foreign = Client()
        foreign.get("/api/v1/session")
        self.assertEqual(foreign.get(f"/api/v1/conversations/{body['id']}").status_code, 404)

    def test_unsafe_requests_require_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.get("/api/v1/session")
        self.assertEqual(client.post("/api/v1/conversations", {}, content_type="application/json").status_code, 403)

    def test_brief_edit_is_compare_and_swap_and_zero_is_preserved(self):
        conversation = self.post("/api/v1/conversations", {}).json()
        path = f"/api/v1/conversations/{conversation['id']}/brief"
        changed = self.client.patch(
            path,
            {"expected_revision": 0, "changes": {"recipient_context": "SELF", "budget_toman": 0}},
            content_type="application/json", HTTP_X_CSRFTOKEN=self.token,
        )
        self.assertEqual(changed.status_code, 200, changed.content)
        self.assertEqual(changed.json()["budget_toman"], 0)
        stale = self.client.patch(
            path, {"expected_revision": 0, "changes": {"category": "رایانه"}},
            content_type="application/json", HTTP_X_CSRFTOKEN=self.token,
        )
        self.assertEqual(stale.status_code, 409)

    @patch("analysis.api.conversations.submit_reserved")
    @patch("analysis.api.conversations.release_execution_slot")
    @patch("analysis.api.conversations.reserve_execution_slot", return_value=True)
    def test_duplicate_submission_returns_same_message_and_conflicting_payload_is_rejected(self, _reserve, _release, _submit):
        conversation = self.post("/api/v1/conversations", {}).json()
        path = f"/api/v1/conversations/{conversation['id']}/messages"
        headers = {"HTTP_IDEMPOTENCY_KEY": "retry-safe-key-0001"}
        payload = {"text": "متن نمونه", "expected_brief_revision": 0, "upload_ids": []}
        first = self.post(path, payload, **headers)
        second = self.post(path, payload, **headers)
        conflict = self.post(path, payload | {"text": "متن متفاوت"}, **headers)
        self.assertEqual(first.status_code, 202, first.content)
        self.assertEqual(second.status_code, 202)
        self.assertTrue(second.json()["idempotent_replay"])
        self.assertEqual(first.json()["message_id"], second.json()["message_id"])
        self.assertEqual(conflict.status_code, 409)

    def test_reads_do_not_extend_expiry(self):
        conversation = self.post("/api/v1/conversations", {}).json()
        marker = timezone.now() + timedelta(days=10)
        Conversation.objects.filter(id=conversation["id"]).update(expires_at=marker)
        self.client.get(f"/api/v1/conversations/{conversation['id']}")
        self.assertEqual(Conversation.objects.get(id=conversation["id"]).expires_at, marker)

    @patch("analysis.api.conversations.submit_reserved")
    @patch("analysis.api.conversations.release_execution_slot")
    @patch("analysis.api.conversations.reserve_execution_slot", return_value=True)
    def test_submitted_image_is_attributed_to_the_user_message(self, _reserve, _release, _submit):
        conversation = self.post("/api/v1/conversations", {}).json()
        upload = UploadedImage.objects.create(
            conversation_id=conversation["id"], media_type="image/png", content=b"sanitized",
            size_bytes=9, width=1, height=1, sha256="3" * 64,
        )
        response = self.post(
            f"/api/v1/conversations/{conversation['id']}/messages",
            {"text": "این تصویر متعلق به همین پیام است.", "expected_brief_revision": 0, "upload_ids": [str(upload.id)]},
            HTTP_IDEMPOTENCY_KEY="image-attribution-key-001",
        )
        self.assertEqual(response.status_code, 202, response.content)
        upload.refresh_from_db()
        self.assertEqual(str(upload.message_id), response.json()["message_id"])
        detail = self.client.get(f"/api/v1/conversations/{conversation['id']}").json()
        self.assertEqual(detail["messages"][0]["upload_ids"], [str(upload.id)])

    def test_delete_cascades_and_denies_repeated_access(self):
        conversation = self.post("/api/v1/conversations", {}).json()
        response = self.client.delete(
            f"/api/v1/conversations/{conversation['id']}", HTTP_X_CSRFTOKEN=self.token
        )
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Conversation.objects.filter(id=conversation["id"]).exists())
        self.assertEqual(self.client.get(f"/api/v1/conversations/{conversation['id']}").status_code, 404)

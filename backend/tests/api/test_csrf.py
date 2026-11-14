from django.test import Client, TestCase, override_settings

from .payloads import valid_analysis_payload


class AnonymousGuestCsrfTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        bootstrap = self.client.get("/api/v1/session")
        self.assertEqual(bootstrap.status_code, 200, "session bootstrap is not implemented")

    def test_valid_guest_session_without_csrf_token_is_rejected(self):
        response = self.client.post("/api/v1/analyses", valid_analysis_payload(), content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "CSRF_FAILED")

    def test_invalid_csrf_token_is_rejected(self):
        response = self.client.post(
            "/api/v1/analyses", valid_analysis_payload(), content_type="application/json",
            HTTP_X_CSRFTOKEN="invalid-token",
        )
        self.assertEqual(response.status_code, 403)

    def test_correct_same_origin_csrf_flow_is_accepted(self):
        token = self.client.cookies["csrftoken"].value
        response = self.client.post(
            "/api/v1/analyses", valid_analysis_payload(), content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 201)

    @override_settings(ALLOWED_HOSTS=["beforebuy.local"], CSRF_TRUSTED_ORIGINS=["https://beforebuy.local"])
    def test_untrusted_host_is_rejected_by_deployed_host_configuration(self):
        response = self.client.get("/api/v1/session", HTTP_HOST="evil.example")
        self.assertEqual(response.status_code, 400)

    @override_settings(ALLOWED_HOSTS=["beforebuy.local"], CSRF_TRUSTED_ORIGINS=["https://beforebuy.local"])
    def test_untrusted_origin_is_rejected_for_unsafe_request(self):
        client = Client(enforce_csrf_checks=True, HTTP_HOST="beforebuy.local")
        client.get("/api/v1/session", secure=True)
        token = client.cookies["csrftoken"].value
        response = client.post(
            "/api/v1/analyses", valid_analysis_payload(), content_type="application/json", secure=True,
            HTTP_X_CSRFTOKEN=token, HTTP_ORIGIN="https://evil.example",
        )
        self.assertEqual(response.status_code, 403)

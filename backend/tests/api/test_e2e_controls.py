from django.test import TestCase, override_settings

from .payloads import valid_analysis_payload
from .test_analysis_create_read import csrf_client


class BrowserVerificationControlTests(TestCase):
    def create_with_limited_header(self):
        client, token = csrf_client()
        response = client.post(
            "/api/v1/analyses",
            valid_analysis_payload(),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
            HTTP_X_BEFOREBUY_E2E_EXPLANATION="limited",
        )
        return response

    @override_settings(BEFOREBUY_E2E_TEST_CONTROLS=False)
    def test_failure_header_is_ignored_when_test_controls_are_disabled(self):
        response = self.create_with_limited_header()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["report"]["mode"], "MOCK_ASSISTED")

    @override_settings(BEFOREBUY_E2E_TEST_CONTROLS=True)
    def test_explicit_test_setting_can_inject_limited_explanation_path(self):
        response = self.create_with_limited_header()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["report"]["mode"], "RULE_BASED_LIMITED")

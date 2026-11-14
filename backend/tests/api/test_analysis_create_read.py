from pathlib import Path

import yaml
from django.test import Client, TestCase

from .payloads import valid_analysis_payload


def csrf_client():
    client = Client(enforce_csrf_checks=True)
    response = client.get("/api/v1/session")
    if response.status_code != 200:
        return client, None
    return client, client.cookies["csrftoken"].value


class AnalysisCreateReadContractTests(TestCase):
    def create(self, client, token, payload=None):
        self.assertIsNotNone(token, "session bootstrap is not implemented")
        return client.post(
            "/api/v1/analyses", payload or valid_analysis_payload(), content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )

    def test_create_returns_scoped_mock_report_and_no_live_ai_claim(self):
        client, token = csrf_client()
        response = self.create(client, token)
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["report"]["mode"], "MOCK_ASSISTED")
        self.assertEqual(body["report"]["primary_outcome"], "PHONE_PURCHASE_JUSTIFIED_WITHIN_BUDGET")
        self.assertEqual(body["report"]["dimensions"]["target_fit"], "TARGET_FIT_UNVERIFIED")

    def test_list_and_read_return_only_the_current_guests_analysis(self):
        owner, token = csrf_client()
        created = self.create(owner, token).json()
        listed = owner.get("/api/v1/analyses")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual([item["id"] for item in listed.json()["items"]], [created["id"]])
        self.assertEqual(owner.get(f"/api/v1/analyses/{created['id']}").status_code, 200)

        stranger, _ = csrf_client()
        missing = stranger.get(f"/api/v1/analyses/{created['id']}")
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(missing.json()["error"]["code"], "NOT_FOUND")

    def test_invalid_money_uses_consistent_error_envelope_and_persists_nothing(self):
        client, token = csrf_client()
        response = self.create(client, token, valid_analysis_payload(price_toman="1e7"))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("price_toman", response.json()["error"]["field_errors"])
        self.assertEqual(client.get("/api/v1/analyses").json()["items"], [])

    def test_questionnaire_rejects_unknown_values_invalid_multiselect_and_extra_fields(self):
        client, token = csrf_client()
        invalid_payloads = [
            valid_analysis_payload(answers=valid_analysis_payload()["answers"] | {"Q-001": "BROKEN_ENUM"}),
            valid_analysis_payload(answers=valid_analysis_payload()["answers"] | {"Q-003": []}),
            valid_analysis_payload(answers=valid_analysis_payload()["answers"] | {"Q-006": ["NONE", "WAIT"]}),
            valid_analysis_payload(unexpected="must-not-be-ignored"),
        ]
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                response = self.create(client, token, payload)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()["error"]["code"], "VALIDATION_ERROR")

    def test_report_evidence_exposes_source_and_attribution(self):
        client, token = csrf_client()
        response = self.create(client, token)
        self.assertEqual(response.status_code, 201)
        for item in response.json()["report"]["evidence"]:
            self.assertEqual(item["attribution"], "USER_REPORTED")
            self.assertRegex(item["source_id"], r"^(PC|Q|F)-[0-9]{3}$")

    def test_openapi_create_example_is_accepted(self):
        contract = Path(__file__).resolve().parents[3] / "specs/001-purchase-decision-analysis/contracts/openapi.yaml"
        document = yaml.safe_load(contract.read_text())
        payload = document["paths"]["/analyses"]["post"]["requestBody"]["content"]["application/json"]["example"]
        client, token = csrf_client()
        response = self.create(client, token, payload)
        self.assertEqual(response.status_code, 201, response.content)

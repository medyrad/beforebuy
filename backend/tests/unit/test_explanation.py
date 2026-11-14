from django.test import SimpleTestCase

from analysis.ai import contracts, generator, validator
from analysis import services


class ExplanationContractTests(SimpleTestCase):
    def setUp(self):
        if not hasattr(contracts, "ExplanationRequest"):
            self.request = None
            return
        self.request = contracts.ExplanationRequest(
            schema_version="PDA-EXPLAIN-v1",
            rubric_id="PDA-CAT-v0.3",
            target_label="گوشی نمونه",
            primary_outcome="PHONE_PURCHASE_JUSTIFIED_WITHIN_BUDGET",
            dimensions={"budget": "WITHIN_BUDGET", "justification": "JUSTIFICATION_SUPPORTED",
                        "target_fit": "TARGET_FIT_UNVERIFIED", "tradeoff": "NOT_REQUIRED"},
            evidence=[{"id": "ev-q001", "type": "CURRENT_DEVICE_STATE", "source_id": "Q-001", "value": "UNUSABLE"}],
            rule_ids=["JUS-04", "OUT-08"],
            unknowns=["TARGET_MODEL_CAPABILITY"],
            actions=["VERIFY_TARGET_CAPABILITY"],
        )

    def test_mock_is_explicit_and_never_live_ai_success(self):
        self.assertIsNotNone(self.request, "ExplanationRequest is not implemented")
        response = generator.MockExplanationGenerator().generate(self.request)
        self.assertEqual(response.mode, "MOCK_ASSISTED")
        self.assertNotEqual(response.mode, "AI_ASSISTED_SUCCESS")

    def test_evidence_id_with_incompatible_claim_type_is_rejected(self):
        self.assertIsNotNone(self.request, "ExplanationRequest is not implemented")
        response = contracts.ExplanationResponse(
            mode="MOCK_ASSISTED",
            outcome_id=self.request.primary_outcome,
            acknowledged_unknown_ids=self.request.unknowns,
            headline_fa="مدل برای بازی مناسب است.",
            claims=[contracts.ExplanationClaim(
                claim_type="TARGET_CAPABILITY_SUPPORTED", text_fa="مدل برای بازی مناسب است.",
                evidence_ids=["ev-q001"], rule_ids=[]
            )],
        )
        with self.assertRaises(validator.UnsupportedExplanation):
            validator.validate_explanation(self.request, response)

    def test_positive_target_fit_requires_explicit_positive_user_report(self):
        for value, attribution in [
            ("NO_INFORMATION", "USER_REPORTED"),
            ("USER_REPORTS_IT_DOES_NOT_FIT", "USER_REPORTED"),
            ("USER_REPORTS_IT_FITS", "UNKNOWN"),
        ]:
            with self.subTest(value=value, attribution=attribution):
                request = contracts.ExplanationRequest(**{
                    **self.request.__dict__,
                    "evidence": [{"id": "ev-fit", "type": "TARGET_FIT_REPORT", "source_id": "F-003",
                                  "value": value, "attribution": attribution}],
                })
                response = contracts.ExplanationResponse(
                    mode="AI_ASSISTED_SUCCESS", outcome_id=request.primary_outcome,
                    acknowledged_unknown_ids=request.unknowns, headline_fa="جمع‌بندی",
                    claims=[contracts.ExplanationClaim(
                        claim_type="USER_REPORTED_TARGET_FIT", text_fa="طبق پاسخ شما این مدل مناسب است.",
                        evidence_ids=["ev-fit"], rule_ids=[]
                    )],
                )
                with self.assertRaises(validator.UnsupportedExplanation):
                    validator.validate_explanation(request, response)

    def test_explicit_positive_user_report_can_support_scoped_fit_claim(self):
        request = contracts.ExplanationRequest(**{
            **self.request.__dict__,
            "evidence": [{"id": "ev-fit", "type": "TARGET_FIT_REPORT", "source_id": "F-003",
                          "value": "USER_REPORTS_IT_FITS", "attribution": "USER_REPORTED"}],
        })
        response = contracts.ExplanationResponse(
            mode="AI_ASSISTED_SUCCESS", outcome_id=request.primary_outcome,
            acknowledged_unknown_ids=request.unknowns, headline_fa="جمع‌بندی",
            claims=[contracts.ExplanationClaim(
                claim_type="USER_REPORTED_TARGET_FIT", text_fa="طبق پاسخ شما این مدل برای نیازتان مناسب است.",
                evidence_ids=["ev-fit"], rule_ids=[]
            )],
        )
        self.assertIs(validator.validate_explanation(request, response), response)

    def test_free_prose_semantics_are_not_misrepresented_as_code_enforced(self):
        response = contracts.ExplanationResponse(
            mode="AI_ASSISTED_SUCCESS", outcome_id=self.request.primary_outcome,
            acknowledged_unknown_ids=self.request.unknowns,
            headline_fa="نتیجهٔ درست با یک متن نامرتبط",
            claims=[contracts.ExplanationClaim(
                claim_type="CURRENT_DEVICE_CONTEXT",
                text_fa="مدل ساختگی X با قیمت ۹۹ میلیون بهترین جایگزین است.",
                evidence_ids=["ev-q001"], rule_ids=[]
            )],
        )
        self.assertIs(validator.validate_explanation(self.request, response), response)

    def test_contradictory_headline_is_a_documented_human_review_limit(self):
        response = contracts.ExplanationResponse(
            mode="AI_ASSISTED_SUCCESS", outcome_id=self.request.primary_outcome,
            acknowledged_unknown_ids=self.request.unknowns,
            headline_fa="این خرید اصلاً توجیه ندارد و حتماً بالاتر از بودجه است.",
            claims=[],
        )
        self.assertIs(validator.validate_explanation(self.request, response), response)

    def test_outcome_contradiction_is_rejected(self):
        self.assertIsNotNone(self.request, "ExplanationRequest is not implemented")
        response = contracts.ExplanationResponse(
            mode="MOCK_ASSISTED", outcome_id=self.request.primary_outcome,
            acknowledged_unknown_ids=self.request.unknowns, headline_fa="این خرید بالاتر از بودجه است.",
            claims=[contracts.ExplanationClaim(
                claim_type="BUDGET_MISMATCH", text_fa="این خرید بالاتر از بودجه است.",
                evidence_ids=[], rule_ids=["OUT-08"]
            )],
        )
        with self.assertRaises(validator.UnsupportedExplanation):
            validator.validate_explanation(self.request, response)

    def test_unknown_claim_type_is_rejected(self):
        response = contracts.ExplanationResponse(
            mode="MOCK_ASSISTED", outcome_id=self.request.primary_outcome,
            acknowledged_unknown_ids=self.request.unknowns, headline_fa="ادعای آزاد",
            claims=[contracts.ExplanationClaim(
                claim_type="FREE_FORM_PRODUCT_FACT", text_fa="این مدل بهترین است.",
                evidence_ids=[], rule_ids=[]
            )],
        )
        with self.assertRaises(validator.UnsupportedExplanation):
            validator.validate_explanation(self.request, response)

    def test_malformed_generator_output_falls_back_to_limited_mode(self):
        class MalformedGenerator:
            def generate(self, request):
                return {"unexpected": True}

        data = {
            "product_label": "گوشی نمونه", "price_toman": 20_000_000, "budget_toman": 25_000_000,
            "answers": {"Q-001": "UNUSABLE", "Q-002": "RESTORE_ESSENTIAL_ACCESS",
                        "Q-003": ["GENERAL_USE"], "Q-004": "FLEXIBLE", "Q-006": ["NONE"]},
        }
        _result, report = services.build_report(data, MalformedGenerator())
        self.assertEqual(report["mode"], "RULE_BASED_LIMITED")
        self.assertTrue(report["explanation_blocks"])
        self.assertTrue(all(block["evidence_ids"] for block in report["explanation_blocks"]))

    def test_unknown_budget_produces_a_scoped_reason_without_numeric_formatting(self):
        data = {
            "product_label": "گوشی نمونه", "price_toman": 20_000_000, "budget_toman": None,
            "answers": {"Q-001": "UNUSABLE", "Q-002": "RESTORE_ESSENTIAL_ACCESS",
                        "Q-003": ["GENERAL_USE"], "Q-004": "FLEXIBLE", "Q-006": ["NONE"]},
        }
        _result, report = services.build_report(data)
        self.assertTrue(any("بودجه را نامعلوم" in block["text_fa"] for block in report["explanation_blocks"]))

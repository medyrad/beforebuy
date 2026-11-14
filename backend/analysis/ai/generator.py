from .contracts import ExplanationClaim, ExplanationRequest, ExplanationResponse


class MockExplanationGenerator:
    """Deterministic development double; never represents a live AI call."""

    def generate(self, request: ExplanationRequest) -> ExplanationResponse:
        return ExplanationResponse(
            mode="MOCK_ASSISTED",
            outcome_id=request.primary_outcome,
            acknowledged_unknown_ids=request.unknowns,
            headline_fa="این گزارش آزمایشی است و بر اساس قواعد قطعی تهیه شده است.",
            claims=[ExplanationClaim(
                claim_type="DETERMINISTIC_OUTCOME",
                text_fa="نتیجه از قواعد نسخه‌دار محاسبه شده است.",
                evidence_ids=[],
                rule_ids=request.rule_ids,
            )],
        )


class E2ELimitedExplanationGenerator:
    """Test-only injected failure; production settings never select this generator."""

    def generate(self, request: ExplanationRequest) -> ExplanationResponse:
        raise ValueError("injected browser-verification explanation failure")

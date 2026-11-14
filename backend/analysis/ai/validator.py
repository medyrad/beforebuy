from .contracts import ExplanationRequest, ExplanationResponse


class UnsupportedExplanation(ValueError):
    pass


def validate_explanation(request: ExplanationRequest, response: ExplanationResponse) -> ExplanationResponse:
    if response.mode not in {"MOCK_ASSISTED", "RULE_BASED_LIMITED", "AI_ASSISTED_SUCCESS"}:
        raise UnsupportedExplanation("unknown report mode")
    if response.outcome_id != request.primary_outcome:
        raise UnsupportedExplanation("AI output contradicts deterministic outcome")
    if response.acknowledged_unknown_ids != request.unknowns:
        raise UnsupportedExplanation("AI output does not preserve deterministic unknowns")
    if not response.headline_fa or len(response.headline_fa) > 240:
        raise UnsupportedExplanation("headline length is outside contract")
    if len(response.claims) > 3:
        raise UnsupportedExplanation("too many explanation claims")
    evidence = {item["id"]: item for item in request.evidence}
    allowed_claim_types = {
        "DETERMINISTIC_OUTCOME", "CURRENT_DEVICE_CONTEXT", "EXPECTED_BENEFIT_CONTEXT",
        "INTENDED_USE_CONTEXT", "URGENCY_CONTEXT", "BUDGET_CONTEXT", "BUDGET_MISMATCH",
        "TARGET_FIT_CONTEXT", "TARGET_CAPABILITY_SUPPORTED", "TRADEOFF_CONTEXT", "NEXT_ACTION",
    }
    evidence_types = {
        "CURRENT_DEVICE_CONTEXT": {"CURRENT_DEVICE_STATE"},
        "EXPECTED_BENEFIT_CONTEXT": {"EXPECTED_BENEFIT"},
        "INTENDED_USE_CONTEXT": {"INTENDED_USE"},
        "URGENCY_CONTEXT": {"URGENCY"},
        "BUDGET_CONTEXT": {"PURCHASE_PRICE", "STATED_BUDGET"},
        "BUDGET_MISMATCH": {"PURCHASE_PRICE", "STATED_BUDGET"},
        "TARGET_FIT_CONTEXT": {"TARGET_FIT_REPORT"},
        "TARGET_CAPABILITY_SUPPORTED": {"TARGET_FIT_REPORT"},
        "TRADEOFF_CONTEXT": {"TRADEOFFS"},
    }
    for claim in response.claims:
        if claim.claim_type not in allowed_claim_types:
            raise UnsupportedExplanation("unsupported claim type")
        if not set(claim.rule_ids).issubset(set(request.rule_ids)):
            raise UnsupportedExplanation("unknown or incompatible rule")
        if not set(claim.evidence_ids).issubset(evidence):
            raise UnsupportedExplanation("unknown evidence")
        if len(claim.evidence_ids) != len(set(claim.evidence_ids)) or len(claim.rule_ids) != len(set(claim.rule_ids)):
            raise UnsupportedExplanation("duplicate evidence or rule reference")
        if not claim.text_fa or len(claim.text_fa) > 320:
            raise UnsupportedExplanation("claim text length is outside contract")
        expected_types = evidence_types.get(claim.claim_type)
        if expected_types is not None and (
            not claim.evidence_ids
            or any(evidence[item]["type"] not in expected_types for item in claim.evidence_ids)
        ):
            raise UnsupportedExplanation("evidence type cannot support claim")
        if claim.claim_type == "TARGET_CAPABILITY_SUPPORTED":
            if not claim.evidence_ids or any(evidence[item]["type"] != "TARGET_FIT_REPORT" for item in claim.evidence_ids):
                raise UnsupportedExplanation("evidence content cannot support target capability")
        if claim.claim_type == "BUDGET_MISMATCH" and request.dimensions["budget"] != "ABOVE_BUDGET":
            raise UnsupportedExplanation("claim contradicts deterministic budget")
        if claim.claim_type == "DETERMINISTIC_OUTCOME" and not claim.rule_ids:
            raise UnsupportedExplanation("deterministic outcome requires rule support")
        if claim.claim_type == "NEXT_ACTION" and not claim.rule_ids:
            raise UnsupportedExplanation("next action requires rule support")
    return response

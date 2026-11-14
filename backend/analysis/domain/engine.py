from .money import normalize_budget, normalize_toman
from .types import AnalysisResult

RUBRIC_ID = "PDA-CAT-v0.3"
CONTRADICTIONS = {
    ("WORKS_WELL", "RESTORE_ESSENTIAL_ACCESS"),
    ("WORKS_WELL", "SOLVE_MAJOR_LIMIT"),
    ("MINOR_PROBLEM", "RESTORE_ESSENTIAL_ACCESS"),
    ("MINOR_PROBLEM", "SOLVE_MAJOR_LIMIT"),
    ("NO_DEVICE", "SOLVE_MINOR_LIMIT"),
}


def _justification(state: str, benefit: str) -> tuple[str, str]:
    if (state, benefit) in CONTRADICTIONS:
        return "CONTRADICTORY", "JUS-01"
    if state == "UNKNOWN" or benefit == "UNKNOWN":
        return "JUSTIFICATION_UNKNOWN", "JUS-02"
    if benefit == "PERSONAL_ENJOYMENT" or (
        state in {"MINOR_PROBLEM", "WORKS_WELL"} and benefit == "SOLVE_MINOR_LIMIT"
    ):
        return "DISCRETIONARY_CLEAR", "JUS-03"
    if (
        state in {"NO_DEVICE", "UNUSABLE", "SERIOUS_PROBLEM"}
        and benefit in {"RESTORE_ESSENTIAL_ACCESS", "SOLVE_MAJOR_LIMIT", "ENABLE_IMPORTANT_NEW_USE"}
    ) or (state in {"MINOR_PROBLEM", "WORKS_WELL"} and benefit == "ENABLE_IMPORTANT_NEW_USE"):
        return "JUSTIFICATION_SUPPORTED", "JUS-04"
    if benefit == "NO_CLEAR_BENEFIT":
        return "WEAK_OR_NONE", "JUS-05"
    return "JUSTIFICATION_UNKNOWN", "JUS-06"


def _target(value: str | None) -> tuple[str, str]:
    if value == "USER_REPORTS_IT_DOES_NOT_FIT":
        return "USER_REPORTED_MISMATCH", "FIT-01"
    if value == "USER_REPORTS_IT_FITS":
        return "USER_REPORTED_SUPPORT", "FIT-02"
    return "TARGET_FIT_UNVERIFIED", "FIT-03"


def _outcome(budget: str, justification: str, target: str, tradeoff: str) -> tuple[str, str]:
    if budget == "ABOVE_BUDGET":
        return "BUDGET_MISMATCH", "OUT-01"
    if justification in {"CONTRADICTORY", "JUSTIFICATION_UNKNOWN"}:
        return "INSUFFICIENT_CONTEXT", "OUT-02"
    if target == "USER_REPORTED_MISMATCH":
        return "RECONSIDER_OR_WAIT", "OUT-03"
    if justification == "WEAK_OR_NONE":
        return "RECONSIDER_OR_WAIT", "OUT-04"
    if justification == "DISCRETIONARY_CLEAR" and tradeoff == "UNRESOLVED":
        return "INSUFFICIENT_CONTEXT", "OUT-05"
    if budget == "BUDGET_UNKNOWN" and justification == "JUSTIFICATION_SUPPORTED":
        return "PHONE_PURCHASE_JUSTIFIED_BUDGET_UNKNOWN", "OUT-06"
    if budget == "BUDGET_UNKNOWN" and justification == "DISCRETIONARY_CLEAR" and tradeoff == "ACKNOWLEDGED":
        return "DISCRETIONARY_CHOICE_BUDGET_UNKNOWN", "OUT-07"
    if budget == "WITHIN_BUDGET" and justification == "JUSTIFICATION_SUPPORTED":
        return "PHONE_PURCHASE_JUSTIFIED_WITHIN_BUDGET", "OUT-08"
    if budget == "WITHIN_BUDGET" and justification == "DISCRETIONARY_CLEAR" and tradeoff == "ACKNOWLEDGED":
        return "DISCRETIONARY_CHOICE_WITHIN_BUDGET", "OUT-09"
    return "INSUFFICIENT_CONTEXT", "OUT-10"


def analyze(data: dict) -> AnalysisResult:
    price = normalize_toman(data["price_toman"], allow_zero=False)
    budget_value = normalize_budget(data.get("budget_toman"))
    answers = data["answers"]
    if budget_value is None:
        budget, budget_rule, delta = "BUDGET_UNKNOWN", "BUD-03", None
    elif price <= budget_value:
        budget, budget_rule, delta = "WITHIN_BUDGET", "BUD-01", None
    else:
        budget, budget_rule, delta = "ABOVE_BUDGET", "BUD-02", price - budget_value

    justification, justification_rule = _justification(answers["Q-001"], answers["Q-002"])
    target, target_rule = _target(answers.get("F-003"))
    tradeoffs = set(answers.get("Q-006", []))
    if justification == "DISCRETIONARY_CLEAR":
        tradeoff = "ACKNOWLEDGED" if "ACCEPTED_TARGET_TRADEOFFS" in tradeoffs else "UNRESOLVED"
        tradeoff_rule = "TRD-01" if tradeoff == "ACKNOWLEDGED" else "TRD-02"
    else:
        tradeoff, tradeoff_rule = "NOT_REQUIRED", "TRD-03"
    outcome, outcome_rule = _outcome(budget, justification, target, tradeoff)

    actions = []
    if "REPAIR_CURRENT" in tradeoffs:
        actions.append("REPAIR_NOTED")
    if "WAIT" in tradeoffs:
        actions.append("WAIT_NOTED")
    unknowns = []
    if target == "TARGET_FIT_UNVERIFIED":
        unknowns.append("TARGET_MODEL_CAPABILITY")
        actions.append("VERIFY_TARGET_CAPABILITY")
    if budget == "BUDGET_UNKNOWN":
        unknowns.append("BUDGET_FIT")
    if justification in {"JUSTIFICATION_UNKNOWN", "CONTRADICTORY"}:
        unknowns.append("PURCHASE_JUSTIFICATION")

    evidence = [
        {"id": "ev-pc002", "type": "PURCHASE_PRICE", "source_id": "PC-002", "value": price,
         "attribution": "USER_REPORTED"},
        {"id": "ev-q001", "type": "CURRENT_DEVICE_STATE", "source_id": "Q-001", "value": answers["Q-001"],
         "attribution": "USER_REPORTED"},
        {"id": "ev-q002", "type": "EXPECTED_BENEFIT", "source_id": "Q-002", "value": answers["Q-002"],
         "attribution": "USER_REPORTED"},
        {"id": "ev-q003", "type": "INTENDED_USE", "source_id": "Q-003", "value": answers.get("Q-003", []),
         "attribution": "USER_REPORTED"},
        {"id": "ev-q004", "type": "URGENCY", "source_id": "Q-004", "value": answers.get("Q-004", "UNKNOWN"),
         "attribution": "USER_REPORTED"},
        {"id": "ev-q005", "type": "STATED_BUDGET", "source_id": "Q-005",
         "value": "UNKNOWN" if budget_value is None else budget_value, "attribution": "USER_REPORTED"},
        {"id": "ev-q006", "type": "TRADEOFFS", "source_id": "Q-006", "value": answers.get("Q-006", []),
         "attribution": "USER_REPORTED"},
    ]
    if "F-003" in answers:
        evidence.append({
            "id": "ev-f003", "type": "TARGET_FIT_REPORT", "source_id": "F-003", "value": answers["F-003"],
            "attribution": "USER_REPORTED",
        })
    return AnalysisResult(
        rubric_id=RUBRIC_ID,
        primary_outcome=outcome,
        dimensions={"budget": budget, "justification": justification, "target_fit": target, "tradeoff": tradeoff},
        matched_rule_ids=[budget_rule, justification_rule, target_rule, tradeoff_rule, outcome_rule],
        evidence=evidence,
        unknowns=unknowns,
        actions=actions,
        budget_delta_toman=delta,
    )

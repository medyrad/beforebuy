from dataclasses import dataclass


@dataclass(frozen=True)
class AnalysisResult:
    rubric_id: str
    primary_outcome: str
    dimensions: dict[str, str]
    matched_rule_ids: list[str]
    evidence: list[dict]
    unknowns: list[str]
    actions: list[str]
    budget_delta_toman: int | None = None

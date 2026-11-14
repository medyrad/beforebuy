from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ExplanationRequest:
    schema_version: str
    rubric_id: str
    target_label: str
    primary_outcome: str
    dimensions: dict[str, str]
    evidence: list[dict]
    rule_ids: list[str]
    unknowns: list[str]
    actions: list[str]


@dataclass(frozen=True)
class ExplanationClaim:
    claim_type: str
    text_fa: str
    evidence_ids: list[str]
    rule_ids: list[str]


@dataclass(frozen=True)
class ExplanationResponse:
    mode: str
    outcome_id: str
    acknowledged_unknown_ids: list[str]
    headline_fa: str
    claims: list[ExplanationClaim]


class ExplanationGenerator(Protocol):
    def generate(self, request: ExplanationRequest) -> ExplanationResponse: ...

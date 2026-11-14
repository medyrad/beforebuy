import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from analysis.ai.evaluation import DATASET_VERSION, EvaluationResult, assess_results


class Command(BaseCommand):
    help = "Validate and assess a completed synthetic AI-review artifact; never calls a provider."

    def add_arguments(self, parser):
        parser.add_argument("artifact")

    def handle(self, *args, **options):
        path = Path(options["artifact"])
        try:
            artifact = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CommandError("review artifact is unreadable") from exc
        required = {"dataset", "run_id", "model", "prompt_version", "schema_version", "synthetic_only", "cases"}
        if not required.issubset(artifact) or artifact["dataset"] != DATASET_VERSION or artifact["synthetic_only"] is not True:
            raise CommandError("review artifact metadata is invalid")
        results = []
        try:
            for case in artifact["cases"]:
                recorded = case["result"]
                human = case["human_review"]
                if human["semantic_support"] is not None and not isinstance(human["semantic_support"], bool):
                    raise TypeError
                if any(value is not None and (not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 5)
                       for value in (human["readability"], human["actionability"], human["added_usefulness"])):
                    raise TypeError
                results.append(EvaluationResult(
                    case_id=case["case_id"],
                    contract_valid=recorded["contract_valid"],
                    outcome_preserved=recorded["outcome_preserved"],
                    unknowns_preserved=recorded["unknowns_preserved"],
                    semantic_support=human["semantic_support"],
                    readability=human["readability"],
                    actionability=human["actionability"],
                    added_usefulness=human["added_usefulness"],
                    attempts=recorded["attempts"],
                    input_tokens=recorded["input_tokens"],
                    output_tokens=recorded["output_tokens"],
                    latency_ms=recorded["latency_ms"],
                    reserved_cost_usd=recorded["reserved_cost_usd"],
                    estimated_cost_usd=recorded["estimated_cost_usd"],
                    cost_discrepancy_usd=recorded["cost_discrepancy_usd"],
                    usage_accounting=recorded["usage_accounting"],
                ))
        except (KeyError, TypeError) as exc:
            raise CommandError("review artifact case fields are invalid") from exc
        assessment = assess_results(results)
        self.stdout.write(json.dumps({
            "dataset": artifact["dataset"], "run_id": artifact["run_id"], "model": artifact["model"],
            "prompt_version": artifact["prompt_version"], "schema_version": artifact["schema_version"],
            "structural_pass": assessment.structural_pass, "operational_pass": assessment.operational_pass,
            "human_review_complete": assessment.human_review_complete, "human_pass": assessment.human_pass,
            "overall_pass": assessment.overall_pass, "case_count": assessment.case_count,
        }, sort_keys=True))

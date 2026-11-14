import hashlib
import json
import uuid
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .ai.contracts import ExplanationRequest
from .ai.generator import MockExplanationGenerator
from .ai.validator import UnsupportedExplanation, validate_explanation
from .domain.engine import analyze
from .domain.money import normalize_budget, normalize_toman
from .domain.presentation import deterministic_headline, deterministic_reason_blocks
from .models import Analysis, CurrentReport, GuestContext, UsefulnessFeedback


class OperationConflict(Exception):
    pass


class RevisionConflict(OperationConflict):
    pass


class AnalysisNotFound(Exception):
    pass


def normalize_input(data: dict) -> dict:
    return {
        "product_label": str(data["product_label"]).strip(),
        "price_toman": normalize_toman(data["price_toman"], allow_zero=False),
        "budget_toman": normalize_budget(data.get("budget_toman")),
        "answers": data["answers"],
    }


def _report_payload(result, explanation):
    return {
        "rubric_id": result.rubric_id,
        "mode": explanation.mode,
        "primary_outcome": result.primary_outcome,
        "dimensions": result.dimensions,
        "matched_rule_ids": result.matched_rule_ids,
        "evidence": result.evidence,
        "unknowns": result.unknowns,
        "actions": result.actions,
        "headline_fa": deterministic_headline(result),
        "explanation_blocks": deterministic_reason_blocks(result) + [
            {"kind": "ai_context", "text_fa": claim.text_fa,
             "evidence_ids": claim.evidence_ids, "rule_ids": claim.rule_ids}
            for claim in explanation.claims
        ],
    }


def build_explanation_request(data, result):
    return ExplanationRequest(
        schema_version="PDA-EXPLAIN-v1",
        rubric_id=result.rubric_id,
        target_label=data["product_label"],
        primary_outcome=result.primary_outcome,
        dimensions=result.dimensions,
        evidence=result.evidence,
        rule_ids=result.matched_rule_ids,
        unknowns=result.unknowns,
        actions=result.actions,
    )


def build_report(data, generator=None):
    result = analyze(data)
    request = build_explanation_request(data, result)
    try:
        explanation = (generator or MockExplanationGenerator()).generate(request)
        validate_explanation(request, explanation)
    except (UnsupportedExplanation, ValueError, TypeError, AttributeError):
        from .ai.contracts import ExplanationResponse

        explanation = ExplanationResponse(
            mode="RULE_BASED_LIMITED",
            outcome_id=result.primary_outcome,
            acknowledged_unknown_ids=result.unknowns,
            headline_fa="",
            claims=[],
        )
    return result, _report_payload(result, explanation)


def create_analysis(guest: GuestContext, data: dict, generator=None) -> Analysis:
    start_epoch = guest.generation_epoch
    result, report_payload = build_report(data, generator=generator)  # no database lock/network transaction
    now = timezone.now()
    expires_at = now + timedelta(days=90)
    canonical = json.dumps(report_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    with transaction.atomic():
        locked_guest = GuestContext.objects.select_for_update().get(id=guest.id)
        if locked_guest.generation_epoch != start_epoch:
            raise OperationConflict("guest generation epoch changed")
        analysis = Analysis.objects.create(
            guest_context=locked_guest,
            product_label=data["product_label"],
            price_toman=data["price_toman"],
            budget_toman=data.get("budget_toman"),
            answers=data["answers"],
            expires_at=expires_at,
        )
        CurrentReport.objects.create(
            analysis=analysis,
            input_revision=analysis.input_revision,
            canonical_hash=hashlib.sha256(canonical.encode()).hexdigest(),
            **report_payload,
        )
        if locked_guest.access_expires_at < expires_at:
            locked_guest.access_expires_at = expires_at
            locked_guest.save(update_fields=["access_expires_at"])
    return analysis


def _owned_locked_analysis(guest, analysis_id):
    item = (
        Analysis.objects.select_for_update()
        .filter(id=analysis_id, guest_context=guest, expires_at__gt=timezone.now())
        .first()
    )
    if item is None:
        raise AnalysisNotFound
    return item


def _canonical_hash(payload):
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def _publish_report(item, payload, *, input_revision, preserve_if_identical):
    report = CurrentReport.objects.select_for_update().get(analysis=item)
    new_hash = _canonical_hash(payload)
    if preserve_if_identical and report.canonical_hash == new_hash:
        return report
    UsefulnessFeedback.objects.filter(analysis=item).delete()
    for field, value in payload.items():
        setattr(report, field, value)
    report.report_revision_id = uuid.uuid4()
    report.input_revision = input_revision
    report.canonical_hash = new_hash
    report.save()
    return report


def update_analysis(guest, analysis_id, expected_input_revision, data, generator=None):
    operation_token = uuid.uuid4()
    with transaction.atomic():
        GuestContext.objects.select_for_update().get(id=guest.id)
        item = _owned_locked_analysis(guest, analysis_id)
        if item.input_revision != expected_input_revision:
            raise RevisionConflict("input revision changed")
        item.report_operation_token = operation_token
        item.save(update_fields=["report_operation_token"])

    _result, report_payload = build_report(data, generator=generator)

    with transaction.atomic():
        GuestContext.objects.select_for_update().get(id=guest.id)
        item = _owned_locked_analysis(guest, analysis_id)
        if item.report_operation_token != operation_token or item.input_revision != expected_input_revision:
            raise OperationConflict("a newer operation superseded this edit")
        item.product_label = data["product_label"]
        item.price_toman = data["price_toman"]
        item.budget_toman = data.get("budget_toman")
        item.answers = data["answers"]
        item.input_revision += 1
        item.report_operation_token = None
        item.save()
        _publish_report(item, report_payload, input_revision=item.input_revision, preserve_if_identical=False)
    return Analysis.objects.select_related("report").get(id=item.id)


def reanalyze_analysis(guest, analysis_id, expected_input_revision, expected_report_revision_id, generator=None):
    operation_token = uuid.uuid4()
    with transaction.atomic():
        GuestContext.objects.select_for_update().get(id=guest.id)
        item = _owned_locked_analysis(guest, analysis_id)
        report = CurrentReport.objects.select_for_update().get(analysis=item)
        if item.input_revision != expected_input_revision or str(report.report_revision_id) != str(expected_report_revision_id):
            raise RevisionConflict("analysis or report revision changed")
        item.report_operation_token = operation_token
        item.save(update_fields=["report_operation_token"])
        data = {
            "product_label": item.product_label,
            "price_toman": item.price_toman,
            "budget_toman": item.budget_toman,
            "answers": item.answers,
        }

    _result, report_payload = build_report(data, generator=generator)

    with transaction.atomic():
        GuestContext.objects.select_for_update().get(id=guest.id)
        item = _owned_locked_analysis(guest, analysis_id)
        report = CurrentReport.objects.select_for_update().get(analysis=item)
        if item.report_operation_token != operation_token:
            raise OperationConflict("a newer operation superseded this retry")
        if item.input_revision != expected_input_revision or str(report.report_revision_id) != str(expected_report_revision_id):
            raise OperationConflict("analysis or report revision changed during retry")
        _publish_report(item, report_payload, input_revision=item.input_revision, preserve_if_identical=True)
        item.report_operation_token = None
        item.save(update_fields=["report_operation_token"])
    return Analysis.objects.select_related("report").get(id=item.id)


def clear_history(guest):
    with transaction.atomic():
        locked_guest = GuestContext.objects.select_for_update().get(id=guest.id)
        locked_guest.generation_epoch += 1
        locked_guest.save(update_fields=["generation_epoch"])
        deleted_count = locked_guest.analyses.count()
        locked_guest.analyses.all().delete()
    return deleted_count


def delete_analysis(guest, analysis_id):
    with transaction.atomic():
        GuestContext.objects.select_for_update().get(id=guest.id)
        item = _owned_locked_analysis(guest, analysis_id)
        item.delete()


def set_feedback(guest, analysis_id, report_revision_id, rating):
    with transaction.atomic():
        item = _owned_locked_analysis(guest, analysis_id)
        report = CurrentReport.objects.select_for_update().get(analysis=item)
        if str(report.report_revision_id) != str(report_revision_id):
            raise RevisionConflict("feedback targets a stale report")
        feedback, _ = UsefulnessFeedback.objects.update_or_create(
            analysis=item,
            defaults={"report_revision_id": report.report_revision_id, "report_mode": report.mode, "rating": rating},
        )
    return feedback


def delete_feedback(guest, analysis_id, report_revision_id):
    with transaction.atomic():
        item = _owned_locked_analysis(guest, analysis_id)
        report = CurrentReport.objects.select_for_update().get(analysis=item)
        if str(report.report_revision_id) != str(report_revision_id):
            raise RevisionConflict("feedback targets a stale report")
        UsefulnessFeedback.objects.filter(analysis=item, report_revision_id=report.report_revision_id).delete()


def active_analyses(guest):
    return Analysis.objects.filter(guest_context=guest, expires_at__gt=timezone.now()).select_related("report").order_by("-created_at")

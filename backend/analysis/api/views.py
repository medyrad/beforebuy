from django.http import Http404
from rest_framework import status
from rest_framework.response import Response

from analysis.guest import extend_guest_session_for_new_analysis, get_or_create_guest
from analysis import services
from analysis.ai.factory import configured_explanation_generator
from analysis.services import active_analyses, create_analysis

from .base import CsrfProtectedAPIView
from .serializers import AnalysisInputSerializer, AnalysisUpdateSerializer, FeedbackInputSerializer, ReanalysisSerializer


def explanation_generator(request, guest):
    return configured_explanation_generator(request, guest)


def conflict_response(exc):
    code = "REVISION_CONFLICT" if isinstance(exc, services.RevisionConflict) else "OPERATION_CONFLICT"
    return Response({"error": {"code": code, "message": "نسخهٔ مورد انتظار تغییر کرده است."}}, status=409)


def serialize_report(report):
    feedback = getattr(report.analysis, "feedback", None)
    return {
        "report_revision_id": str(report.report_revision_id),
        "rubric_id": report.rubric_id,
        "mode": report.mode,
        "primary_outcome": report.primary_outcome,
        "dimensions": report.dimensions,
        "matched_rule_ids": report.matched_rule_ids,
        "evidence": report.evidence,
        "unknowns": report.unknowns,
        "actions": report.actions,
        "headline_fa": report.headline_fa,
        "explanation_blocks": report.explanation_blocks,
        "feedback": None if feedback is None else {
            "report_revision_id": str(feedback.report_revision_id),
            "report_mode": feedback.report_mode,
            "rating": feedback.rating,
        },
    }


def serialize_analysis(item, *, summary=False):
    base = {
        "id": str(item.id),
        "product_label": item.product_label,
        "created_at": item.created_at.isoformat(),
        "expires_at": item.expires_at.isoformat(),
    }
    if summary:
        return base | {"primary_outcome": item.report.primary_outcome, "mode": item.report.mode}
    return base | {
        "input_revision": item.input_revision,
        "price_toman": item.price_toman,
        "budget_toman": item.budget_toman,
        "answers": item.answers,
        "report": serialize_report(item.report),
    }


class AnalysisListCreateView(CsrfProtectedAPIView):
    def get(self, request):
        guest = get_or_create_guest(request)
        return Response({"items": [serialize_analysis(item, summary=True) for item in active_analyses(guest)]})

    def post(self, request):
        guest = get_or_create_guest(request)
        serializer = AnalysisInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = create_analysis(guest, serializer.validated_data, generator=explanation_generator(request, guest))
        extend_guest_session_for_new_analysis(request, item.expires_at)
        return Response(serialize_analysis(item), status=status.HTTP_201_CREATED)


class AnalysisDetailView(CsrfProtectedAPIView):
    def get_object(self, request, analysis_id):
        guest = get_or_create_guest(request)
        item = active_analyses(guest).filter(id=analysis_id).first()
        if item is None:
            raise Http404
        return item

    def get(self, request, analysis_id):
        return Response(serialize_analysis(self.get_object(request, analysis_id)))

    def patch(self, request, analysis_id):
        guest = get_or_create_guest(request)
        serializer = AnalysisUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        expected = data.pop("expected_input_revision")
        try:
            item = services.update_analysis(
                guest, analysis_id, expected, data, generator=explanation_generator(request, guest)
            )
        except services.AnalysisNotFound:
            raise Http404
        except services.OperationConflict as exc:
            return conflict_response(exc)
        return Response(serialize_analysis(item))

    def delete(self, request, analysis_id):
        guest = get_or_create_guest(request)
        try:
            services.delete_analysis(guest, analysis_id)
        except services.AnalysisNotFound:
            raise Http404
        return Response(status=status.HTTP_204_NO_CONTENT)


class ClearHistoryView(CsrfProtectedAPIView):
    def post(self, request):
        guest = get_or_create_guest(request)
        return Response({"deleted_count": services.clear_history(guest)})


class ReanalysisView(CsrfProtectedAPIView):
    def post(self, request, analysis_id):
        guest = get_or_create_guest(request)
        serializer = ReanalysisSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            item = services.reanalyze_analysis(
                guest, analysis_id, generator=explanation_generator(request, guest), **serializer.validated_data
            )
        except services.AnalysisNotFound:
            raise Http404
        except services.OperationConflict as exc:
            return conflict_response(exc)
        return Response(serialize_analysis(item))


class FeedbackView(CsrfProtectedAPIView):
    def put(self, request, analysis_id):
        guest = get_or_create_guest(request)
        serializer = FeedbackInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            feedback = services.set_feedback(guest, analysis_id, **serializer.validated_data)
        except services.AnalysisNotFound:
            raise Http404
        except services.OperationConflict as exc:
            return conflict_response(exc)
        return Response({
            "report_revision_id": str(feedback.report_revision_id),
            "report_mode": feedback.report_mode,
            "rating": feedback.rating,
        })

    def delete(self, request, analysis_id):
        guest = get_or_create_guest(request)
        report_revision_id = request.query_params.get("report_revision_id")
        if not report_revision_id:
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "report_revision_id الزامی است."}}, status=400)
        try:
            services.delete_feedback(guest, analysis_id, report_revision_id)
        except services.AnalysisNotFound:
            raise Http404
        except services.OperationConflict as exc:
            return conflict_response(exc)
        return Response(status=status.HTTP_204_NO_CONTENT)

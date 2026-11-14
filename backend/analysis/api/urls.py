from django.urls import path

from .health import live, ready
from .session import bootstrap_session
from .views import AnalysisDetailView, AnalysisListCreateView, ClearHistoryView, FeedbackView, ReanalysisView

urlpatterns = [
    path("health/live", live, name="health-live"),
    path("health/ready", ready, name="health-ready"),
    path("session", bootstrap_session, name="session"),
    path("analyses", AnalysisListCreateView.as_view(), name="analysis-list"),
    path("analyses/clear", ClearHistoryView.as_view(), name="analysis-clear"),
    path("analyses/<uuid:analysis_id>", AnalysisDetailView.as_view(), name="analysis-detail"),
    path("analyses/<uuid:analysis_id>/reanalysis", ReanalysisView.as_view(), name="analysis-reanalysis"),
    path("analyses/<uuid:analysis_id>/feedback", FeedbackView.as_view(), name="analysis-feedback"),
]

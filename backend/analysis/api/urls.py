from django.urls import path

from .health import live, ready
from .session import bootstrap_session
from .views import AnalysisDetailView, AnalysisListCreateView, ClearHistoryView, FeedbackView, ReanalysisView
from .conversations import (
    BriefConfirmView, BriefView, ConversationDetailView, ConversationListCreateView, MessageSubmitView,
)
from .operations import OperationCancelView, OperationDetailView, OperationEventView
from .uploads import UploadCreateView, UploadDetailView
from .research import ResearchCancelView, ResearchDetailView, ResearchStartView
from .choices import ChoiceCandidatesView, ChoiceDemoView, ChoiceDeskView

urlpatterns = [
    path('conversations/<uuid:conversation_id>/choices', ChoiceDeskView.as_view(), name='choice-desk'),
    path('conversations/<uuid:conversation_id>/choices/candidates', ChoiceCandidatesView.as_view(), name='choice-candidates'),
    path('conversations/<uuid:conversation_id>/choices/demo', ChoiceDemoView.as_view(), name='choice-demo'),
    path("health/live", live, name="health-live"),
    path("health/ready", ready, name="health-ready"),
    path("session", bootstrap_session, name="session"),
    path("analyses", AnalysisListCreateView.as_view(), name="analysis-list"),
    path("analyses/clear", ClearHistoryView.as_view(), name="analysis-clear"),
    path("analyses/<uuid:analysis_id>", AnalysisDetailView.as_view(), name="analysis-detail"),
    path("analyses/<uuid:analysis_id>/reanalysis", ReanalysisView.as_view(), name="analysis-reanalysis"),
    path("analyses/<uuid:analysis_id>/feedback", FeedbackView.as_view(), name="analysis-feedback"),
    path("conversations", ConversationListCreateView.as_view(), name="conversation-list"),
    path("conversations/<uuid:conversation_id>", ConversationDetailView.as_view(), name="conversation-detail"),
    path("conversations/<uuid:conversation_id>/messages", MessageSubmitView.as_view(), name="conversation-message"),
    path("conversations/<uuid:conversation_id>/brief", BriefView.as_view(), name="conversation-brief"),
    path("conversations/<uuid:conversation_id>/brief/confirm", BriefConfirmView.as_view(), name="conversation-brief-confirm"),
    path("conversations/<uuid:conversation_id>/research", ResearchStartView.as_view(), name="research-start"),
    path("research-jobs/<uuid:job_id>", ResearchDetailView.as_view(), name="research-detail"),
    path("research-jobs/<uuid:job_id>/cancel", ResearchCancelView.as_view(), name="research-cancel"),
    path("operations/<uuid:operation_id>", OperationDetailView.as_view(), name="operation-detail"),
    path("operations/<uuid:operation_id>/events", OperationEventView.as_view(), name="operation-events"),
    path("operations/<uuid:operation_id>/cancel", OperationCancelView.as_view(), name="operation-cancel"),
    path("uploads", UploadCreateView.as_view(), name="upload-create"),
    path("uploads/<uuid:upload_id>", UploadDetailView.as_view(), name="upload-detail"),
]

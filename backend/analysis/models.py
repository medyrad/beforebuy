import uuid
from datetime import timedelta

from django.db import models
from django.db import transaction
from django.utils import timezone


REPORT_MODES = [
    ("AI_ASSISTED_SUCCESS", "AI assisted success"),
    ("MOCK_ASSISTED", "Mock assisted"),
    ("RULE_BASED_LIMITED", "Rule based limited"),
]


class GuestContext(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    access_expires_at = models.DateTimeField(db_index=True)
    generation_epoch = models.PositiveBigIntegerField(default=0)


class Analysis(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    guest_context = models.ForeignKey(GuestContext, on_delete=models.CASCADE, related_name="analyses")
    input_revision = models.PositiveIntegerField(default=1)
    rubric_id = models.CharField(max_length=32, default="PDA-CAT-v0.3")
    questionnaire_schema = models.CharField(max_length=32, default="PDA-Q-v1")
    product_label = models.CharField(max_length=120)
    price_toman = models.BigIntegerField()
    budget_toman = models.BigIntegerField(null=True)
    answers = models.JSONField(default=dict)
    report_operation_token = models.UUIDField(null=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["guest_context", "expires_at", "-created_at"])]
        constraints = [
            models.CheckConstraint(condition=models.Q(price_toman__gt=0), name="analysis_price_positive"),
            models.CheckConstraint(
                condition=models.Q(budget_toman__isnull=True) | models.Q(budget_toman__gte=0),
                name="analysis_budget_null_or_nonnegative",
            ),
            models.CheckConstraint(condition=models.Q(input_revision__gt=0), name="analysis_revision_positive"),
        ]


class CurrentReport(models.Model):
    analysis = models.OneToOneField(Analysis, primary_key=True, on_delete=models.CASCADE, related_name="report")
    report_revision_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    input_revision = models.PositiveIntegerField()
    rubric_id = models.CharField(max_length=32)
    mode = models.CharField(max_length=32, choices=REPORT_MODES)
    primary_outcome = models.CharField(max_length=64)
    dimensions = models.JSONField(default=dict)
    matched_rule_ids = models.JSONField(default=list)
    evidence = models.JSONField(default=list)
    unknowns = models.JSONField(default=list)
    actions = models.JSONField(default=list)
    headline_fa = models.TextField()
    explanation_blocks = models.JSONField(default=list)
    canonical_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(input_revision__gt=0), name="report_revision_positive"),
        ]


class UsefulnessFeedback(models.Model):
    analysis = models.OneToOneField(Analysis, primary_key=True, on_delete=models.CASCADE, related_name="feedback")
    report_revision_id = models.UUIDField()
    report_mode = models.CharField(max_length=32, choices=REPORT_MODES)
    rating = models.PositiveSmallIntegerField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(rating__gte=1) & models.Q(rating__lte=5),
                name="feedback_rating_1_to_5",
            ),
        ]


class AILiveBudgetWindow(models.Model):
    day = models.DateField(primary_key=True)
    reserved_cost_microusd = models.PositiveBigIntegerField(default=0)
    spent_estimate_microusd = models.PositiveBigIntegerField(default=0)
    consecutive_failures = models.PositiveIntegerField(default=0)
    circuit_open_until = models.DateTimeField(null=True)
    updated_at = models.DateTimeField(auto_now=True)


class AIEvaluationAuthorization(models.Model):
    id = models.CharField(primary_key=True, max_length=64)
    authorized_toman = models.DecimalField(max_digits=18, decimal_places=6)
    reserved_toman = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    spent_estimate_toman = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(authorized_toman__gt=0), name="ai_eval_authorized_positive"),
            models.CheckConstraint(condition=models.Q(reserved_toman__gte=0), name="ai_eval_reserved_nonnegative"),
            models.CheckConstraint(condition=models.Q(spent_estimate_toman__gte=0), name="ai_eval_spent_nonnegative"),
        ]


class AIInvocation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    guest_context = models.ForeignKey(
        GuestContext, null=True, on_delete=models.SET_NULL, related_name="ai_invocations"
    )
    operation_id = models.UUIDField(unique=True, editable=False)
    provider = models.CharField(max_length=32)
    model = models.CharField(max_length=64)
    prompt_version = models.CharField(max_length=32)
    schema_version = models.CharField(max_length=32)
    status = models.CharField(max_length=16)
    error_class = models.CharField(max_length=40, null=True)
    attempt_count = models.PositiveSmallIntegerField(default=0)
    input_tokens = models.PositiveIntegerField(null=True)
    output_tokens = models.PositiveIntegerField(null=True)
    latency_ms = models.PositiveIntegerField(null=True)
    reserved_cost_microusd = models.PositiveBigIntegerField(default=0)
    estimated_cost_microusd = models.PositiveBigIntegerField(default=0)
    provider_request_id = models.CharField(max_length=128, null=True)
    provider_estimated_cost_toman = models.DecimalField(max_digits=18, decimal_places=6, null=True)
    evaluation_authorization = models.ForeignKey(
        AIEvaluationAuthorization, null=True, on_delete=models.PROTECT, related_name="invocations"
    )
    evaluation_reserved_toman = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    evaluation_run_id = models.CharField(max_length=64, null=True)
    evaluation_case_id = models.CharField(max_length=32, null=True)
    exchange_rate_toman_per_usd = models.DecimalField(max_digits=18, decimal_places=6, null=True)
    exchange_margin_ratio = models.DecimalField(max_digits=8, decimal_places=6, null=True)
    known_cost_microusd = models.PositiveBigIntegerField(default=0)
    unknown_cost_microusd = models.PositiveBigIntegerField(default=0)
    usage_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)

    class Meta:
        indexes = [models.Index(fields=["guest_context", "created_at"])]
        constraints = [
            models.CheckConstraint(condition=models.Q(attempt_count__lte=2), name="ai_attempt_count_at_most_two"),
        ]


COPILOT_RETENTION_DAYS = 90


def copilot_event_expiry():
    return timezone.now() + timedelta(hours=24)


def copilot_upload_expiry():
    return timezone.now() + timedelta(hours=24)


def copilot_brief_unknowns():
    return ["مخاطب خرید", "دستهٔ محصول", "بودجه", "کاربرد اصلی"]


class ConversationManager(models.Manager):
    @transaction.atomic
    def create_for_guest(self, guest_context, *, title="گفت‌وگوی خرید"):
        now = timezone.now()
        conversation = self.create(
            guest_context=guest_context,
            title=title,
            last_eligible_activity_at=now,
            expires_at=now + timedelta(days=COPILOT_RETENTION_DAYS),
        )
        ShoppingBrief.objects.create(conversation=conversation)
        return conversation


class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    guest_context = models.ForeignKey(GuestContext, on_delete=models.CASCADE, related_name="conversations")
    status = models.CharField(max_length=16, default="ACTIVE")
    title = models.CharField(max_length=120, default="گفت‌وگوی خرید")
    brief_revision = models.PositiveIntegerField(default=0)
    generation_epoch = models.PositiveBigIntegerField(default=0)
    last_eligible_activity_at = models.DateTimeField()
    expires_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ConversationManager()

    class Meta:
        indexes = [models.Index(fields=["guest_context", "-updated_at"])]
        constraints = [
            models.CheckConstraint(condition=models.Q(status="ACTIVE"), name="copilot_conversation_active_only"),
        ]


class ShoppingBrief(models.Model):
    conversation = models.OneToOneField(
        Conversation, primary_key=True, on_delete=models.CASCADE, related_name="brief"
    )
    revision = models.PositiveIntegerField(default=0)
    recipient_context = models.CharField(
        max_length=16, null=True, choices=[("SELF", "Self"), ("GIFT", "Gift"), ("HOUSEHOLD", "Household")]
    )
    category = models.CharField(max_length=120, null=True)
    selected_product_label = models.CharField(max_length=160, null=True)
    budget_toman = models.BigIntegerField(null=True)
    use_cases = models.JSONField(default=list)
    hard_constraints = models.JSONField(default=list)
    unknowns = models.JSONField(default=copilot_brief_unknowns)
    contradictions = models.JSONField(default=list)
    provenance = models.JSONField(default=list)
    confirmed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(budget_toman__isnull=True) | models.Q(budget_toman__gte=0),
                name="copilot_brief_budget_null_or_nonnegative",
            ),
        ]


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=16, choices=[("USER", "User"), ("ASSISTANT", "Assistant")])
    state = models.CharField(
        max_length=16,
        choices=[("ACCEPTED", "Accepted"), ("FINAL", "Final"), ("FAILED", "Failed"), ("CANCELLED", "Cancelled")],
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["conversation", "created_at"])]


class StreamOperation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="operations")
    user_message = models.OneToOneField(
        Message, null=True, on_delete=models.CASCADE, related_name="stream_operation"
    )
    final_message = models.OneToOneField(
        Message, null=True, blank=True, on_delete=models.SET_NULL, related_name="final_for_operation"
    )
    status = models.CharField(
        max_length=16,
        default="PENDING",
        choices=[
            ("PENDING", "Pending"), ("RUNNING", "Running"), ("COMPLETED", "Completed"),
            ("FAILED", "Failed"), ("CANCELLED", "Cancelled"), ("INTERRUPTED", "Interrupted"),
        ],
    )
    idempotency_key = models.CharField(max_length=128)
    request_hash = models.CharField(max_length=64)
    operation_token = models.UUIDField(default=uuid.uuid4, editable=False)
    expected_brief_revision = models.PositiveIntegerField()
    next_sequence = models.PositiveIntegerField(default=1)
    lease_owner = models.CharField(max_length=96, null=True)
    lease_expires_at = models.DateTimeField(null=True)
    cancel_requested_at = models.DateTimeField(null=True)
    terminal_code = models.CharField(max_length=64, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True)
    completed_at = models.DateTimeField(null=True)

    class Meta:
        indexes = [models.Index(fields=["conversation", "status", "created_at"])]
        constraints = [
            models.UniqueConstraint(
                fields=["conversation", "idempotency_key"], name="copilot_operation_idempotency_unique"
            ),
        ]


class StreamEvent(models.Model):
    operation = models.ForeignKey(StreamOperation, on_delete=models.CASCADE, related_name="events")
    sequence = models.PositiveIntegerField()
    event_type = models.CharField(max_length=64)
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=copilot_event_expiry, db_index=True)

    class Meta:
        ordering = ["sequence"]
        constraints = [
            models.UniqueConstraint(fields=["operation", "sequence"], name="copilot_event_sequence_unique"),
        ]


class UploadedImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="uploads")
    message = models.ForeignKey(Message, null=True, on_delete=models.CASCADE, related_name="uploads")
    media_type = models.CharField(max_length=32)
    content = models.BinaryField()
    size_bytes = models.PositiveIntegerField()
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    sha256 = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=copilot_upload_expiry, db_index=True)

    class Meta:
        indexes = [models.Index(fields=["conversation", "expires_at"])]
        constraints = [
            models.CheckConstraint(condition=models.Q(size_bytes__gt=0), name="copilot_upload_size_positive"),
            models.CheckConstraint(condition=models.Q(width__gt=0), name="copilot_upload_width_positive"),
            models.CheckConstraint(condition=models.Q(height__gt=0), name="copilot_upload_height_positive"),
        ]

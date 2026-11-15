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
    copilot_reserved_microusd = models.PositiveBigIntegerField(default=0)
    copilot_spent_microusd = models.PositiveBigIntegerField(default=0)


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
    temporary = models.BooleanField(default=False)
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


class CopilotSettings(models.Model):
    guest_context = models.OneToOneField(GuestContext, primary_key=True, on_delete=models.CASCADE)
    memory_enabled = models.BooleanField(default=False)
    provider = models.CharField(max_length=32, default="gapgpt")
    model = models.CharField(max_length=64, default="gapgpt-deepseek-v4.1-flash")
    revision = models.PositiveIntegerField(default=0)


class UserCredential(models.Model):
    guest_context = models.OneToOneField(GuestContext, primary_key=True, on_delete=models.CASCADE, related_name="credential")
    ciphertext = models.TextField()
    wrapped_key = models.TextField()
    revision = models.UUIDField(default=uuid.uuid4, editable=False)
    state = models.CharField(max_length=32, default="STORED_UNVALIDATED")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)


class ProviderCredential(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    guest_context = models.ForeignKey(GuestContext, on_delete=models.CASCADE, related_name="provider_credentials")
    provider = models.CharField(max_length=32)
    ciphertext = models.TextField()
    wrapped_key = models.TextField()
    revision = models.UUIDField(default=uuid.uuid4, editable=False)
    state = models.CharField(max_length=32, default="STORED_UNVALIDATED")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["guest_context", "provider"], name="copilot_provider_credential_unique"),
            models.CheckConstraint(condition=models.Q(provider__in=["gapgpt"]), name="copilot_provider_credential_supported"),
        ]


class PreferenceMemory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    guest_context = models.ForeignKey(GuestContext, on_delete=models.CASCADE, related_name="preferences")
    source_conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="derived_preferences")
    source_revision = models.PositiveIntegerField()
    category = models.CharField(max_length=120)
    criterion = models.JSONField()
    state = models.CharField(max_length=16, default="CANDIDATE", choices=[(s, s) for s in ("CANDIDATE", "CONFIRMED", "REJECTED")])
    revision = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True)
    expires_at = models.DateTimeField(db_index=True)


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
    comparison = models.JSONField(default=dict)
    conversation_state = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(budget_toman__isnull=True) | models.Q(budget_toman__gte=0),
                name="copilot_brief_budget_null_or_nonnegative",
            ),
        ]


class ChoiceSet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='choice_sets')
    brief_revision = models.PositiveIntegerField()
    generation_epoch = models.PositiveBigIntegerField()
    rule_version = models.CharField(max_length=64)
    result = models.JSONField()
    snapshot_ids = models.JSONField(default=list)
    evidence_valid_until = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=16, choices=[("USER", "User"), ("ASSISTANT", "Assistant")])
    state = models.CharField(
        max_length=16,
        choices=[("ACCEPTED", "Accepted"), ("FINAL", "Final"), ("FAILED", "Failed"), ("CANCELLED", "Cancelled")],
    )
    text = models.TextField()
    reply_actions = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["conversation", "created_at"])]


class StreamOperation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    credential_revision = models.UUIDField(null=True, editable=False)
    credential_provider = models.CharField(max_length=32, null=True, editable=False)
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
    operation_kind = models.CharField(
        max_length=16,
        default="CONVERSATION",
        choices=[("CONVERSATION", "Conversation"), ("RESEARCH", "Research")],
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
    context_manifest = models.JSONField(default=dict)
    context_fingerprint = models.CharField(max_length=64, null=True)
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


RESEARCH_ACTIVE_STATUSES = ["PENDING", "RUNNING"]


class SourcePolicy(models.Model):
    hostname = models.CharField(max_length=253, unique=True)
    allowed_ports = models.JSONField(default=list)
    allowed_path_prefixes = models.JSONField(default=list)
    redirect_hostnames = models.JSONField(default=list)
    redirect_rules = models.JSONField(default=dict)
    source_role = models.CharField(
        max_length=24,
        choices=[
            ("MANUFACTURER", "Manufacturer"),
            ("MERCHANT", "Merchant"),
            ("COMPARISON", "Comparison"),
            ("EXPERT", "Expert"),
            ("CUSTOMER_REVIEW", "Customer review"),
        ],
    )
    readiness = models.CharField(
        max_length=32,
        choices=[
            ("DISABLED", "Disabled"),
            ("SYNTHETIC_FIXTURE", "Synthetic fixture"),
            ("CAPTURED_REAL_FIXTURE", "Captured real fixture"),
            ("LIVE_PROBE", "Live probe"),
            ("REPEATABLE_LIVE_EXTRACTION", "Repeatable live extraction"),
            ("ENABLED", "Enabled"),
        ],
    )
    live_enabled = models.BooleanField(default=False)
    robots_url = models.URLField(max_length=500, null=True)
    robots_observed_at = models.DateTimeField(null=True)
    terms_url = models.URLField(max_length=500, null=True)
    terms_observed_at = models.DateTimeField(null=True)
    access_notes = models.TextField(default="")
    retention_notes = models.TextField(default="")
    display_constraints = models.TextField(default="")
    freshness_seconds = models.PositiveIntegerField(default=86400)
    min_interval_ms = models.PositiveIntegerField(default=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.hostname = self.hostname.rstrip(".").lower()
        if not self.allowed_ports:
            self.allowed_ports = [443]
        super().save(*args, **kwargs)


class ResearchJob(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="research_jobs")
    operation = models.OneToOneField(StreamOperation, on_delete=models.CASCADE, related_name="research_job")
    brief_revision = models.PositiveIntegerField()
    generation_epoch = models.PositiveBigIntegerField()
    request_hash = models.CharField(max_length=64)
    mode = models.CharField(max_length=16, choices=[("FIXTURE", "Fixture"), ("LIVE", "Live")])
    source_ids = models.JSONField(default=list)
    targets = models.JSONField(default=list)
    limits = models.JSONField(default=dict)
    status = models.CharField(
        max_length=32,
        default="PENDING",
        choices=[
            ("PENDING", "Pending"),
            ("RUNNING", "Running"),
            ("SUCCESS", "Success"),
            ("PARTIAL_SUCCESS", "Partial success"),
            ("NO_SUPPORTED_SOURCES", "No supported sources"),
            ("BLOCKED_SOURCE", "Blocked source"),
            ("EXTRACTION_FAILED", "Extraction failed"),
            ("TIMED_OUT", "Timed out"),
            ("CANCELLED", "Cancelled"),
            ("INTERRUPTED", "Interrupted"),
            ("FAILED", "Failed"),
        ],
    )
    stage = models.CharField(max_length=32, default="QUEUED")
    completed_units = models.PositiveIntegerField(default=0)
    total_units = models.PositiveIntegerField(default=0)
    request_count = models.PositiveIntegerField(default=0)
    decoded_bytes = models.PositiveBigIntegerField(default=0)
    wire_bytes = models.PositiveBigIntegerField(default=0)
    redirect_count = models.PositiveIntegerField(default=0)
    coverage = models.JSONField(default=dict)
    terminal_code = models.CharField(max_length=64, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True)
    completed_at = models.DateTimeField(null=True)

    class Meta:
        indexes = [models.Index(fields=["conversation", "-created_at"])]
        constraints = [
            models.UniqueConstraint(
                fields=["conversation"],
                condition=models.Q(status__in=RESEARCH_ACTIVE_STATUSES),
                name="copilot_one_active_research_per_conversation",
            ),
            models.CheckConstraint(
                condition=models.Q(completed_units__lte=models.F("total_units")),
                name="copilot_research_progress_within_total",
            ),
        ]


class SourceSnapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    research_job = models.ForeignKey(ResearchJob, on_delete=models.CASCADE, related_name="snapshots")
    source_policy = models.ForeignKey(SourcePolicy, on_delete=models.PROTECT, related_name="snapshots")
    canonical_url = models.URLField(max_length=1000, null=True)
    fixture_label = models.CharField(max_length=120, null=True)
    source_role = models.CharField(max_length=24)
    retrieval_time = models.DateTimeField()
    status = models.CharField(max_length=32)
    http_status = models.PositiveSmallIntegerField(null=True)
    content_type = models.CharField(max_length=120, null=True)
    response_bytes = models.PositiveIntegerField(default=0)
    fingerprint = models.CharField(max_length=64)
    extractor_version = models.CharField(max_length=64, null=True)
    failure_code = models.CharField(max_length=64, null=True)
    raw_content = models.BinaryField(null=True)
    raw_expires_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(models.Q(canonical_url__isnull=False) | models.Q(fixture_label__isnull=False)),
                name="copilot_snapshot_source_or_fixture",
            ),
        ]


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    brand = models.CharField(max_length=120)
    model_name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)


class Variant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    canonical_identifier = models.CharField(max_length=160, null=True)
    identifiers = models.JSONField(default=dict)
    attributes = models.JSONField(default=dict)
    region = models.CharField(max_length=80, null=True)
    bundle = models.BooleanField(default=False)
    condition = models.CharField(
        max_length=16,
        default="NEW",
        choices=[("NEW", "New"), ("USED", "Used"), ("REFURBISHED", "Refurbished"), ("UNKNOWN", "Unknown")],
    )


class Offer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    snapshot = models.ForeignKey(SourceSnapshot, on_delete=models.CASCADE, related_name="offers")
    variant = models.ForeignKey(Variant, on_delete=models.PROTECT, related_name="offers")
    item_price_minor = models.BigIntegerField(null=True)
    currency = models.CharField(max_length=12, null=True)
    price_toman = models.BigIntegerField(null=True)
    shipping_minor = models.BigIntegerField(null=True)
    mandatory_charges_minor = models.BigIntegerField(null=True)
    total_payable_minor = models.BigIntegerField(null=True)
    seller = models.CharField(max_length=200, null=True)
    merchant_url = models.URLField(max_length=1000, null=True)
    observation_kind = models.CharField(
        max_length=32,
        choices=[("COMPARISON_OBSERVED", "Comparison observed"), ("MERCHANT_PAGE_VERIFIED", "Merchant page verified")],
        default="MERCHANT_PAGE_VERIFIED",
    )
    warranty = models.CharField(max_length=200, null=True)
    registration = models.CharField(max_length=200, null=True)
    availability = models.CharField(
        max_length=24,
        choices=[
            ("IN_STOCK", "In stock"),
            ("OUT_OF_STOCK", "Out of stock"),
            ("PREORDER", "Preorder"),
            ("UNKNOWN", "Unknown"),
        ],
        default="UNKNOWN",
    )
    observed_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(item_price_minor__isnull=True) | models.Q(item_price_minor__gte=0),
                name="copilot_offer_item_price_nonnegative",
            ),
            models.CheckConstraint(
                condition=models.Q(price_toman__isnull=True) | models.Q(price_toman__gte=0),
                name="copilot_offer_price_toman_nonnegative",
            ),
            models.CheckConstraint(
                condition=models.Q(shipping_minor__isnull=True) | models.Q(shipping_minor__gte=0),
                name="copilot_offer_shipping_nonnegative",
            ),
            models.CheckConstraint(
                condition=models.Q(mandatory_charges_minor__isnull=True) | models.Q(mandatory_charges_minor__gte=0),
                name="copilot_offer_mandatory_charges_nonnegative",
            ),
            models.CheckConstraint(
                condition=models.Q(total_payable_minor__isnull=True) | models.Q(total_payable_minor__gte=0),
                name="copilot_offer_total_nonnegative",
            ),
        ]


class EvidenceClaim(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    snapshot = models.ForeignKey(SourceSnapshot, on_delete=models.CASCADE, related_name="claims")
    variant = models.ForeignKey(Variant, null=True, on_delete=models.PROTECT, related_name="claims")
    field = models.CharField(max_length=120)
    normalized_value = models.JSONField(null=True)
    source_location = models.CharField(max_length=500, null=True)
    supporting_excerpt = models.CharField(max_length=500, null=True)
    evidence_status = models.CharField(
        max_length=16,
        choices=[
            ("SUPPORTED", "Supported"),
            ("UNKNOWN", "Unknown"),
            ("CONFLICTING", "Conflicting"),
            ("STALE", "Stale"),
        ],
    )
    created_at = models.DateTimeField(auto_now_add=True)

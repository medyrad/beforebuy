import uuid

from django.db import models


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


class AIInvocation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    guest_context = models.ForeignKey(GuestContext, on_delete=models.CASCADE, related_name="ai_invocations")
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
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)

    class Meta:
        indexes = [models.Index(fields=["guest_context", "created_at"])]
        constraints = [
            models.CheckConstraint(condition=models.Q(attempt_count__lte=2), name="ai_attempt_count_at_most_two"),
        ]

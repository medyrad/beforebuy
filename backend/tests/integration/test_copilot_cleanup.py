from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from analysis.models import (
    Conversation,
    EvidenceClaim,
    GuestContext,
    Message,
    Product,
    ResearchJob,
    SourcePolicy,
    SourceSnapshot,
    StreamEvent,
    StreamOperation,
    UploadedImage,
    Variant,
)


class CopilotCleanupTests(TestCase):
    def test_active_conversation_prevents_guest_cleanup(self):
        guest = GuestContext.objects.create(access_expires_at=timezone.now() - timedelta(days=1))
        conversation = Conversation.objects.create_for_guest(guest)
        call_command("purge_expired_analyses", stdout=StringIO())
        self.assertTrue(GuestContext.objects.filter(id=guest.id).exists())
        self.assertTrue(Conversation.objects.filter(id=conversation.id).exists())

    def test_expired_conversation_is_purged_before_owner(self):
        guest = GuestContext.objects.create(access_expires_at=timezone.now() - timedelta(days=1))
        conversation = Conversation.objects.create_for_guest(guest)
        Conversation.objects.filter(id=conversation.id).update(expires_at=timezone.now() - timedelta(seconds=1))
        call_command("purge_expired_analyses", stdout=StringIO())
        self.assertFalse(Conversation.objects.filter(id=conversation.id).exists())
        self.assertFalse(GuestContext.objects.filter(id=guest.id).exists())

    def test_expired_upload_and_stream_event_are_purged_without_deleting_active_owner(self):
        guest = GuestContext.objects.create(access_expires_at=timezone.now() + timedelta(days=1))
        conversation = Conversation.objects.create_for_guest(guest)
        message = Message.objects.create(conversation=conversation, role="USER", state="ACCEPTED", text="fixture")
        operation = StreamOperation.objects.create(
            conversation=conversation,
            user_message=message,
            idempotency_key="cleanup-evidence-key-001",
            request_hash="1" * 64,
            expected_brief_revision=0,
        )
        event = StreamEvent.objects.create(
            operation=operation, sequence=1, event_type="operation.started", payload={"sequence": 1}
        )
        upload = UploadedImage.objects.create(
            conversation=conversation,
            media_type="image/png",
            content=b"sanitized",
            size_bytes=9,
            width=1,
            height=1,
            sha256="2" * 64,
        )
        expired = timezone.now() - timedelta(seconds=1)
        StreamEvent.objects.filter(id=event.id).update(expires_at=expired)
        UploadedImage.objects.filter(id=upload.id).update(expires_at=expired)

        call_command("purge_expired_analyses", stdout=StringIO())

        self.assertFalse(StreamEvent.objects.filter(id=event.id).exists())
        self.assertFalse(UploadedImage.objects.filter(id=upload.id).exists())
        self.assertTrue(Conversation.objects.filter(id=conversation.id).exists())
        self.assertTrue(GuestContext.objects.filter(id=guest.id).exists())

    def test_expired_raw_research_cache_is_cleared_without_deleting_normalized_evidence(self):
        guest = GuestContext.objects.create(access_expires_at=timezone.now() + timedelta(days=1))
        conversation = Conversation.objects.create_for_guest(guest)
        operation = StreamOperation.objects.create(
            conversation=conversation,
            operation_kind="RESEARCH",
            idempotency_key="cleanup-research-key-001",
            request_hash="4" * 64,
            expected_brief_revision=0,
        )
        job = ResearchJob.objects.create(
            conversation=conversation,
            operation=operation,
            brief_revision=0,
            generation_epoch=0,
            request_hash="4" * 64,
            mode="FIXTURE",
            status="SUCCESS",
            limits={},
        )
        policy = SourcePolicy.objects.create(
            hostname="fixture.invalid",
            allowed_path_prefixes=[],
            redirect_hostnames=[],
            source_role="MANUFACTURER",
            readiness="SYNTHETIC_FIXTURE",
        )
        snapshot = SourceSnapshot.objects.create(
            research_job=job,
            source_policy=policy,
            fixture_label="cleanup-fixture",
            source_role="MANUFACTURER",
            retrieval_time=timezone.now() - timedelta(hours=25),
            status="EXTRACTED",
            response_bytes=3,
            fingerprint="5" * 64,
            raw_content=b"raw",
            raw_expires_at=timezone.now() - timedelta(seconds=1),
        )
        call_command("purge_expired_analyses", stdout=StringIO())
        snapshot.refresh_from_db()
        self.assertIsNone(snapshot.raw_content)
        self.assertTrue(SourceSnapshot.objects.filter(id=snapshot.id).exists())

    def test_expired_conversation_purges_only_unreferenced_product_identity(self):
        guest = GuestContext.objects.create(access_expires_at=timezone.now() + timedelta(days=1))
        conversation = Conversation.objects.create_for_guest(guest)
        operation = StreamOperation.objects.create(
            conversation=conversation,
            operation_kind="RESEARCH",
            idempotency_key="cleanup-research-identity-001",
            request_hash="6" * 64,
            expected_brief_revision=0,
        )
        job = ResearchJob.objects.create(
            conversation=conversation,
            operation=operation,
            brief_revision=0,
            generation_epoch=0,
            request_hash="6" * 64,
            mode="FIXTURE",
            status="SUCCESS",
            limits={},
        )
        policy = SourcePolicy.objects.create(
            hostname="identity-fixture.invalid",
            source_role="MANUFACTURER",
            readiness="SYNTHETIC_FIXTURE",
        )
        snapshot = SourceSnapshot.objects.create(
            research_job=job,
            source_policy=policy,
            fixture_label="identity-cleanup-fixture",
            source_role="MANUFACTURER",
            retrieval_time=timezone.now(),
            status="EXTRACTED",
            fingerprint="7" * 64,
            raw_expires_at=timezone.now() + timedelta(hours=24),
        )
        product = Product.objects.create(brand="نمونه", model_name="مدل پاک‌سازی")
        variant = Variant.objects.create(product=product, canonical_identifier="CLEANUP-1")
        EvidenceClaim.objects.create(
            snapshot=snapshot,
            variant=variant,
            field="model",
            normalized_value={"value": "CLEANUP-1"},
            evidence_status="SUPPORTED",
        )
        Conversation.objects.filter(id=conversation.id).update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )

        call_command("purge_expired_analyses", stdout=StringIO())

        self.assertFalse(Variant.objects.filter(id=variant.id).exists())
        self.assertFalse(Product.objects.filter(id=product.id).exists())

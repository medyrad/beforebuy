from datetime import timedelta

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from analysis.models import (
    Conversation,
    EvidenceClaim,
    GuestContext,
    Offer,
    Product,
    ResearchJob,
    SourcePolicy,
    SourceSnapshot,
    StreamOperation,
    Variant,
)


class ResearchModelTests(TestCase):
    def setUp(self):
        self.guest = GuestContext.objects.create(access_expires_at=timezone.now() + timedelta(days=90))
        self.conversation = Conversation.objects.create_for_guest(self.guest)
        self.operation = StreamOperation.objects.create(
            conversation=self.conversation,
            operation_kind="RESEARCH",
            idempotency_key="research-model-key-001",
            request_hash="1" * 64,
            expected_brief_revision=0,
        )
        self.job = ResearchJob.objects.create(
            conversation=self.conversation,
            operation=self.operation,
            brief_revision=0,
            generation_epoch=0,
            request_hash="1" * 64,
            mode="FIXTURE",
            limits={"max_total_requests": 20},
        )
        self.policy = SourcePolicy.objects.create(
            hostname="example.test",
            allowed_path_prefixes=["/products/"],
            redirect_hostnames=[],
            source_role="MANUFACTURER",
            readiness="SYNTHETIC_FIXTURE",
        )

    def test_snapshot_claim_offer_keep_retrieval_and_owner_provenance(self):
        retrieved = timezone.now()
        snapshot = SourceSnapshot.objects.create(
            research_job=self.job,
            source_policy=self.policy,
            canonical_url=None,
            fixture_label="synthetic-appliance-v1",
            source_role="MANUFACTURER",
            retrieval_time=retrieved,
            status="EXTRACTED",
            content_type="application/ld+json",
            response_bytes=240,
            fingerprint="a" * 64,
            extractor_version="JSONLD-v1",
            raw_expires_at=retrieved + timedelta(hours=24),
        )
        product = Product.objects.create(brand="Philips", model_name="Series 5000")
        variant = Variant.objects.create(product=product, canonical_identifier="EP5934/10R1", attributes={})
        claim = EvidenceClaim.objects.create(
            snapshot=snapshot,
            variant=variant,
            field="water_tank_capacity",
            normalized_value={"value": "1.8", "unit": "L"},
            source_location="jsonld:additionalProperty[water tank]",
            evidence_status="SUPPORTED",
        )
        offer = Offer.objects.create(
            snapshot=snapshot,
            variant=variant,
            item_price_minor=113_800_000,
            currency="TOMAN",
            shipping_minor=None,
            total_payable_minor=None,
            availability="OUT_OF_STOCK",
            observed_at=retrieved,
        )
        self.assertEqual(claim.snapshot.research_job.conversation_id, self.conversation.id)
        self.assertEqual(offer.shipping_minor, None)
        self.assertEqual(offer.total_payable_minor, None)
        self.assertEqual(snapshot.raw_expires_at, retrieved + timedelta(hours=24))

    def test_policy_hostname_and_active_job_are_unique(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            SourcePolicy.objects.create(
                hostname="EXAMPLE.test",
                allowed_path_prefixes=["/"],
                redirect_hostnames=[],
                source_role="MERCHANT",
                readiness="DISABLED",
            )
        second_operation = StreamOperation.objects.create(
            conversation=self.conversation,
            operation_kind="RESEARCH",
            idempotency_key="research-model-key-002",
            request_hash="2" * 64,
            expected_brief_revision=0,
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            ResearchJob.objects.create(
                conversation=self.conversation,
                operation=second_operation,
                brief_revision=0,
                generation_epoch=0,
                request_hash="2" * 64,
                mode="FIXTURE",
                limits={},
            )

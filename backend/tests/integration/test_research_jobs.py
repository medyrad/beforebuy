from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from analysis.models import Conversation, GuestContext, ResearchJob, SourceSnapshot, StreamOperation
from analysis.research.jobs import (
    DEFAULT_LIMITS,
    complete_research_job,
    create_research_job,
    publish_research_progress,
    perform_research,
)


class ResearchJobLifecycleTests(TestCase):
    def setUp(self):
        self.guest = GuestContext.objects.create(access_expires_at=timezone.now() + timedelta(days=90))
        self.conversation = Conversation.objects.create_for_guest(self.guest)
        self.conversation.brief.confirmed = True
        self.conversation.brief.save(update_fields=["confirmed"])
        self.job, _ = create_research_job(
            conversation=self.conversation,
            idempotency_key="research-lifecycle-001",
            request_hash="7" * 64,
            source_ids=["synthetic-appliance-v1", "blocked-sports-v1"],
            mode="FIXTURE",
        )

    def test_limits_are_immutable_and_progress_counts_completed_work_only(self):
        self.assertEqual(self.job.limits, DEFAULT_LIMITS)
        owner = "research-worker-test"
        from analysis.conversation.streaming import claim_operation
        self.assertTrue(claim_operation(self.job.operation_id, owner))
        self.assertTrue(publish_research_progress(self.job.id, owner, stage="FETCH", completed=1, total=2))
        self.job.refresh_from_db()
        self.assertEqual(self.job.completed_units, 1)
        event = self.job.operation.events.get(event_type="research.progress")
        self.assertEqual(event.payload["completed"], 1)
        self.assertEqual(event.payload["total"], 2)

    def test_partial_success_preserves_coverage_and_completes_without_final_message(self):
        owner = "research-worker-partial"
        from analysis.conversation.streaming import claim_operation
        self.assertTrue(claim_operation(self.job.operation_id, owner))
        result = complete_research_job(
            self.job.id,
            owner,
            coverage={"extracted": ["synthetic-appliance-v1"], "blocked": ["blocked-sports-v1"]},
            outcome="PARTIAL_SUCCESS",
        )
        self.assertTrue(result)
        self.job.refresh_from_db()
        self.job.operation.refresh_from_db()
        self.assertEqual(self.job.status, "PARTIAL_SUCCESS")
        self.assertEqual(self.job.operation.status, "COMPLETED")
        self.assertIsNone(self.job.operation.final_message_id)
        self.assertEqual(self.job.coverage["blocked"], ["blocked-sports-v1"])

    def test_expired_lease_prevents_late_publication(self):
        owner = "research-worker-stale"
        from analysis.conversation.streaming import claim_operation
        self.assertTrue(claim_operation(self.job.operation_id, owner))
        StreamOperation.objects.filter(id=self.job.operation_id).update(lease_expires_at=timezone.now())
        self.assertFalse(publish_research_progress(self.job.id, owner, stage="EXTRACT", completed=2, total=2))
        self.assertFalse(complete_research_job(self.job.id, owner, coverage={}, outcome="SUCCESS"))

    def test_brief_edit_and_conversation_expiry_prevent_late_publication(self):
        owner = "research-worker-edited"
        from analysis.conversation.streaming import claim_operation
        self.assertTrue(claim_operation(self.job.operation_id, owner))
        Conversation.objects.filter(id=self.conversation.id).update(brief_revision=1)
        self.assertFalse(publish_research_progress(self.job.id, owner, stage="EXTRACT", completed=1, total=2))
        self.assertFalse(complete_research_job(self.job.id, owner, coverage={}, outcome="SUCCESS"))

        Conversation.objects.filter(id=self.conversation.id).update(
            brief_revision=0, expires_at=timezone.now() - timedelta(seconds=1)
        )
        self.assertFalse(publish_research_progress(self.job.id, owner, stage="EXTRACT", completed=1, total=2))

    def test_fixture_work_renews_lease_without_reviving_expired_owner(self):
        owner = "research-worker-renew"
        from analysis.conversation.streaming import claim_operation
        self.assertTrue(claim_operation(self.job.operation_id, owner))
        before = StreamOperation.objects.get(id=self.job.operation_id).lease_expires_at
        self.assertTrue(perform_research(self.job.id, owner))
        operation = StreamOperation.objects.get(id=self.job.operation_id)
        self.assertEqual(operation.status, "COMPLETED")
        self.assertIsNone(operation.lease_expires_at)
        self.assertGreater(operation.completed_at, before - timedelta(seconds=30))

    @patch("analysis.research.jobs.perform_research")
    @patch("analysis.research.jobs.close_old_connections")
    def test_worker_interruption_does_not_automatically_repeat_network_work(self, _close, perform):
        perform.side_effect = RuntimeError("process interrupted")
        from analysis.research.jobs import execute_research_job
        execute_research_job(self.job.id, worker_identity="research-worker-crash", release_slot=False)
        self.job.operation.refresh_from_db()
        self.assertEqual(perform.call_count, 1)
        self.assertEqual(self.job.operation.status, "FAILED")
        self.assertFalse(self.job.operation.events.filter(event_type="operation.started").count() > 1)

    def test_owner_scoped_cache_hit_preserves_original_retrieval_time_and_expiry(self):
        owner = "research-worker-cache-1"
        from analysis.conversation.streaming import claim_operation
        self.assertTrue(claim_operation(self.job.operation_id, owner))
        self.assertTrue(perform_research(self.job.id, owner))
        original = self.job.snapshots.get(fixture_label="synthetic-appliance-v1")

        second, _ = create_research_job(
            conversation=self.conversation,
            idempotency_key="research-lifecycle-cache-002",
            request_hash="8" * 64,
            source_ids=["synthetic-appliance-v1"],
            mode="FIXTURE",
        )
        owner2 = "research-worker-cache-2"
        self.assertTrue(claim_operation(second.operation_id, owner2))
        self.assertTrue(perform_research(second.id, owner2))
        cached = second.snapshots.get()
        self.assertEqual(cached.status, "CACHE_HIT")
        self.assertEqual(cached.retrieval_time, original.retrieval_time)
        self.assertEqual(cached.raw_expires_at, original.raw_expires_at)

    def test_private_cache_is_not_reused_across_conversations(self):
        owner = "research-worker-private-cache-1"
        from analysis.conversation.streaming import claim_operation
        self.assertTrue(claim_operation(self.job.operation_id, owner))
        self.assertTrue(perform_research(self.job.id, owner))
        original = self.job.snapshots.get(fixture_label="synthetic-appliance-v1")

        other = Conversation.objects.create_for_guest(self.guest)
        other.brief.confirmed = True
        other.brief.save(update_fields=["confirmed"])
        second, _ = create_research_job(
            conversation=other,
            idempotency_key="research-private-cache-002",
            request_hash="9" * 64,
            source_ids=["synthetic-appliance-v1"],
            mode="FIXTURE",
        )
        owner2 = "research-worker-private-cache-2"
        self.assertTrue(claim_operation(second.operation_id, owner2))
        self.assertTrue(perform_research(second.id, owner2))
        fresh = SourceSnapshot.objects.get(research_job=second)
        self.assertEqual(fresh.status, "EXTRACTED")
        self.assertNotEqual(fresh.id, original.id)

    def test_active_job_admission_is_guest_wide_across_conversations(self):
        other = Conversation.objects.create_for_guest(self.guest)
        other.brief.confirmed = True
        other.brief.save(update_fields=["confirmed"])
        with self.assertRaisesRegex(ValueError, "RESEARCH_LIMIT_REACHED"):
            create_research_job(
                conversation=other,
                idempotency_key="research-other-conversation-001",
                request_hash="a" * 64,
                source_ids=["synthetic-electronics-v1"],
                mode="FIXTURE",
            )

    def test_live_mode_with_no_enabled_source_returns_explicit_no_support(self):
        owner = "research-worker-finish-fixture"
        from analysis.conversation.streaming import claim_operation
        self.assertTrue(claim_operation(self.job.operation_id, owner))
        self.assertTrue(perform_research(self.job.id, owner))

        live, _ = create_research_job(
            conversation=self.conversation,
            idempotency_key="research-live-disabled-001",
            request_hash="b" * 64,
            source_ids=["www.philips.com"],
            mode="LIVE",
        )
        live_owner = "research-worker-live-disabled"
        self.assertTrue(claim_operation(live.operation_id, live_owner))
        with patch("socket.create_connection") as connect:
            self.assertTrue(perform_research(live.id, live_owner))
        live.refresh_from_db()
        self.assertEqual(live.status, "NO_SUPPORTED_SOURCES")
        self.assertEqual(live.coverage["blocked"], ["www.philips.com"])
        connect.assert_not_called()

    def test_conversation_delete_removes_job_and_blocks_late_publication(self):
        owner = "research-worker-deleted"
        job_id = self.job.id
        operation_id = self.job.operation_id
        from analysis.conversation.streaming import claim_operation
        self.assertTrue(claim_operation(operation_id, owner))
        self.conversation.delete()
        self.assertFalse(publish_research_progress(job_id, owner, stage="EXTRACT", completed=1, total=2))
        self.assertFalse(ResearchJob.objects.filter(id=job_id).exists())

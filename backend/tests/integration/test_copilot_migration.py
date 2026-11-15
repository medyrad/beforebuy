from datetime import timedelta

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.utils import timezone


class CopilotMigrationTests(TransactionTestCase):
    migrate_from = [("analysis", "0004_evaluation_accounting")]
    migrate_to = [("analysis", "0007_research_targets_and_transport_counters")]

    def test_upgrade_preserves_feature_001_rows(self):
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        old_apps = executor.loader.project_state(self.migrate_from).apps
        Guest = old_apps.get_model("analysis", "GuestContext")
        Analysis = old_apps.get_model("analysis", "Analysis")
        guest = Guest.objects.create(access_expires_at=timezone.now() + timedelta(days=90))
        analysis = Analysis.objects.create(
            guest_context=guest,
            product_label="legacy synthetic migration row",
            price_toman=1_000_000,
            budget_toman=None,
            answers={},
            expires_at=timezone.now() + timedelta(days=90),
        )

        milestone_b = [("analysis", "0006_copilot_milestone_b")]
        executor = MigrationExecutor(connection)
        executor.migrate(milestone_b)
        milestone_apps = executor.loader.project_state(milestone_b).apps
        Conversation = milestone_apps.get_model("analysis", "Conversation")
        Operation = milestone_apps.get_model("analysis", "StreamOperation")
        LegacyJob = milestone_apps.get_model("analysis", "ResearchJob")
        now = timezone.now()
        conversation = Conversation.objects.create(
            guest_context_id=guest.id, last_eligible_activity_at=now, expires_at=now + timedelta(days=90)
        )
        operation = Operation.objects.create(
            conversation=conversation, operation_kind="RESEARCH", idempotency_key="migration-research-key",
            request_hash="f" * 64, expected_brief_revision=0,
        )
        legacy_job = LegacyJob.objects.create(
            conversation=conversation, operation=operation, brief_revision=0, generation_epoch=0,
            request_hash="f" * 64, mode="FIXTURE", source_ids=["synthetic-appliance-v1"], limits={},
        )

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        new_apps = executor.loader.project_state(self.migrate_to).apps
        NewAnalysis = new_apps.get_model("analysis", "Analysis")
        Conversation = new_apps.get_model("analysis", "Conversation")
        ResearchJob = new_apps.get_model("analysis", "ResearchJob")
        SourcePolicy = new_apps.get_model("analysis", "SourcePolicy")
        self.assertEqual(NewAnalysis.objects.get(id=analysis.id).product_label, "legacy synthetic migration row")
        self.assertEqual(Conversation.objects.count(), 1)
        migrated_job = ResearchJob.objects.get(id=legacy_job.id)
        self.assertEqual(migrated_job.targets, [{"source_id": "synthetic-appliance-v1", "url": None}])
        self.assertEqual((migrated_job.wire_bytes, migrated_job.redirect_count), (0, 0))
        self.assertEqual(SourcePolicy.objects.count(), 0)

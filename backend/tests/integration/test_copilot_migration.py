from datetime import timedelta

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.utils import timezone


class CopilotMigrationTests(TransactionTestCase):
    migrate_from = [("analysis", "0004_evaluation_accounting")]
    migrate_to = [("analysis", "0006_copilot_milestone_b")]

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

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        new_apps = executor.loader.project_state(self.migrate_to).apps
        NewAnalysis = new_apps.get_model("analysis", "Analysis")
        Conversation = new_apps.get_model("analysis", "Conversation")
        ResearchJob = new_apps.get_model("analysis", "ResearchJob")
        SourcePolicy = new_apps.get_model("analysis", "SourcePolicy")
        self.assertEqual(NewAnalysis.objects.get(id=analysis.id).product_label, "legacy synthetic migration row")
        self.assertEqual(Conversation.objects.count(), 0)
        self.assertEqual(ResearchJob.objects.count(), 0)
        self.assertEqual(SourcePolicy.objects.count(), 0)

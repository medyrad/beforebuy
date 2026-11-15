from django.db import migrations, models


def copy_legacy_targets(apps, schema_editor):
    ResearchJob = apps.get_model("analysis", "ResearchJob")
    for job in ResearchJob.objects.only("id", "source_ids").iterator():
        job.targets = [{"source_id": value, "url": None} for value in job.source_ids]
        job.save(update_fields=["targets"])


class Migration(migrations.Migration):
    dependencies = [("analysis", "0006_copilot_milestone_b")]

    operations = [
        migrations.AddField(
            model_name="sourcepolicy",
            name="redirect_rules",
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name="researchjob",
            name="targets",
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name="researchjob",
            name="wire_bytes",
            field=models.PositiveBigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="researchjob",
            name="redirect_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.RunPython(copy_legacy_targets, migrations.RunPython.noop),
    ]

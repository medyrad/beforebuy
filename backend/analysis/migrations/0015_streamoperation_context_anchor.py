from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('analysis', '0014_copilot_session_accounting')]
    operations = [
        migrations.AddField(
            model_name='streamoperation', name='context_manifest',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='streamoperation', name='context_fingerprint',
            field=models.CharField(max_length=64, null=True),
        ),
    ]

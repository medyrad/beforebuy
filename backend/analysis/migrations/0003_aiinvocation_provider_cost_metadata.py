from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("analysis", "0002_ai_live_controls")]

    operations = [
        migrations.AddField(
            model_name="aiinvocation",
            name="provider_request_id",
            field=models.CharField(max_length=128, null=True),
        ),
        migrations.AddField(
            model_name="aiinvocation",
            name="provider_estimated_cost_toman",
            field=models.DecimalField(decimal_places=6, max_digits=18, null=True),
        ),
    ]

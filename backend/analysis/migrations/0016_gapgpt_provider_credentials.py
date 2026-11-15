import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("analysis", "0015_streamoperation_context_anchor")]

    operations = [
        migrations.AddField(
            model_name="copilotsettings", name="provider",
            field=models.CharField(default="openai", max_length=32),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="copilotsettings", name="provider",
            field=models.CharField(default="gapgpt", max_length=32),
        ),
        migrations.AlterField(
            model_name="copilotsettings", name="model",
            field=models.CharField(default="gapgpt-deepseek-v4.1-flash", max_length=64),
        ),
        migrations.AddField(
            model_name="streamoperation", name="credential_provider",
            field=models.CharField(editable=False, max_length=32, null=True),
        ),
        migrations.CreateModel(
            name="ProviderCredential",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("provider", models.CharField(max_length=32)),
                ("ciphertext", models.TextField()),
                ("wrapped_key", models.TextField()),
                ("revision", models.UUIDField(default=uuid.uuid4, editable=False)),
                ("state", models.CharField(default="STORED_UNVALIDATED", max_length=32)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField(db_index=True)),
                ("guest_context", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                                     related_name="provider_credentials", to="analysis.guestcontext")),
            ],
        ),
        migrations.AddConstraint(
            model_name="providercredential",
            constraint=models.UniqueConstraint(fields=("guest_context", "provider"),
                                                name="copilot_provider_credential_unique"),
        ),
        migrations.AddConstraint(
            model_name="providercredential",
            constraint=models.CheckConstraint(condition=models.Q(("provider__in", ["gapgpt"])),
                                               name="copilot_provider_credential_supported"),
        ),
    ]

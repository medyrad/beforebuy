from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('analysis', '0017_conversational_ux')]
    operations = [
        migrations.RemoveConstraint(model_name='providercredential', name='copilot_provider_credential_supported'),
        migrations.AddConstraint(model_name='providercredential', constraint=models.CheckConstraint(
            condition=models.Q(provider__in=['gapgpt', 'openrouter']), name='copilot_provider_credential_supported')),
        migrations.AddField(model_name='conversation', name='openrouter_pilot', field=models.BooleanField(default=False)),
        migrations.AddField(model_name='copilotsettings', name='openrouter_data_consent', field=models.BooleanField(default=False)),
        migrations.AddField(model_name='aiinvocation', name='provider_reported_cost_usd',
                            field=models.DecimalField(max_digits=20, decimal_places=10, null=True)),
        migrations.AddField(model_name='aiinvocation', name='hosting_provider', field=models.CharField(max_length=64, null=True)),
        migrations.CreateModel(name='OpenRouterFreePilot', fields=[
            ('id', models.CharField(primary_key=True, default='initial', max_length=16, serialize=False)),
            ('attempts', models.PositiveSmallIntegerField(default=0)), ('blocked', models.BooleanField(default=False))],
            options={'constraints': [models.CheckConstraint(condition=models.Q(id='initial', attempts__lte=10),
                                                            name='openrouter_initial_ten_attempts')]}),
    ]

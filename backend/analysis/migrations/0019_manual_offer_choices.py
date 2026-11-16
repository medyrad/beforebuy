from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('analysis', '0018_openrouter_free_pilot')]
    operations = [
        migrations.AlterField(model_name='researchjob', name='mode', field=models.CharField(max_length=16,
            choices=[('FIXTURE', 'Fixture'), ('LIVE', 'Live'), ('MANUAL', 'Manual')])),
        migrations.AlterField(model_name='offer', name='observation_kind', field=models.CharField(max_length=32,
            default='MERCHANT_PAGE_VERIFIED', choices=[('COMPARISON_OBSERVED', 'Comparison observed'),
                ('MERCHANT_PAGE_VERIFIED', 'Merchant page verified'), ('USER_REPORTED', 'User reported')])),
    ]

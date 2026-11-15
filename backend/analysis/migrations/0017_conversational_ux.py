from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('analysis', '0016_gapgpt_provider_credentials')]
    operations = [
        migrations.AddField(model_name='shoppingbrief', name='conversation_state', field=models.JSONField(default=dict)),
        migrations.AddField(model_name='message', name='reply_actions', field=models.JSONField(default=list)),
    ]

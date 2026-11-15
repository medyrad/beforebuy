from django.db import migrations, models
from django.db.models import Sum


def backfill(apps, schema_editor):
    Guest = apps.get_model('analysis', 'GuestContext')
    Invocation = apps.get_model('analysis', 'AIInvocation')
    rows = Invocation.objects.using(schema_editor.connection.alias).filter(provider='openai-copilot')
    for guest in Guest.objects.using(schema_editor.connection.alias).all().iterator():
        own = rows.filter(guest_context_id=guest.pk)
        guest.copilot_reserved_microusd = own.filter(status='reserved').aggregate(
            n=Sum('reserved_cost_microusd'))['n'] or 0
        guest.copilot_spent_microusd = own.exclude(status='reserved').aggregate(
            n=Sum('estimated_cost_microusd'))['n'] or 0
        guest.save(using=schema_editor.connection.alias,
                   update_fields=['copilot_reserved_microusd', 'copilot_spent_microusd'])


class Migration(migrations.Migration):
    dependencies = [('analysis', '0013_copilot_credential_revision')]
    operations = [
        migrations.AddField(model_name='guestcontext', name='copilot_reserved_microusd',
                            field=models.PositiveBigIntegerField(default=0)),
        migrations.AddField(model_name='guestcontext', name='copilot_spent_microusd',
                            field=models.PositiveBigIntegerField(default=0)),
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]

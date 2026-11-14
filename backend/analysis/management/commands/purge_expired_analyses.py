from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from django.db import transaction
from django.utils import timezone

from analysis.models import AIInvocation, Analysis, GuestContext


class Command(BaseCommand):
    help = "Delete expired analyses and expired guest contexts that no longer own analyses."

    def handle(self, *args, **options):
        now = timezone.now()
        with transaction.atomic():
            invocations_deleted, _ = AIInvocation.objects.filter(
                created_at__lte=now - timezone.timedelta(days=90)
            ).delete()
            analyses_deleted, _ = Analysis.objects.filter(expires_at__lte=now).delete()
            guests_deleted, _ = GuestContext.objects.filter(access_expires_at__lte=now, analyses__isnull=True).delete()
            sessions_deleted, _ = Session.objects.filter(expire_date__lte=now).delete()
        self.stdout.write(
            f"analyses_deleted={analyses_deleted} ai_invocations_deleted={invocations_deleted} "
            f"guests_deleted={guests_deleted} sessions_deleted={sessions_deleted}"
        )

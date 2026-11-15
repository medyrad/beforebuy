from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from django.db import transaction
from django.utils import timezone

from analysis.models import AIInvocation, Analysis, Conversation, GuestContext, StreamEvent, UploadedImage


class Command(BaseCommand):
    help = "Delete expired analyses and expired guest contexts that no longer own analyses."

    def handle(self, *args, **options):
        now = timezone.now()
        with transaction.atomic():
            invocations_deleted, _ = AIInvocation.objects.filter(
                created_at__lte=now - timezone.timedelta(days=90)
            ).delete()
            events_deleted, _ = StreamEvent.objects.filter(expires_at__lte=now).delete()
            uploads_deleted, _ = UploadedImage.objects.filter(expires_at__lte=now).delete()
            conversations_deleted, _ = Conversation.objects.filter(expires_at__lte=now).delete()
            analyses_deleted, _ = Analysis.objects.filter(expires_at__lte=now).delete()
            guests_deleted, _ = GuestContext.objects.filter(
                access_expires_at__lte=now, analyses__isnull=True, conversations__isnull=True
            ).delete()
            sessions_deleted, _ = Session.objects.filter(expire_date__lte=now).delete()
        self.stdout.write(
            f"analyses_deleted={analyses_deleted} conversations_deleted={conversations_deleted} "
            f"uploads_deleted={uploads_deleted} events_deleted={events_deleted} "
            f"ai_invocations_deleted={invocations_deleted} "
            f"guests_deleted={guests_deleted} sessions_deleted={sessions_deleted}"
        )

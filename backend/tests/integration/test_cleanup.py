from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.contrib.sessions.models import Session
from django.test import TestCase
from django.utils import timezone

from analysis.models import AIInvocation, GuestContext
from analysis import services
from tests.api.payloads import valid_analysis_payload


class RetentionCleanupTests(TestCase):
    def test_expired_analysis_is_denied_before_physical_purge_and_then_removed(self):
        guest = GuestContext.objects.create(access_expires_at=timezone.now() + timedelta(days=90))
        item = services.create_analysis(guest, services.normalize_input(valid_analysis_payload()))
        item.expires_at = timezone.now() - timedelta(seconds=1)
        item.save(update_fields=["expires_at"])
        self.assertFalse(services.active_analyses(guest).filter(id=item.id).exists())
        call_command("purge_expired_analyses", stdout=StringIO())
        self.assertFalse(guest.analyses.filter(id=item.id).exists())

    def test_unused_expired_guest_is_purged(self):
        guest = GuestContext.objects.create(access_expires_at=timezone.now() - timedelta(seconds=1))
        call_command("purge_expired_analyses", stdout=StringIO())
        self.assertFalse(GuestContext.objects.filter(id=guest.id).exists())

    def test_expired_django_sessions_are_purged(self):
        session = Session.objects.create(session_key="expired-session", session_data="", expire_date=timezone.now() - timedelta(seconds=1))
        call_command("purge_expired_analyses", stdout=StringIO())
        self.assertFalse(Session.objects.filter(pk=session.pk).exists())

    def test_ai_operational_metadata_older_than_ninety_days_is_purged(self):
        guest = GuestContext.objects.create(access_expires_at=timezone.now() + timedelta(days=180))
        invocation = AIInvocation.objects.create(
            guest_context=guest,
            operation_id="00000000-0000-0000-0000-000000000001",
            provider="openai",
            model="gpt-6-luna",
            prompt_version="PDA-EXPLAIN-P1",
            schema_version="PDA-EXPLAIN-v1",
            status="succeeded",
        )
        AIInvocation.objects.filter(id=invocation.id).update(created_at=timezone.now() - timedelta(days=91))
        call_command("purge_expired_analyses", stdout=StringIO())
        self.assertFalse(AIInvocation.objects.filter(id=invocation.id).exists())

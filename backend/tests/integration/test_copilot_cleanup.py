from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from analysis.models import Conversation, GuestContext, Message, StreamEvent, StreamOperation, UploadedImage


class CopilotCleanupTests(TestCase):
    def test_active_conversation_prevents_guest_cleanup(self):
        guest = GuestContext.objects.create(access_expires_at=timezone.now() - timedelta(days=1))
        conversation = Conversation.objects.create_for_guest(guest)
        call_command("purge_expired_analyses", stdout=StringIO())
        self.assertTrue(GuestContext.objects.filter(id=guest.id).exists())
        self.assertTrue(Conversation.objects.filter(id=conversation.id).exists())

    def test_expired_conversation_is_purged_before_owner(self):
        guest = GuestContext.objects.create(access_expires_at=timezone.now() - timedelta(days=1))
        conversation = Conversation.objects.create_for_guest(guest)
        Conversation.objects.filter(id=conversation.id).update(expires_at=timezone.now() - timedelta(seconds=1))
        call_command("purge_expired_analyses", stdout=StringIO())
        self.assertFalse(Conversation.objects.filter(id=conversation.id).exists())
        self.assertFalse(GuestContext.objects.filter(id=guest.id).exists())

    def test_expired_upload_and_stream_event_are_purged_without_deleting_active_owner(self):
        guest = GuestContext.objects.create(access_expires_at=timezone.now() + timedelta(days=1))
        conversation = Conversation.objects.create_for_guest(guest)
        message = Message.objects.create(conversation=conversation, role="USER", state="ACCEPTED", text="fixture")
        operation = StreamOperation.objects.create(
            conversation=conversation,
            user_message=message,
            idempotency_key="cleanup-evidence-key-001",
            request_hash="1" * 64,
            expected_brief_revision=0,
        )
        event = StreamEvent.objects.create(
            operation=operation, sequence=1, event_type="operation.started", payload={"sequence": 1}
        )
        upload = UploadedImage.objects.create(
            conversation=conversation,
            media_type="image/png",
            content=b"sanitized",
            size_bytes=9,
            width=1,
            height=1,
            sha256="2" * 64,
        )
        expired = timezone.now() - timedelta(seconds=1)
        StreamEvent.objects.filter(id=event.id).update(expires_at=expired)
        UploadedImage.objects.filter(id=upload.id).update(expires_at=expired)

        call_command("purge_expired_analyses", stdout=StringIO())

        self.assertFalse(StreamEvent.objects.filter(id=event.id).exists())
        self.assertFalse(UploadedImage.objects.filter(id=upload.id).exists())
        self.assertTrue(Conversation.objects.filter(id=conversation.id).exists())
        self.assertTrue(GuestContext.objects.filter(id=guest.id).exists())

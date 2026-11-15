from datetime import timedelta

from django.utils import timezone

from .models import GuestContext

GUEST_SESSION_KEY = "guest_context_id"
ACCESS_DAYS = 90


def get_or_create_guest(request) -> GuestContext:
    guest_id = request.session.get(GUEST_SESSION_KEY)
    guest = None
    if guest_id:
        guest = GuestContext.objects.filter(id=guest_id, access_expires_at__gt=timezone.now()).first()
    if guest is None:
        guest = GuestContext.objects.create(access_expires_at=timezone.now() + timedelta(days=ACCESS_DAYS))
        request.session[GUEST_SESSION_KEY] = str(guest.id)
        request.session.set_expiry(timedelta(days=ACCESS_DAYS))
    return guest


def extend_guest_session_for_new_analysis(request, analysis_expiry) -> None:
    guest = get_or_create_guest(request)
    if guest.access_expires_at < analysis_expiry:
        GuestContext.objects.filter(id=guest.id).update(access_expires_at=analysis_expiry)
    remaining = max(timedelta(seconds=1), analysis_expiry - timezone.now())
    request.session.set_expiry(remaining)


def extend_guest_session_for_eligible_action(request, expiry) -> None:
    """Extend access only for an accepted message or explicit brief action."""
    extend_guest_session_for_new_analysis(request, expiry)

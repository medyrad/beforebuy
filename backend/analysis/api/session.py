from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie

from analysis.guest import get_or_create_guest


@ensure_csrf_cookie
def bootstrap_session(request):
    guest = get_or_create_guest(request)
    return JsonResponse({"expires_at": guest.access_expires_at.isoformat()})

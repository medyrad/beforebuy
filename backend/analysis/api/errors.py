from django.http import Http404, JsonResponse
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.views import exception_handler


class CopilotUnavailable(NotFound):
    pass


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None
    if isinstance(exc, ValidationError):
        response.data = {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "ورودی‌ها را اصلاح کنید.",
                "field_errors": response.data,
            }
        }
    elif isinstance(exc, CopilotUnavailable):
        response.data = {
            "error": {"code": "RESOURCE_UNAVAILABLE", "message": "این منبع در دسترس نیست."}
        }
    elif isinstance(exc, (Http404, NotFound)):
        response.data = {"error": {"code": "NOT_FOUND", "message": "این تحلیل در دسترس نیست."}}
    return response


def csrf_failure(request, reason=""):
    return JsonResponse(
        {"error": {"code": "CSRF_FAILED", "message": "درخواست امن قابل تأیید نیست."}}, status=403
    )

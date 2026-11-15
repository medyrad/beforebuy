from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework.views import APIView


@method_decorator(csrf_protect, name="dispatch")
class CsrfProtectedAPIView(APIView):
    """Explicit Django CSRF enforcement, including anonymous guest requests."""


class ObjectBodyAPIView(CsrfProtectedAPIView):
    """JSON object commands; reject arrays/scalars before accessing private state."""

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE') and not isinstance(request.data, dict):
            from rest_framework.exceptions import ValidationError
            error = ValidationError({'body': 'An object is required.'})
            error.status_code = 422
            raise error

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework.views import APIView


@method_decorator(csrf_protect, name="dispatch")
class CsrfProtectedAPIView(APIView):
    """Explicit Django CSRF enforcement, including anonymous guest requests."""

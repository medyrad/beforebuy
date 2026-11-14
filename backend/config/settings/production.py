import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403


def _secret(name: str, file_name: str) -> str:
    value = os.environ.get(name, "")
    path = os.environ.get(file_name, "")
    if value and path:
        raise ImproperlyConfigured(f"Set only one of {name} or {file_name}.")
    if path:
        try:
            value = Path(path).read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise ImproperlyConfigured(f"Cannot read {file_name}.") from exc
    if not value:
        raise ImproperlyConfigured(f"{name} or {file_name} is required in production.")
    return value


def _required_list(name: str) -> list[str]:
    values = [item.strip() for item in os.environ.get(name, "").split(",") if item.strip()]
    if not values:
        raise ImproperlyConfigured(f"{name} is required in production.")
    return values


if os.environ.get("DJANGO_DEBUG", "0") != "0":
    raise ImproperlyConfigured("DJANGO_DEBUG must be 0 in production.")
if BEFOREBUY_E2E_TEST_CONTROLS:  # noqa: F405
    raise ImproperlyConfigured("BEFOREBUY_E2E_TEST_CONTROLS must be 0 in production.")

DEBUG = False
SECRET_KEY = _secret("DJANGO_SECRET_KEY", "DJANGO_SECRET_KEY_FILE")
ALLOWED_HOSTS = _required_list("DJANGO_ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = _required_list("DJANGO_CSRF_TRUSTED_ORIGINS")
if any(not origin.startswith("https://") for origin in CSRF_TRUSTED_ORIGINS):
    raise ImproperlyConfigured("DJANGO_CSRF_TRUSTED_ORIGINS must contain HTTPS origins only.")

DATABASES["default"]["PASSWORD"] = _secret("POSTGRES_PASSWORD", "POSTGRES_PASSWORD_FILE")  # noqa: F405
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_SECURE_HSTS_SECONDS", "3600"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

if BEFOREBUY_AI_MODE == "live":  # noqa: F405
    missing_live = []
    if BEFOREBUY_AI_PROVIDER != "avalai":  # noqa: F405
        missing_live.append("BEFOREBUY_AI_PROVIDER=avalai")
    if not BEFOREBUY_AVALAI_ELIGIBILITY_CONFIRMED:  # noqa: F405
        missing_live.append("BEFOREBUY_AVALAI_ELIGIBILITY_CONFIRMED=1")
    if not AVALAI_API_KEY:  # noqa: F405
        missing_live.append("AVALAI_API_KEY")
    if BEFOREBUY_AI_DAILY_BUDGET_TOMAN <= 0:  # noqa: F405
        missing_live.append("BEFOREBUY_AI_DAILY_BUDGET_TOMAN>0")
    if BEFOREBUY_AI_USD_TO_TOMAN_RATE <= 0:  # noqa: F405
        missing_live.append("BEFOREBUY_AI_USD_TO_TOMAN_RATE>0")
    if missing_live:
        raise ImproperlyConfigured("Incomplete live AI configuration: " + ", ".join(missing_live))

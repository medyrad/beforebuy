import os
from decimal import Decimal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "unsafe-development-only")
DEBUG = False
ALLOWED_HOSTS = [x for x in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",") if x]
CSRF_TRUSTED_ORIGINS = [x for x in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "http://localhost:8000").split(",") if x]
BEFOREBUY_E2E_TEST_CONTROLS = os.environ.get("BEFOREBUY_E2E_TEST_CONTROLS", "0") == "1"
BEFOREBUY_AI_MODE = os.environ.get("BEFOREBUY_AI_MODE", "mock")
BEFOREBUY_AI_SUPPORTED_REGION_CONFIRMED = os.environ.get("BEFOREBUY_AI_SUPPORTED_REGION_CONFIRMED", "0") == "1"
BEFOREBUY_AI_MODEL = os.environ.get("BEFOREBUY_AI_MODEL", "gpt-6-luna")
BEFOREBUY_AI_TIMEOUT_SECONDS = float(os.environ.get("BEFOREBUY_AI_TIMEOUT_SECONDS", "8"))
BEFOREBUY_AI_MAX_ATTEMPTS = int(os.environ.get("BEFOREBUY_AI_MAX_ATTEMPTS", "2"))
BEFOREBUY_AI_MAX_INPUT_BYTES = int(os.environ.get("BEFOREBUY_AI_MAX_INPUT_BYTES", "8192"))
BEFOREBUY_AI_MAX_OUTPUT_TOKENS = int(os.environ.get("BEFOREBUY_AI_MAX_OUTPUT_TOKENS", "512"))
BEFOREBUY_AI_PER_GUEST_DAILY_LIMIT = int(os.environ.get("BEFOREBUY_AI_PER_GUEST_DAILY_LIMIT", "10"))
BEFOREBUY_AI_DAILY_BUDGET_MICROUSD = int(
    Decimal(os.environ.get("BEFOREBUY_AI_DAILY_BUDGET_USD", "1.00")) * Decimal("1000000")
)
BEFOREBUY_AI_CIRCUIT_THRESHOLD = int(os.environ.get("BEFOREBUY_AI_CIRCUIT_THRESHOLD", "5"))
BEFOREBUY_AI_CIRCUIT_COOLDOWN_SECONDS = int(os.environ.get("BEFOREBUY_AI_CIRCUIT_COOLDOWN_SECONDS", "300"))
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "rest_framework",
    "analysis",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = []
WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "beforebuy"),
        "USER": os.environ.get("POSTGRES_USER", "beforebuy"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "beforebuy-development"),
        "HOST": os.environ.get("POSTGRES_HOST", "127.0.0.1"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": 0,
    }
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 90 * 24 * 60 * 60
SESSION_SAVE_EVERY_REQUEST = False
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = not DEBUG
CSRF_FAILURE_VIEW = "analysis.api.errors.csrf_failure"
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "EXCEPTION_HANDLER": "analysis.api.errors.api_exception_handler",
}
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}

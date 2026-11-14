from django.conf import settings
from django.test import SimpleTestCase


class ConfigurationSmokeTests(SimpleTestCase):
    def test_postgresql_database_and_nonpersistent_connections_are_explicit(self):
        database = settings.DATABASES["default"]
        self.assertEqual(database["ENGINE"], "django.db.backends.postgresql")
        self.assertEqual(database["CONN_MAX_AGE"], 0)

    def test_session_and_csrf_middleware_are_installed_in_safe_order(self):
        session = settings.MIDDLEWARE.index("django.contrib.sessions.middleware.SessionMiddleware")
        csrf = settings.MIDDLEWARE.index("django.middleware.csrf.CsrfViewMiddleware")
        self.assertLess(session, csrf)
        self.assertFalse(settings.SESSION_SAVE_EVERY_REQUEST)
        self.assertTrue(settings.SESSION_COOKIE_HTTPONLY)

    def test_logging_does_not_include_request_bodies(self):
        serialized = repr(settings.LOGGING).lower()
        self.assertNotIn("request.body", serialized)
        self.assertNotIn("django.db.backends", settings.LOGGING.get("loggers", {}))

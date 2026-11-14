import json
import os
import subprocess
import sys
from pathlib import Path

from django.test import SimpleTestCase, TestCase


ROOT = Path(__file__).resolve().parents[2]


def production_process(*, extra_env=None, expression="print('ok')"):
    env = os.environ.copy()
    env.update(
        {
            "DJANGO_SETTINGS_MODULE": "config.settings.production",
            "DJANGO_SECRET_KEY": "production-test-secret-with-enough-entropy-123456789",
            "DJANGO_ALLOWED_HOSTS": "localhost",
            "DJANGO_CSRF_TRUSTED_ORIGINS": "https://localhost:58443",
            "POSTGRES_PASSWORD": "production-test-database-password",
            "BEFOREBUY_AI_MODE": "mock",
            "BEFOREBUY_E2E_TEST_CONTROLS": "0",
        }
    )
    env.update(extra_env or {})
    return subprocess.run(
        [sys.executable, "-c", f"import django; django.setup(); {expression}"],
        cwd=ROOT / "backend",
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


class ProductionSettingsTests(SimpleTestCase):
    def test_valid_production_settings_are_hardened(self):
        result = production_process(
            expression=(
                "from django.conf import settings; import json; "
                "print(json.dumps({'debug': settings.DEBUG, 'session': settings.SESSION_COOKIE_SECURE, "
                "'csrf': settings.CSRF_COOKIE_SECURE, 'proxy': settings.SECURE_PROXY_SSL_HEADER, "
                "'ai_mode': settings.BEFOREBUY_AI_MODE}))"
            )
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        config = json.loads(result.stdout.strip())
        self.assertEqual(
            config,
            {"debug": False, "session": True, "csrf": True, "proxy": ["HTTP_X_FORWARDED_PROTO", "https"], "ai_mode": "mock"},
        )

    def test_missing_secret_fails_clearly(self):
        result = production_process(extra_env={"DJANGO_SECRET_KEY": ""})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY", result.stderr)

    def test_debug_and_test_controls_are_rejected(self):
        for variable in ("DJANGO_DEBUG", "BEFOREBUY_E2E_TEST_CONTROLS"):
            with self.subTest(variable=variable):
                result = production_process(extra_env={variable: "1"})
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(variable, result.stderr)

    def test_incomplete_live_mode_is_rejected(self):
        result = production_process(extra_env={"BEFOREBUY_AI_MODE": "live"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("live AI", result.stderr)


class HealthEndpointTests(TestCase):
    def test_liveness_does_not_require_database_query(self):
        response = self.client.get("/api/v1/health/live")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "live"})

    def test_readiness_checks_database(self):
        response = self.client.get("/api/v1/health/ready")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ready"})

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from django.test import SimpleTestCase, TestCase, override_settings


ROOT = Path(__file__).resolve().parents[2]


def production_process(*, extra_env=None, expression="print('ok')"):
    env = os.environ.copy()
    env.update(
        {
            "DJANGO_SETTINGS_MODULE": "config.settings.production",
            "DJANGO_SECRET_KEY": "production-test-secret-with-enough-entropy-123456789",
            "DJANGO_ALLOWED_HOSTS": "api.beforebuy.test",
            "DJANGO_CSRF_TRUSTED_ORIGINS": "https://api.beforebuy.test:58443",
            "BEFOREBUY_HEALTHCHECK_HOST": "api.beforebuy.test",
            "POSTGRES_PASSWORD": "production-test-database-password",
            "DJANGO_DEBUG": "0",
            "BEFOREBUY_AI_MODE": "mock",
            "BEFOREBUY_E2E_TEST_CONTROLS": "0",
            "AVALAI_API_KEY": "",
            "AVALAI_API_KEY_FILE": "",
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
                "'ai_mode': settings.BEFOREBUY_AI_MODE, 'health_host': settings.BEFOREBUY_HEALTHCHECK_HOST, "
                "'avalai_key_present': bool(settings.AVALAI_API_KEY)}))"
            )
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        config = json.loads(result.stdout.strip())
        self.assertEqual(
            config,
            {"debug": False, "session": True, "csrf": True, "proxy": ["HTTP_X_FORWARDED_PROTO", "https"],
             "ai_mode": "mock", "health_host": "api.beforebuy.test", "avalai_key_present": False},
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

    def test_healthcheck_host_must_be_explicitly_allowlisted(self):
        for extra_env in (
            {"BEFOREBUY_HEALTHCHECK_HOST": ""},
            {"BEFOREBUY_HEALTHCHECK_HOST": "other.beforebuy.test"},
            {"DJANGO_ALLOWED_HOSTS": "*", "BEFOREBUY_HEALTHCHECK_HOST": "api.beforebuy.test"},
        ):
            with self.subTest(extra_env=extra_env):
                result = production_process(extra_env=extra_env)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("BEFOREBUY_HEALTHCHECK_HOST", result.stderr)

    def test_live_file_credential_loads_factory_with_stubbed_transport(self):
        with tempfile.TemporaryDirectory() as directory:
            credential = Path(directory) / "avalai-key"
            credential.write_text("synthetic-file-key\n", encoding="utf-8")
            result = production_process(
                extra_env={
                    "BEFOREBUY_AI_MODE": "live",
                    "BEFOREBUY_AI_PROVIDER": "avalai",
                    "BEFOREBUY_AI_MODEL": "gpt-5.6-luna",
                    "BEFOREBUY_AVALAI_ELIGIBILITY_CONFIRMED": "1",
                    "BEFOREBUY_AI_DAILY_BUDGET_TOMAN": "1000",
                    "BEFOREBUY_AI_USD_TO_TOMAN_RATE": "100000",
                    "AVALAI_API_KEY": "",
                    "AVALAI_API_KEY_FILE": str(credential),
                },
                expression=(
                    "from types import SimpleNamespace; from unittest.mock import patch; "
                    "from django.conf import settings; from analysis.ai.factory import configured_explanation_generator; "
                    "sentinel=object(); request=SimpleNamespace(headers={}); guest=SimpleNamespace(id=7); "
                    "patcher=patch('analysis.ai.factory.AvalAIExplanationGenerator.from_api_key', return_value=sentinel); "
                    "mocked=patcher.start(); selected=configured_explanation_generator(request, guest); patcher.stop(); "
                    "print('loaded' if selected is sentinel and mocked.call_args.args[0] == 'synthetic-file-key' "
                    "and settings.BEFOREBUY_AI_MODEL == 'gpt-5.6-luna' else 'wrong')"
                ),
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "loaded")


class HealthEndpointTests(TestCase):
    def test_liveness_does_not_require_database_query(self):
        response = self.client.get("/api/v1/health/live")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "live"})

    def test_readiness_checks_database(self):
        response = self.client.get("/api/v1/health/ready")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ready"})

    @override_settings(ALLOWED_HOSTS=["api.beforebuy.test"])
    def test_readiness_accepts_configured_non_localhost_host(self):
        response = self.client.get(
            "/api/v1/health/ready",
            HTTP_HOST="api.beforebuy.test",
            HTTP_X_FORWARDED_PROTO="https",
        )
        self.assertEqual(response.status_code, 200)

    @override_settings(ALLOWED_HOSTS=["api.beforebuy.test"])
    def test_readiness_rejects_unconfigured_host(self):
        with self.assertLogs("django.security.DisallowedHost", level="ERROR"):
            response = self.client.get(
                "/api/v1/health/ready",
                HTTP_HOST="invalid.beforebuy.test",
                HTTP_X_FORWARDED_PROTO="https",
            )
        self.assertEqual(response.status_code, 400)

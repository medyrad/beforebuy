import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from django.test import SimpleTestCase


ROOT = Path(__file__).resolve().parents[2]


class ProductionComposeTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if shutil.which("docker") is None:
            raise unittest.SkipTest("Docker CLI is required to render production Compose")

    def render(self, *, live=False):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            paths = {}
            for name in ("django", "postgres", "certificate", "tls-key", "avalai"):
                path = runtime / name
                path.write_text("synthetic\n", encoding="utf-8")
                paths[name] = str(path)
            compose_environment = {
                "DJANGO_ALLOWED_HOSTS": "api.beforebuy.test",
                "DJANGO_CSRF_TRUSTED_ORIGINS": "https://api.beforebuy.test:58443",
                "BEFOREBUY_HEALTHCHECK_HOST": "api.beforebuy.test",
                "DJANGO_SECRET_KEY_FILE_PATH": paths["django"],
                "POSTGRES_PASSWORD_FILE_PATH": paths["postgres"],
                "TLS_CERT_PATH": paths["certificate"],
                "TLS_KEY_PATH": paths["tls-key"],
                "BEFOREBUY_AI_MODE": "live" if live else "mock",
                "BEFOREBUY_AI_PROVIDER": "avalai",
                "BEFOREBUY_AI_MODEL": "gpt-5.6-luna",
                "BEFOREBUY_AVALAI_ELIGIBILITY_CONFIRMED": "1" if live else "0",
                "BEFOREBUY_AI_TIMEOUT_SECONDS": "7",
                "BEFOREBUY_AI_MAX_ATTEMPTS": "2",
                "BEFOREBUY_AI_MAX_INPUT_BYTES": "8192",
                "BEFOREBUY_AI_MAX_OUTPUT_TOKENS": "512",
                "BEFOREBUY_AI_PER_GUEST_DAILY_LIMIT": "9",
                "BEFOREBUY_AI_DAILY_BUDGET_TOMAN": "25000" if live else "0",
                "BEFOREBUY_AI_USD_TO_TOMAN_RATE": "100000" if live else "0",
                "BEFOREBUY_AI_EXCHANGE_MARGIN_RATIO": "0.15",
                "BEFOREBUY_AI_CIRCUIT_THRESHOLD": "5",
                "BEFOREBUY_AI_CIRCUIT_COOLDOWN_SECONDS": "300",
                "AVALAI_API_KEY_FILE_PATH": paths["avalai"],
                "PHASE61_HOST_ONLY_MARKER": "must-not-enter-container",
            }
            env_file = runtime / "production.env"
            env_file.write_text(
                "\n".join(f"{key}={value}" for key, value in compose_environment.items()) + "\n",
                encoding="utf-8",
            )
            process_environment = os.environ.copy()
            for key in compose_environment:
                process_environment.pop(key, None)
            command = [
                "docker", "compose", "--env-file", str(env_file),
                "-f", str(ROOT / "compose.production.yaml"),
            ]
            if live:
                command.extend(["-f", str(ROOT / "compose.production.live.yaml")])
            command.extend(["config", "--format", "json"])
            result = subprocess.run(
                command, cwd=ROOT, env=process_environment, text=True, capture_output=True, check=False
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_postgres_data_directory_is_covered_by_only_the_named_volume(self):
        config = self.render()
        mounts = config["services"]["db"]["volumes"]
        self.assertEqual(
            mounts,
            [{"type": "volume", "source": "postgres_data", "target": "/var/lib/postgresql", "volume": {}}],
        )

    def test_mock_container_receives_complete_non_secret_configuration_without_avalai_secret(self):
        config = self.render()
        environment = config["services"]["api"]["environment"]
        self.assertEqual(environment["BEFOREBUY_AI_MODE"], "mock")
        self.assertEqual(environment["BEFOREBUY_AI_PROVIDER"], "avalai")
        self.assertEqual(environment["BEFOREBUY_AI_MODEL"], "gpt-5.6-luna")
        self.assertEqual(environment["BEFOREBUY_AI_TIMEOUT_SECONDS"], "7")
        self.assertEqual(environment["BEFOREBUY_AI_PER_GUEST_DAILY_LIMIT"], "9")
        self.assertEqual(environment["BEFOREBUY_HEALTHCHECK_HOST"], "api.beforebuy.test")
        self.assertEqual(environment["BEFOREBUY_E2E_TEST_CONTROLS"], "0")
        self.assertNotIn("AVALAI_API_KEY", environment)
        self.assertNotIn("AVALAI_API_KEY_FILE", environment)
        self.assertNotIn("PHASE61_HOST_ONLY_MARKER", environment)

    def test_live_overlay_mounts_avalai_file_secret(self):
        config = self.render(live=True)
        api = config["services"]["api"]
        self.assertEqual(api["environment"]["AVALAI_API_KEY_FILE"], "/run/secrets/avalai_api_key")
        self.assertIn({"source": "avalai_api_key", "target": "/run/secrets/avalai_api_key"}, api["secrets"])
        self.assertIn("avalai_api_key", config["secrets"])

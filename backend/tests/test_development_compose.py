import json
import shutil
import subprocess
import unittest
from pathlib import Path

from django.test import SimpleTestCase


ROOT = Path(__file__).resolve().parents[2]


class DevelopmentComposeTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if shutil.which("docker") is None:
            raise unittest.SkipTest("Docker CLI is required to render development Compose")

    def render(self):
        result = subprocess.run(
            ["docker", "compose", "config", "--format", "json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_postgres_18_data_is_in_the_new_named_parent_volume(self):
        config = self.render()

        self.assertEqual(
            config["services"]["db"]["volumes"],
            [
                {
                    "type": "volume",
                    "source": "beforebuy_pgdata_v18",
                    "target": "/var/lib/postgresql",
                    "volume": {},
                }
            ],
        )
        self.assertEqual(
            config["volumes"]["beforebuy_pgdata_v18"]["name"],
            "beforebuy_beforebuy_pgdata_v18",
        )

    def test_database_and_api_ports_publish_only_on_loopback(self):
        config = self.render()

        self.assertEqual(
            config["services"]["db"]["ports"],
            [
                {
                    "mode": "ingress",
                    "host_ip": "127.0.0.1",
                    "target": 5432,
                    "published": "55439",
                    "protocol": "tcp",
                }
            ],
        )
        self.assertEqual(
            config["services"]["api"]["ports"],
            [
                {
                    "mode": "ingress",
                    "host_ip": "127.0.0.1",
                    "target": 8000,
                    "published": "58000",
                    "protocol": "tcp",
                }
            ],
        )
        self.assertEqual(config["services"]["web"]["ports"][0]["host_ip"], "127.0.0.1")
        self.assertEqual(config["services"]["web"]["ports"][0]["published"], "58080")

    def test_offline_web_uses_development_proxy_and_api_has_thread_capacity(self):
        config = self.render()
        self.assertEqual(config["services"]["web"]["build"]["args"]["NGINX_CONFIG"], "deploy/web.dev.conf")
        command = config["services"]["api"]["command"]
        self.assertIn("gthread", command)
        self.assertIn("4", command)

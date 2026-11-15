import gzip
import http.client
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest import TestCase

from analysis.research.fetch import (
    FetchBudget,
    FetchError,
    FetchPolicy,
    SafeFetcher,
    validate_public_address,
)


class FakeResponse:
    def __init__(self, body=b"ok", *, status=200, headers=None):
        self.status = status
        self._body = body
        self._offset = 0
        self.headers = {key.lower(): value for key, value in (headers or {}).items()}

    def getheader(self, name, default=None):
        return self.headers.get(name.lower(), default)

    def read(self, size=-1):
        if size < 0:
            size = len(self._body)
        part = self._body[self._offset:self._offset + size]
        self._offset += len(part)
        return part


class FakeConnection:
    def __init__(self, response):
        self.response = response
        self.request_data = None

    def request(self, method, path, headers=None):
        self.request_data = (method, path, headers)

    def getresponse(self):
        return self.response

    def close(self):
        pass


class SafeFetchTests(TestCase):
    def policy(self, **changes):
        values = dict(
            hostname="products.example",
            allowed_path_prefixes=("/p/",),
            redirect_hostnames=(),
            allowed_ports=(443,),
            max_redirects=2,
            max_decoded_bytes=32,
            request_timeout_seconds=20,
        )
        values.update(changes)
        return FetchPolicy(**values)

    def test_rejects_credentials_bad_scheme_port_private_and_ipv6_reserved(self):
        for url in (
            "file:///etc/passwd",
            "https://user:secret@products.example/p/1",
            "https://products.example:444/p/1",
        ):
            with self.subTest(url=url), self.assertRaises(FetchError):
                SafeFetcher(resolver=lambda *_: ["93.184.216.34"]).fetch(url, self.policy(), FetchBudget())
        for address in ("127.0.0.1", "10.0.0.1", "169.254.169.254", "::1", "fe80::1", "2001:db8::1"):
            with self.subTest(address=address), self.assertRaises(FetchError):
                validate_public_address(address)

    def test_connection_is_pinned_to_validated_address_while_host_is_preserved(self):
        connected = []
        connection = FakeConnection(FakeResponse(headers={"Content-Type": "text/html; charset=utf-8"}))

        def connector(scheme, hostname, port, approved_ip, timeout):
            connected.append((scheme, hostname, port, approved_ip, timeout))
            return connection

        fetcher = SafeFetcher(resolver=lambda host, port: ["93.184.216.34"], connector=connector)
        result = fetcher.fetch("https://products.example/p/item", self.policy(), FetchBudget())
        self.assertEqual(connected, [("https", "products.example", 443, "93.184.216.34", 20)])
        self.assertEqual(connection.request_data[1], "/p/item")
        self.assertEqual(connection.request_data[2]["Host"], "products.example")
        self.assertEqual(result.body, b"ok")

    def test_controlled_local_http_fixture_uses_only_test_connector_boundary(self):
        observed = {}

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                observed["host"] = self.headers["Host"]
                observed["path"] = self.path
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"fixture")

            def log_message(self, *_args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            port = server.server_address[1]

            def test_connector(_scheme, _hostname, _port, approved_ip, timeout):
                self.assertEqual(approved_ip, "93.184.216.34")
                return http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)

            result = SafeFetcher(
                resolver=lambda *_: ["93.184.216.34"], connector=test_connector
            ).fetch(
                f"http://products.example:{port}/p/local",
                self.policy(allowed_ports=(port,)),
                FetchBudget(),
            )
            self.assertEqual(result.body, b"fixture")
            self.assertEqual(observed, {"host": f"products.example:{port}", "path": "/p/local"})
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_mixed_public_private_dns_answer_is_rejected_before_connect(self):
        connected = []
        fetcher = SafeFetcher(
            resolver=lambda *_: ["93.184.216.34", "127.0.0.1"],
            connector=lambda *args: connected.append(args),
        )
        with self.assertRaisesRegex(FetchError, "NON_PUBLIC_ADDRESS"):
            fetcher.fetch("https://products.example/p/1", self.policy(), FetchBudget())
        self.assertEqual(connected, [])

    def test_redirect_is_revalidated_and_unapproved_destination_is_blocked(self):
        first = FakeConnection(FakeResponse(status=302, headers={"Location": "https://other.example/p/2"}))
        calls = []

        def connector(*args):
            calls.append(args)
            return first

        with self.assertRaisesRegex(FetchError, "REDIRECT_NOT_ALLOWED"):
            SafeFetcher(resolver=lambda *_: ["93.184.216.34"], connector=connector).fetch(
                "https://products.example/p/1", self.policy(), FetchBudget()
            )
        self.assertEqual(len(calls), 1)

    def test_decoded_gzip_limit_and_request_cap_are_enforced(self):
        body = gzip.compress(b"x" * 64)
        response = FakeResponse(body, headers={"Content-Type": "text/html", "Content-Encoding": "gzip"})
        fetcher = SafeFetcher(
            resolver=lambda *_: ["93.184.216.34"],
            connector=lambda *args: FakeConnection(response),
        )
        with self.assertRaisesRegex(FetchError, "RESPONSE_TOO_LARGE"):
            fetcher.fetch("https://products.example/p/1", self.policy(), FetchBudget(max_requests=1))
        with self.assertRaisesRegex(FetchError, "REQUEST_BUDGET_EXHAUSTED"):
            fetcher.fetch("https://products.example/p/1", self.policy(), FetchBudget(max_requests=0))

    def test_policy_disabled_causes_zero_dns_or_connection_work(self):
        called = []
        policy = self.policy(enabled=False)
        with self.assertRaisesRegex(FetchError, "SOURCE_DISABLED"):
            SafeFetcher(resolver=lambda *_: called.append("dns")).fetch(
                "https://products.example/p/1", policy, FetchBudget()
            )
        self.assertEqual(called, [])

    def test_body_read_stops_at_total_deadline(self):
        class SlowResponse(FakeResponse):
            def read(self, size=-1):
                time.sleep(0.015)
                return super().read(1)

        response = SlowResponse(b"slow", headers={"Content-Type": "text/plain"})
        fetcher = SafeFetcher(
            resolver=lambda *_: ["93.184.216.34"],
            connector=lambda *args: FakeConnection(response),
        )
        budget = FetchBudget(deadline_monotonic=time.monotonic() + 0.02)
        with self.assertRaisesRegex(FetchError, "JOB_DEADLINE_EXCEEDED"):
            fetcher.fetch("https://products.example/p/slow", self.policy(), budget)

    def test_domain_pacing_cannot_extend_connection_past_job_deadline(self):
        connections = []
        response = FakeResponse(headers={"Content-Type": "text/plain"})
        fetcher = SafeFetcher(
            resolver=lambda *_: ["93.184.216.34"],
            connector=lambda *args: connections.append(args) or FakeConnection(response),
        )
        policy = self.policy(min_interval_seconds=0.05)
        fetcher.fetch("https://products.example/p/first", policy, FetchBudget())
        with self.assertRaisesRegex(FetchError, "JOB_DEADLINE_EXCEEDED"):
            fetcher.fetch(
                "https://products.example/p/second",
                policy,
                FetchBudget(deadline_monotonic=time.monotonic() + 0.01),
            )
        self.assertEqual(len(connections), 1)

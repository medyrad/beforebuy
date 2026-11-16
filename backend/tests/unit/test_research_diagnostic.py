import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
from unittest import TestCase
from unittest.mock import patch, MagicMock

spec = importlib.util.spec_from_file_location('research_diagnostic', Path(__file__).resolve().parents[3] / 'scripts/diagnose-research.py')
diagnostic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diagnostic)


class DiagnosticTests(TestCase):
    def invoke(self, *args):
        output = io.StringIO()
        with patch.object(sys, 'argv', ['diagnose-research.py', *args]), contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
            try: code = diagnostic.main()
            except SystemExit as exc: code = exc.code
        return code, output.getvalue()

    def test_reviewed_target_dns_failure_is_reported_without_connecting(self):
        with patch.object(diagnostic.SafeFetcher, '_resolve', side_effect=diagnostic.FetchError('DNS_ERROR')):
            code, output = self.invoke('--layer', 'direct', '--target', 'takkalaban-na230')
        self.assertEqual(code, 1)
        report = json.loads(output)
        self.assertEqual(report['url'], 'https://takkalaban.com/product/philips-na230/')
        self.assertEqual(report['failure_stage'], 'DNS')
        self.assertEqual(report['attempts'], 0)
        self.assertEqual(report['request_budget_used'], 1)

    def test_arbitrary_target_is_rejected_before_network(self):
        code, output = self.invoke('--layer', 'direct', '--target', 'https://127.0.0.1/')
        self.assertEqual(code, 2)
        self.assertEqual(output, '')

    def test_direct_tcp_and_tls_failures_are_distinct_and_counted(self):
        for stage in ('TCP', 'TLS'):
            raw = MagicMock()
            context = MagicMock()
            if stage == 'TCP': raw.connect.side_effect = TimeoutError()
            else: context.wrap_socket.side_effect = diagnostic.ssl.SSLCertVerificationError()
            with patch.object(diagnostic.SafeFetcher, '_resolve', return_value=['93.184.216.34']), \
                 patch.object(diagnostic.socket, 'socket', return_value=raw), \
                 patch.object(diagnostic.ssl, 'create_default_context', return_value=context):
                report = diagnostic.probe('takkalaban-na230', 'direct')
            self.assertEqual(report['failure_stage'], stage)
            self.assertEqual(report['request_budget_used'], 1)
            self.assertEqual(report['attempts'], 1)
            self.assertNotIn('http_status', report)

    def test_safe_fallback_http_rejection_reports_headers_not_previous_tcp_failure(self):
        raw = MagicMock()
        raw.makefile.return_value = io.BytesIO(b'HTTP/1.1 490 Rejected\r\nContent-Length: 0\r\n\r\n')
        context = MagicMock()
        context.wrap_socket.return_value = raw
        with patch.object(diagnostic.SafeFetcher, '_resolve', return_value=['93.184.216.34', '1.1.1.1']), \
             patch.object(diagnostic.transport, '_connect_numeric', side_effect=[TimeoutError(), raw]), \
             patch.object(diagnostic.ssl, 'create_default_context', return_value=context):
            report = diagnostic.probe('takkalaban-na230', 'safe', 2)
        self.assertEqual(report['http_status'], 490)
        self.assertEqual(report['failure'], 'HTTP_STATUS')
        self.assertEqual(report['failure_stage'], 'HTTP_HEADERS')
        self.assertEqual(report['request_budget_used'], 2)
        self.assertEqual(report['attempts'], 2)
        self.assertNotIn('EXTRACTION', [t['stage'] for t in report['timings']])

    def test_safe_nested_connection_failure_keeps_deepest_stage(self):
        for stage in ('TCP', 'TLS'):
            raw = MagicMock()
            context = MagicMock()
            context.wrap_socket.side_effect = diagnostic.ssl.SSLCertVerificationError()
            with patch.object(diagnostic.SafeFetcher, '_resolve', return_value=['93.184.216.34']), \
                 patch.object(diagnostic.transport, '_connect_numeric', side_effect=TimeoutError() if stage == 'TCP' else None, return_value=raw), \
                 patch.object(diagnostic.ssl, 'create_default_context', return_value=context):
                report = diagnostic.probe('takkalaban-na230', 'safe')
            self.assertEqual(report['failure_stage'], stage)
            self.assertEqual(report['attempts'], 1)

    def test_both_layers_use_matching_headers_and_extract_without_publishing(self):
        body = b'<script type="application/ld+json">{"@type":"Product","name":"Synthetic appliance","sku":"TEST-ONLY","offers":{"@type":"Offer","price":"100000","priceCurrency":"IRR","availability":"https://schema.org/InStock"}}</script>'
        requests = []
        for layer in ('direct', 'safe'):
            raw = MagicMock()
            raw.makefile.return_value = io.BytesIO(b'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: ' + str(len(body)).encode() + b'\r\n\r\n' + body)
            context = MagicMock(); context.wrap_socket.return_value = raw
            with patch.object(diagnostic.SafeFetcher, '_resolve', return_value=['93.184.216.34']), \
                 patch.object(diagnostic.socket, 'socket', return_value=raw), \
                 patch.object(diagnostic.ssl, 'create_default_context', return_value=context):
                report = diagnostic.probe('takkalaban-na230', layer)
            self.assertNotIn('failure', report, report)
            self.assertEqual(report['stage'], 'EXTRACTED')
            self.assertEqual(report['offers'], 1)
            self.assertEqual(report['publication'], 'NOT_RUN')
            self.assertEqual(report['request_budget_used'], 1)
            self.assertEqual([t['stage'] for t in report['timings']], ['DNS', 'TCP', 'TLS', 'HTTP_SEND', 'HTTP_HEADERS', 'BODY', 'EXTRACTION'])
            requests.append(b''.join(call.args[0] for call in raw.sendall.call_args_list))
        self.assertEqual(requests[0], requests[1])
        self.assertIn(b'Cookie: \r\n', requests[0])

    def test_private_dns_is_rejected_and_proxy_values_are_not_disclosed(self):
        with patch.object(diagnostic.SafeFetcher, '_resolve', return_value=['127.0.0.1']), \
             patch.dict(diagnostic.os.environ, {'HTTPS_PROXY': 'https://secret-user:secret-pass@proxy.invalid'}):
            report = diagnostic.probe('takkalaban-na230', 'direct')
        self.assertEqual(report['failure'], 'NON_PUBLIC_ADDRESS')
        self.assertEqual(report['attempts'], 0)
        self.assertTrue(report['proxy_env_present'])
        self.assertNotIn('secret-pass', json.dumps(report))

    def test_one_unit_cap_prevents_connection_fallback(self):
        with patch.object(diagnostic.SafeFetcher, '_resolve', return_value=['93.184.216.34', '1.1.1.1']), \
             patch.object(diagnostic.transport, '_connect_numeric', side_effect=TimeoutError()):
            report = diagnostic.probe('takkalaban-na230', 'safe', 1)
        self.assertEqual(report['failure'], 'REQUEST_BUDGET_EXHAUSTED')
        self.assertEqual(report['attempts'], 1)
        self.assertEqual(report['request_budget_used'], 1)

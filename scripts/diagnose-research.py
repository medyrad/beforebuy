"""One reviewed URL, fresh proxy-free traffic; no credentials or retained bodies.

Run from root: python3 scripts/diagnose-research.py --target takkalaban-na230 --layer direct
Standard library only; no Django, database, key or retained bodies. Default one
budget unit; safe may explicitly reserve up to four including redirects/fallback.
Run sequentially and include every invocation in the checkpoint ledger.
"""
import argparse
import datetime
import hashlib
import http.client
import json
import os
from pathlib import Path
import socket
import ssl
import sys
import time
import urllib.request
from urllib.parse import urlsplit
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from analysis.research.extractors import ExtractionError, extract_product_document
from analysis.research.fetch import (
    FetchBudget, FetchError, FetchPolicy, SafeFetcher, default_connector, validate_public_address,
)
from analysis.research import fetch as transport

URL = 'https://torob.com/p/bb037069-fba8-4964-a758-6adcec22898f/q60d/'
TARGETS = {
    'torob-q60d': (URL, 'COMPARISON'),
    'takkalaban-na230': ('https://takkalaban.com/product/philips-na230/', 'MERCHANT'),
    'bkalaa-na230': ('https://bkalaa.com/product/na230/', 'MERCHANT'),
}


def measured(report, stage, action, *args, **kwargs):
    report['stage'] = stage
    report.pop('failure_stage', None)
    started = time.monotonic()
    event = {'stage': stage, 'outcome': 'OK'}
    try:
        return action(*args, **kwargs)
    except BaseException:
        event['outcome'] = 'FAILED'
        report['failure_stage'] = stage
        raise
    finally:
        event['seconds'] = round(time.monotonic() - started, 4)
        report['timings'].append(event)


def probe(target, layer, max_attempts=1):
    url, role = TARGETS[target]
    parts = urlsplit(url)
    host = parts.hostname
    started = time.monotonic()
    report = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'url': url,
              'layer': layer, 'network_mode': 'DIRECT_NO_PROXY', 'timings': [],
              'proxy_env_present': any(os.environ.get(k) for k in (
                  'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy')),
              'system_proxy_types': sorted(urllib.request.getproxies()), 'attempts': 0,
              'publication': 'NOT_RUN'}
    deadline = started + 20
    policy = FetchPolicy(hostname=host, allowed_path_prefixes=(parts.path,),
                         redirect_hostnames=('www.' + host,) if host != 'torob.com' else (),
                         max_redirects=1, request_timeout_seconds=10)
    budget = FetchBudget(max_requests=max_attempts, deadline_monotonic=deadline)
    fetcher = SafeFetcher()
    try:
        if layer == 'direct':
            budget.consume_request(host)
            addresses = measured(report, 'DNS', fetcher._resolve, host, 443, deadline)
            addresses = [validate_public_address(a) for a in addresses]
            if not addresses: raise FetchError('DNS_EMPTY')
            report['addresses'] = addresses
            address = addresses[0]
            report['approved_ip'] = address
            raw = socket.socket(socket.AF_INET6 if ':' in address else socket.AF_INET, socket.SOCK_STREAM)
            try:
                raw.settimeout(min(10, fetcher._remaining(deadline)))
                report['attempts'] += 1
                measured(report, 'TCP', raw.connect, (address, 443))
                raw.settimeout(min(10, fetcher._remaining(deadline)))
                raw = measured(report, 'TLS', ssl.create_default_context().wrap_socket, raw, server_hostname=host)
                report['tls'] = 'verified'
                path = parts.path + ('?' + parts.query if parts.query else '')
                # Match SafeFetcher request headers; no browser UA, cookies or auth.
                request = (f'GET {path} HTTP/1.1\r\nHost: {host}\r\n'
                           'User-Agent: BeforebuyResearch/0.1 (+https://github.com/medyrad/beforebuy)\r\n'
                           'Accept: text/html,application/json,application/ld+json,text/plain\r\n'
                           'Accept-Encoding: gzip\r\nCookie: \r\n\r\n')
                raw.settimeout(min(10, fetcher._remaining(deadline)))
                measured(report, 'HTTP_SEND', raw.sendall, request.encode('ascii'))
                response = http.client.HTTPResponse(raw)
                measured(report, 'HTTP_HEADERS', response.begin)
                report['http_status'] = response.status
                if not 200 <= response.status < 300:
                    report['failure_stage'] = 'HTTP_HEADERS'
                    raise FetchError('HTTP_STATUS')  # Direct probe never follows/retries a rejection/redirect.
                content_type = response.getheader('Content-Type', '').split(';', 1)[0].strip().lower()
                if content_type not in transport.ALLOWED_MIME_TYPES: raise FetchError('UNSUPPORTED_MIME')
                body, _ = measured(report, 'BODY', fetcher._read_bounded, response,
                    policy.max_decoded_bytes, policy.max_wire_bytes, budget, deadline)
            finally:
                raw.close()
        else:
            original_resolve = fetcher._resolve
            fetcher._resolve = lambda *a: measured(report, 'DNS', original_resolve, *a)
            original_read = fetcher._read_bounded
            fetcher._read_bounded = lambda *a: measured(report, 'BODY', original_read, *a)
            def connector(*values):
                report['attempts'] += 1
                report['approved_ip'] = values[3]
                connection = default_connector(*values)
                wrap = connection._context.wrap_socket
                def tls(*a, **kw):
                    result = measured(report, 'TLS', wrap, *a, **kw)
                    report['tls'] = 'verified'
                    return result
                connection._context.wrap_socket = tls
                original = connection.getresponse
                def response():
                    result = measured(report, 'HTTP_HEADERS', original)
                    report['http_status'] = result.status
                    return result
                connection.getresponse = response
                request = connection.request
                connection.request = lambda *a, **kw: measured(report, 'HTTP_SEND', request, *a, **kw)
                return connection
            fetcher.connector = connector
            numeric = transport._connect_numeric
            # Observe the real numeric socket connect, without replacing validation/TLS behavior.
            with patch.object(transport, '_connect_numeric', lambda *a: measured(report, 'TCP', numeric, *a)):
                result = fetcher.fetch(url, policy, budget)
            body, url = result.body, result.url
        report.update(body_bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
        extracted = measured(report, 'EXTRACTION', extract_product_document, body,
                             source_url=url, source_role=role, retrieved_at=report['utc'])
        report.update(stage='EXTRACTED', offers=len(extracted.offers))
    except (FetchError, ExtractionError, OSError, http.client.HTTPException) as exc:
        report['failure'] = getattr(exc, 'code', type(exc).__name__)
        report.setdefault('failure_stage', report.get('stage', 'POLICY'))
    report.update(request_budget_used=budget.request_count, redirects=budget.redirect_count,
                  total_seconds=round(time.monotonic() - started, 4))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--layer', choices=['direct', 'safe'], required=True)
    parser.add_argument('--target', choices=sorted(TARGETS), default='torob-q60d')
    parser.add_argument('--max-attempts', type=int, choices=range(1, 5), default=1)
    args = parser.parse_args()
    report = probe(args.target, args.layer, args.max_attempts)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 1 if 'failure' in report else 0


if __name__ == '__main__':
    raise SystemExit(main())

"""One reviewed URL, fresh proxy-free traffic; no credentials or retained bodies.

Run from root: uv run python scripts/diagnose-research.py --layer safe
This probe does not enable policies or publish evidence. Each invocation reserves
at most four outbound attempts; include its reported count in the phase ledger.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import socket
import ssl
import sys
import time
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from analysis.research.extractors import ExtractionError, extract_product_document
from analysis.research.fetch import (
    FetchBudget, FetchError, FetchPolicy, SafeFetcher, default_connector, validate_public_address,
)

URL = 'https://torob.com/p/bb037069-fba8-4964-a758-6adcec22898f/q60d/'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--layer', choices=['direct', 'safe'], required=True)
    args = parser.parse_args()
    report = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'url': URL,
              'layer': args.layer, 'proxy_env_present': any(os.environ.get(k) for k in (
                  'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy')),
              'system_proxy_types': sorted(urllib.request.getproxies()), 'attempts': 0}
    deadline = time.monotonic() + 20
    policy = FetchPolicy(hostname='torob.com', allowed_path_prefixes=('/p/',),
                         redirect_hostnames=(), max_redirects=1, request_timeout_seconds=10)
    budget = FetchBudget(max_requests=4, deadline_monotonic=deadline)
    fetcher = SafeFetcher()
    try:
        if args.layer == 'direct':
            report['stage'] = 'DNS'
            addresses = [validate_public_address(a) for a in fetcher._resolve('torob.com', 443, deadline)]
            report['addresses'] = addresses
            address = addresses[0]
            family = socket.AF_INET6 if ':' in address else socket.AF_INET
            report['address_family'] = family.name
            raw = socket.socket(family, socket.SOCK_STREAM)
            try:
                raw.settimeout(min(5, fetcher._remaining(deadline)))
                report['stage'] = 'TCP'; report['attempts'] += 1
                raw.connect((address, 443)); report['tcp'] = 'OK'
                report['stage'] = 'TLS'
                raw.settimeout(min(5, fetcher._remaining(deadline)))
                raw = ssl.create_default_context().wrap_socket(raw, server_hostname='torob.com')
                report['tls'] = 'verified'; report['stage'] = 'HTTP'
                raw.sendall(('GET /p/bb037069-fba8-4964-a758-6adcec22898f/q60d/ HTTP/1.1\r\n'
                             'Host: torob.com\r\nUser-Agent: BeforebuyResearch/0.1\r\n'
                             'Connection: close\r\n\r\n').encode())
                report['http_status_line'] = raw.recv(1024).split(b'\r\n')[0].decode('ascii', 'replace')
                report['body'] = 'not retained; status probe only'
            finally:
                raw.close()
        else:
            def connector(*values):
                report['attempts'] += 1
                report['approved_ip'] = values[3]
                connection = default_connector(*values)
                original = connection.getresponse
                def response():
                    result = original()
                    report['http_status'] = result.status
                    return result
                connection.getresponse = response
                return connection
            fetcher.connector = connector
            report['stage'] = 'FETCH'
            result = fetcher.fetch(URL, policy, budget)
            report.update(body_bytes=len(result.body), sha256=hashlib.sha256(result.body).hexdigest())
            report['stage'] = 'EXTRACTION'
            extracted = extract_product_document(result.body, source_url=result.url,
                                                 source_role='COMPARISON', retrieved_at=report['utc'])
            report.update(stage='EXTRACTED', offers=len(extracted.offers), publication='NOT_RUN')
    except (FetchError, ExtractionError, OSError) as exc:
        report['failure'] = getattr(exc, 'code', type(exc).__name__)
        report['publication'] = 'NOT_RUN'
    report['request_budget_used'] = budget.request_count
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 1 if 'failure' in report else 0


if __name__ == '__main__':
    raise SystemExit(main())

"""Opt-in local API pilot; preflight must extract before two fresh conversations.

Run inside the API container so preflight uses the application network:
docker compose exec -T api python scripts/pilot-reviewed-offer.py
Requires explicit LIVE configuration and reviewed policies already enabled.
Reserves at most 16 outbound attempts (4 preflight + 6 per API job); do not
run unless the phase has that allowance remaining. No automatic retry.
"""
import http.cookiejar
import json
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
import uuid


def main():
    preflight = subprocess.run(
        [sys.executable, str(Path(__file__).with_name('diagnose-research.py')), '--layer', 'safe'],
        capture_output=True, text=True, timeout=30)
    evidence = json.loads(preflight.stdout)
    print(json.dumps({'preflight': evidence}), flush=True)
    if preflight.returncode or evidence.get('stage') != 'EXTRACTED' or not evidence.get('offers'):
        print('PREFLIGHT_FAILED: no API job submitted', flush=True)
        return 1
    base = 'http://127.0.0.1:8000'
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPCookieProcessor(jar))

    def call(path, data=None, method=None):
        headers = {'Content-Type': 'application/json', 'Origin': base}
        for cookie in jar:
            if cookie.name == 'csrftoken':
                headers['X-CSRFToken'] = cookie.value
        if path.endswith('/research'):
            headers['Idempotency-Key'] = str(uuid.uuid4())
        request = urllib.request.Request(base + path, headers=headers, method=method,
                                         data=None if data is None else json.dumps(data).encode())
        with opener.open(request, timeout=30) as response:
            return json.load(response)

    call('/api/v1/session')
    for run in (1, 2):
        # Cache is conversation-scoped: each new conversation forces fresh research.
        conversation = call('/api/v1/conversations', {})
        path = '/api/v1/conversations/' + conversation['id']
        call(path + '/brief', {'expected_revision': 0, 'changes': {
            'recipient_context': 'SELF', 'category': 'لوازم الکترونیک',
            'budget_toman': 120000000, 'use_cases': ['پایلوت تلویزیون Q60D']}}, 'PATCH')
        call(path + '/brief/confirm', {'expected_revision': 1})
        response = call(path + '/research', {'expected_brief_revision': 1,
                        'targets': [{'source_id': 'torob.com', 'url': evidence['url']}]})
        job_id = response['job']['id']
        deadline = time.monotonic() + 70
        while time.monotonic() < deadline:
            job = call('/api/v1/research-jobs/' + job_id)
            if job['status'] not in ('PENDING', 'RUNNING'):
                break
            time.sleep(1)
        offers = job['offers']
        fresh = all(s['status'] == 'EXTRACTED' and not s['fixture_label'] for s in job['snapshots'])
        by_variant = {}
        for offer in offers:
            by_variant.setdefault(offer['variant_id'], set()).add(offer['seller'])
        comparable = max((len(sellers - {None, ''}) for sellers in by_variant.values()), default=0)
        print(json.dumps({'run': run, 'job_id': job_id, 'status': job['status'], 'mode': job['mode'],
                          'fresh': fresh, 'request_count': job['request_count'],
                          'comparable_merchants': comparable, 'offers': offers}, ensure_ascii=False), flush=True)
        if job['mode'] != 'LIVE' or job['status'] != 'SUCCESS' or not fresh or not offers:
            return 1
        if comparable < 3:
            print('T066 merchant target unmet; repeat may establish extraction only', flush=True)
    print('API pilot finished; inspect PostgreSQL and browser evidence before closing T066', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

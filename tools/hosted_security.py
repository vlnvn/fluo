"""Additional bounded HTTPS negative tests; expiry modifies only this test's guest."""
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

import httpx
from psycopg import connect

from backend.auth import token_digest
from backend.postgres_store import connection_options
from tools.provision_postgres import read_env

ROOT = Path(__file__).resolve().parents[1]


def main():
    base = os.environ['FLUO_BASE_URL']
    assert urlparse(base).scheme == 'https' and urlparse(base).hostname.endswith('.vercel.app')
    token = read_env(ROOT / '.local/fluo-development.env')['VERCEL_OIDC_TOKEN']
    headers = {'x-vercel-trusted-oidc-idp-token': token}
    checks = []

    def check(name, actual, expected):
        if actual != expected:
            raise RuntimeError(f'{name}: expected {expected}, received {actual}')
        checks.append({'name': name, 'pass': True})

    with httpx.Client(base_url=base, headers=headers, timeout=30) as client:
        check('forged identity headers', client.get('/api/v1/health', headers={
            'X-Fluo-Guest': 'admin', 'X-User-Id': 'admin', 'X-Forwarded-For': '127.0.0.1'}).status_code, 401)
        check('forged cookie', client.get('/api/v1/health', headers={
            'Cookie': '__Host-fluo_guest=' + 'a' * 43}).status_code, 401)
        for path in ['/assets/%2e%2e/%2e%2e/.env', '/assets/%2e%2e/backend/app.py',
                     '/api/v1/../../data/original/fluo_sensor_stream.csv.gz']:
            check('traversal denied ' + path, client.get(path).status_code in (400, 403, 404), True)
        entered = client.post('/api/v1/auth/guest', headers={'X-Fluo-Intent': 'guest'}, json={})
        check('test guest entry', entered.status_code, 200)
        csrf = entered.json()['csrf_token']
        client.headers['X-CSRF-Token'] = csrf
        check('authenticated long query bounded', client.get('/api/v1/health?' + 'x' * 9000).status_code, 414)
        state = client.post('/api/v1/sessions', json={}).json()
        root = '/api/v1/sessions/' + state['session_id']
        event = state['events'][0]['id']
        with ThreadPoolExecutor(max_workers=2) as executor:
            statuses = sorted(executor.map(lambda _: client.put(root + '/events/' + event + '/review',
                json={'revision': 0, 'checked_steps': [], 'note': '<script>window.xss=true</script>'}).status_code, range(2)))
        check('concurrent revision conflict', statuses, [200, 409])
        report = client.get(root + '/events/' + event + '/print')
        check('report escapes operator HTML', '<script>window.xss=true</script>' in report.text, False)
        check('escaped operator note retained', '&lt;script&gt;window.xss=true&lt;/script&gt;' in report.text, True)
        check('guest session quota', client.post('/api/v1/sessions', json={}).status_code, 201)
        check('third session denied', client.post('/api/v1/sessions', json={}).status_code, 429)
        dsn = json.loads((ROOT / '.local/fluo-app-private.json').read_text())['dsn']
        digest = token_digest(client.cookies.get('__Host-fluo_guest'))
        with connect(dsn, **connection_options(dsn)) as connection:
            changed = connection.execute('UPDATE fluo_guests SET expires=%s WHERE digest=%s',
                                         (time.time() - 1, digest)).rowcount
            check('expire only own disposable guest', changed, 1)
        check('expired credential denied', client.get(root).status_code, 401)
        check('expired PDF denied', client.get(root + '/events/' + event + '/report.pdf').status_code, 401)
    evidence = {'status': 'PASS', 'url': base, 'date': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'scope': 'Two concurrent requests, no destructive load; expiry limited to own test guest.', 'checks': checks}
    (ROOT / 'docs/implementation/qa/vercel/hosted-security.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
    print(json.dumps({'status': 'PASS', 'checks': len(checks)}))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # HTTP exceptions can include headers or request bodies. Keep details private.
        print(json.dumps({'status': 'FAIL', 'error_type': type(error).__name__,
                          'message': str(error).split('\n')[0] if isinstance(error, RuntimeError) else 'Inspect privately'}))
        raise SystemExit(1)

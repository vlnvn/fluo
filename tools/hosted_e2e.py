"""Execute browser tests on an explicit HTTPS preview; never print provider tokens."""
import json
import os
import subprocess
from pathlib import Path
from urllib.parse import urlparse

from tools.provision_postgres import read_env

ROOT = Path(__file__).resolve().parents[1]


def main():
    base = os.environ['FLUO_BASE_URL']
    parsed = urlparse(base)
    if parsed.scheme != 'https' or not parsed.hostname.endswith('.vercel.app'):
        raise ValueError('An explicit Vercel HTTPS origin is required')
    env = dict(os.environ)
    env['FLUO_VERCEL_OIDC_TOKEN'] = read_env(ROOT / '.local/fluo-development.env')['VERCEL_OIDC_TOKEN']
    destination = ROOT / 'docs/implementation/qa/e2e-results.json'
    historical = destination.read_bytes()
    try:
        with (ROOT / '.local/hosted-e2e-private.log').open('w', encoding='utf-8') as output:
            completed = subprocess.run(['npm.cmd', 'run', 'test:e2e'], cwd=ROOT / 'web', env=env,
                                       stdout=output, stderr=subprocess.STDOUT)
        result = json.loads(destination.read_text(encoding='utf-8'))
        result['hosted_origin'] = base
        archived = ROOT / 'docs/implementation/qa/vercel/hosted-e2e.json'
        archived.write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(json.dumps({'url': base, 'exit_code': completed.returncode, 'stats': result['stats']}))
        return completed.returncode
    finally:
        destination.write_bytes(historical)


if __name__ == '__main__':
    raise SystemExit(main())

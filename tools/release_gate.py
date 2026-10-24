"""Evidence gate: local readiness is separate from permission to expose staging."""
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', choices=['local', 'staging'], default='staging')
    args = parser.parse_args()
    qa = ROOT / 'docs/implementation/qa'
    evidence_path = qa / 'RELEASE_EVIDENCE.json'
    evidence = json.loads(evidence_path.read_text()) if evidence_path.exists() else {}
    junit = qa / 'guest-api.xml'
    suites = ET.parse(junit).getroot() if junit.exists() else ET.Element('missing')
    cases = list(suites.iter('testcase'))
    required = {'test_two_guests_and_anonymous_have_no_cross_object_access',
                'test_csrf_logout_expiry_and_forgery',
                'test_public_cookie_capabilities_docs_and_headers',
                'test_guest_limits_cleanup_and_persistence'}
    auth_tested = required.issubset({case.get('name') for case in cases}) and not any(
        list(suites.iter(tag)) for tag in ('failure', 'error', 'skipped'))
    checks = {
        'model_digest': hashlib.sha256((ROOT / 'models/fluo_hgb_synthetic_v2.joblib').read_bytes()).hexdigest() == '5237917ae6ccfccd2ff21d288b92201536c923028d8931599aaf9715033e9b09',
        'sensor_digest': hashlib.sha256((ROOT / 'data/original/fluo_sensor_stream.csv.gz').read_bytes()).hexdigest() == 'f9fe34bf04a31e753df47c6f736f5155a4eaf34a8a6dedf7b6b5a53ed00ce018',
        'executed_local_suites': evidence.get('local_gates_passed') is True,
        'auth_tests_pass_without_skip_or_xfail': auth_tested,
    }
    local_ready = all(checks.values())
    # Local TestClient/browser evidence cannot substitute for real hosted evidence.
    staging = {'server_identity_enforced_locally': auth_tested, 'session_ownership_enforced_locally': auth_tested,
               'protected_origin_and_https_verified': False, 'hosted_persistence_verified': False,
               'approved_hosting_and_budget_available': False}
    result = {'local_status': 'LOCAL_DEMO_READY' if local_ready else 'BLOCKED',
              'staging_status': 'PUBLIC_DEPLOYMENT_BLOCKED', 'deployed': False,
              'local_checks': checks, 'staging_checks': staging,
              'blockers': [key for key, passed in staging.items() if not passed]}
    destination = ROOT / 'docs/implementation/deployment/RELEASE_DECISION.json'
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2), encoding='utf-8', newline='\n')
    print(json.dumps(result, indent=2))
    return 0 if args.target == 'local' and local_ready else 2


if __name__ == '__main__':
    raise SystemExit(main())

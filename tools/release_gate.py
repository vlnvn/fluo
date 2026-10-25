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
    junit = qa / 'vercel/final-local-api.xml'
    if not junit.exists():
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
    def load(name):
        path = qa / 'vercel' / name
        return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}

    capture, security, persistence = [load(name) for name in ('hosted-capture.json', 'hosted-security.json', 'hosted-verify.json')]
    browser, reviewer, backup, release = [load(name) for name in ('hosted-e2e.json', 'reviewer-access.json', 'hosted-backup-restore.json', 'CLOUD_RELEASE.json')]
    provider, ci = load('DEPLOYMENT.json'), load('CI_DEPLOYED_COMMIT.json')
    stats = browser.get('stats', {})
    origin = release.get('url')
    manifest = load('DEPLOYED_APPLICATION_MANIFEST.json')
    source_matches = bool(manifest) and all((ROOT / name).exists() and hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest for name, digest in manifest.items())
    def passed(document, count):
        return document.get('status') == 'PASS' and len(document.get('checks', [])) >= count and all(check.get('pass') is True for check in document.get('checks', []))

    staging = {'server_identity_enforced_locally': auth_tested, 'session_ownership_enforced_locally': auth_tested,
               'protected_origin_and_https_verified': passed(capture, 77) and capture.get('url') == origin,
               'hosted_negative_security': passed(security, 15) and security.get('url') == origin,
               'hosted_persistence_verified': passed(persistence, 7) and persistence.get('url') == origin,
               'hosted_browser_passed': stats.get('expected') == 18 and all(stats.get(key) == 0 for key in ('unexpected', 'flaky', 'skipped')) and release.get('browser_url') == origin and browser.get('hosted_origin') == origin,
               'reviewer_share_access_verified': reviewer.get('status') == 'PASS' and reviewer.get('url') == origin,
               'logical_backup_restore_verified': backup.get('status') == 'PASS' and backup.get('source_database_untouched') is True and len(backup.get('table_hashes_match', {})) == 5 and all(table.get('exact_rows_equal') is True for table in backup.get('table_hashes_match', {}).values()),
               'approved_hosting_and_budget_available': release.get('free_plan_verified') is True and release.get('owner_educational_use_confirmed') is True,
               'actual_provider_ready': provider.get('readyState') == 'READY' and provider.get('target') is None and provider.get('meta', {}).get('githubCommitSha') == release.get('deployed_git_sha') and 'https://' + provider.get('url', '') == origin,
               'deployed_application_source_matches': source_matches,
               'pdf_parsed': release.get('pdf_a4_pages') == 2,
               'ci_passed': ci.get('headRevision') == release.get('deployed_git_sha') and bool(ci.get('checks')) and all(check.get('conclusion') == 'success' for check in ci.get('checks', []))}
    deployed = local_ready and all(staging.values())
    result = {'local_status': 'LOCAL_DEMO_READY' if local_ready else 'BLOCKED',
              'staging_status': 'DEPLOYED_ACCESS_CONTROLLED' if deployed else 'PUBLIC_DEPLOYMENT_BLOCKED', 'deployed': deployed,
              'url': origin, 'deployed_git_sha': release.get('deployed_git_sha'),
              'local_checks': checks, 'staging_checks': staging,
              'blockers': [key for key, passed in staging.items() if not passed]}
    destination = ROOT / 'docs/implementation/deployment/RELEASE_DECISION.json'
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2), encoding='utf-8', newline='\n')
    print(json.dumps(result, indent=2))
    return 0 if (args.target == 'local' and local_ready) or (args.target == 'staging' and deployed) else 2


if __name__ == '__main__':
    raise SystemExit(main())

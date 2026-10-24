"""Evidence gate: local readiness is separate from permission to expose staging."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', choices=['local', 'staging'], default='staging')
    args = parser.parse_args()
    qa = ROOT / 'docs/implementation/qa'
    evidence_path = qa / 'RELEASE_EVIDENCE.json'
    evidence = json.loads(evidence_path.read_text()) if evidence_path.exists() else {}
    checks = {
        'model_digest': hashlib.sha256((ROOT / 'models/fluo_hgb_synthetic_v2.joblib').read_bytes()).hexdigest() == '5237917ae6ccfccd2ff21d288b92201536c923028d8931599aaf9715033e9b09',
        'sensor_digest': hashlib.sha256((ROOT / 'data/original/fluo_sensor_stream.csv.gz').read_bytes()).hexdigest() == 'f9fe34bf04a31e753df47c6f736f5155a4eaf34a8a6dedf7b6b5a53ed00ce018',
        'executed_local_suites': evidence.get('local_gates_passed') is True,
    }
    local_ready = all(checks.values())
    # These remain false until an implementation and on-host negative tests exist.
    staging = {'server_identity_enforced': False, 'session_ownership_enforced': False,
               'protected_origin_and_https_verified': False, 'hosted_persistence_verified': False,
               'container_built_and_smoked': False}
    result = {'local_status': 'LOCAL_DEMO_READY' if local_ready else 'BLOCKED',
              'staging_status': 'BLOCKED_FOR_PUBLIC_ACCESS', 'deployed': False,
              'local_checks': checks, 'staging_checks': staging,
              'blockers': [key for key, passed in staging.items() if not passed]}
    destination = ROOT / 'docs/implementation/deployment/RELEASE_DECISION.json'
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2), encoding='utf-8', newline='\n')
    print(json.dumps(result, indent=2))
    return 0 if args.target == 'local' and local_ready else 2


if __name__ == '__main__':
    raise SystemExit(main())

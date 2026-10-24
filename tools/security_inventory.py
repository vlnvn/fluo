"""Bounded secret-pattern checks: report locations only, never matched values."""
import hashlib
import json
import re
import subprocess
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = {
    'private-key': re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'github-token': re.compile(rb'\bgh[pousr]_[A-Za-z0-9]{30,}\b'),
    'openai-key': re.compile(rb'\bsk-(?:proj-)?[A-Za-z0-9_-]{40,}\b'),
    'aws-access-id': re.compile(rb'\bAKIA[A-Z0-9]{16}\b'),
}


def main():
    issues, checked = [], set()
    commits = subprocess.check_output(['git', 'rev-list', '--all'], cwd=ROOT, text=True).splitlines()
    for revision in commits:
        rows = subprocess.check_output(['git', 'ls-tree', '-r', revision], cwd=ROOT, text=True).splitlines()
        for row in rows:
            metadata, name = row.split('\t', 1)
            blob = metadata.split()[2]
            if blob in checked or Path(name).suffix in {'.png', '.joblib', '.ttf', '.mp3', '.ico'}:
                continue
            checked.add(blob)
            content = subprocess.check_output(['git', 'cat-file', 'blob', blob], cwd=ROOT)
            for rule, pattern in RULES.items():
                if pattern.search(content):
                    issues.append({'revision': revision, 'file': name, 'rule': rule})
    for directory in ['backend', 'web/src', 'tools']:
        for path in (ROOT / directory).rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts:
                for rule, pattern in RULES.items():
                    if pattern.search(path.read_bytes()):
                        issues.append({'revision': 'working-tree', 'file': path.relative_to(ROOT).as_posix(), 'rule': rule})
    original = ROOT.parent / 'FLUO_Notification_Chime.mp3'
    served = ROOT / 'web/public/assets/notification-chime.mp3'
    sound = {'served_sha256': hashlib.sha256(served.read_bytes()).hexdigest(), 'source_exists': original.exists()}
    if original.exists():
        sound['original_sha256'] = hashlib.sha256(original.read_bytes()).hexdigest()
        sound['identical'] = sound['original_sha256'] == sound['served_sha256']
    result = {'commits_scanned': len(commits), 'unique_text_blobs_scanned': len(checked), 'findings': issues,
              'limitation': 'Pattern-based check, not proof that arbitrary secrets are absent; ignored private files are not published.',
              'chime': sound, 'tools': {name: version(name) for name in ('pip-audit', 'bandit', 'Pillow', 'pypdf')}}
    (ROOT / 'docs/implementation/qa/SECURITY_INVENTORY.json').write_text(json.dumps(result, indent=2), encoding='utf-8', newline='\n')
    print(json.dumps({'commits': len(commits), 'findings': len(issues), 'sound_identical': sound.get('identical')}))
    return int(bool(issues))


if __name__ == '__main__':
    raise SystemExit(main())

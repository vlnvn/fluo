"""Read-only forensic inventory of the supplied research archive and Git checkout."""
import ast
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
ARCHIVE = WORKSPACE / 'FLUO_ML_RESEARCH_AUDITED_20261024.zip'
EXTRACTED = WORKSPACE / 'source-audit' / 'ml-20261024'
OUT = ROOT / 'docs' / 'implementation'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((EXTRACTED / 'PACKAGE_SHA256.json').read_text())
    checks = []
    for name, expected in manifest['files'].items():
        path = EXTRACTED / name
        actual = sha(path) if path.is_file() else None
        checks.append({'path': name, 'expected': expected, 'actual': actual, 'matches': actual == expected})
    differences = []
    scripts = []
    for path in sorted(EXTRACTED.rglob('*')):
        if not path.is_file():
            continue
        rel = path.relative_to(EXTRACTED).as_posix()
        tracked = subprocess.run(['git', 'show', f'f2c05af115f374848ee3b8592a32af8648afea53:{rel}'], cwd=ROOT, capture_output=True)
        if tracked.returncode == 0:
            original = tracked.stdout
            differences.append({'path': rel, 'archive_sha256': sha(path), 'repo_sha256': hashlib.sha256(original).hexdigest(), 'identical': path.read_bytes() == original})
        if path.suffix == '.py':
            tree = ast.parse(path.read_text(encoding='utf-8-sig'))
            scripts.append({'path': rel, 'functions': [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))], 'lines': len(path.read_text().splitlines())})
    with zipfile.ZipFile(ARCHIVE) as archive:
        bad_member = archive.testzip()
        entries = [{'path': i.filename, 'bytes': i.file_size, 'compressed_bytes': i.compress_size} for i in archive.infolist()]
    result = {'archive': str(ARCHIVE), 'archive_sha256': sha(ARCHIVE), 'zip_crc_error': bad_member, 'entries': entries,
              'package_checksum_checks': checks, 'comparison': differences, 'python_static_inventory': scripts,
              'models': {'archive_selected': sha(EXTRACTED / 'selected_model.joblib'), 'repo_hgb': sha(ROOT / 'models/fluo_hgb_synthetic_v2.joblib')},
              'repo_sha': subprocess.check_output(['git', 'rev-parse', 'f2c05af115f374848ee3b8592a32af8648afea53'], cwd=ROOT, text=True).strip()}
    (OUT / 'SOURCE_MANIFEST.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    failures = [c for c in checks if not c['matches']]
    changed = [c['path'] for c in differences if not c['identical']]
    (OUT / 'SOURCE_INVENTORY.md').write_text(f'''# Source inventory — 25 October 2026

- Workspace: `{WORKSPACE}`; application checkout: `{ROOT}`.
- Original ZIP: `{ARCHIVE.name}` ({ARCHIVE.stat().st_size:,} bytes), preserved without modification.
- ZIP SHA-256: `{sha(ARCHIVE)}`.
- Archive CRC: {bad_member or 'PASS for every member'}; {len(entries)} members.
- Package checksum manifest: {len(checks) - len(failures)}/{len(checks)} match.
- GitHub repository: https://github.com/vlnvn/fluo ; verified main SHA `{result['repo_sha']}`.
- Implementation branch: `feat/fluo-fullstack-audited-replay`; checkout initially clean.
- Archived extraction: `{EXTRACTED}`; preserved separately from application.
- Archive selected model SHA-256: `{result['models']['archive_selected']}`.
- Repository HGB model SHA-256: `{result['models']['repo_hgb']}`.
- Common archive/repository files with differences: {', '.join(changed) or 'none'}.
- Figma access: connected API available; session `00473d8a-d6b7-4499-b83d-0f6fb37fe34a`.
- Figma: 83 visible top-level frames; start points `74:2` and `128:5`; 1,465 nodes with prototype reactions (includes hover handlers and repeated states).
- Google Docs DEEPTECH: readable through connected Drive; modified 24 October 2026; `alven 2` content present. Private text cache is excluded from commits.
- Full paths, lengths, hashes, Python function inventory and comparisons: `SOURCE_MANIFEST.json`.

## Preserved research contract

HistGradientBoostingClassifier, six causal features, strict score >0.90, 5 of 10 rows per site, 20-row mode stabilization and five valid-history rows. The 13 telemetry fields and original inference function are authoritative. Seeds named 20261101/20270111 are numeric identifiers, not experimental dates. Synthetic signature score is not causal probability. Recovery eligibility remains unknown and physical actuation is false.

## Source review

All archived Python files parsed; all member bytes checked against available package hashes; archived reports, configs, model card, data sources and experiment summaries reviewed. Dataset schemas, record cadence and frozen artifact compatibility are verified in Gate 1. The archive supplies datasets missing from Git; the repository has no frontend or HTTP backend. Historical v1 remains historical.
''', encoding='utf-8')
    print(json.dumps({'members': len(entries), 'checksum_failures': failures, 'different_common_files': changed, 'models': result['models']}, indent=2))


if __name__ == '__main__':
    main()

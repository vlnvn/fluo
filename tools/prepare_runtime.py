"""Materialize the supplied audited ZIP safely without overwriting research."""
import hashlib
import json
import os
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_ZIP = '7ad2b4a94a3147241641ff839853c927828ca077858bc801c6e7c157d3c5d5ca'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    archive = Path(os.environ.get('FLUO_ARCHIVE_PATH', ROOT.parent / 'FLUO_ML_RESEARCH_AUDITED_20261024.zip'))
    if not archive.is_file():
        raise SystemExit(f'Supplied archive missing: {archive}. Set FLUO_ARCHIVE_PATH; no model will be retrained.')
    if sha(archive) != EXPECTED_ZIP:
        raise SystemExit('Archive checksum mismatch; refusing to replace audited research artifacts.')
    extracted = ROOT.parent / 'source-audit/ml-20261024'
    extracted.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as bundle:
        if bundle.testzip():
            raise SystemExit('Archive CRC failure')
        for entry in bundle.infolist():
            if entry.is_dir():
                continue
            path = (extracted / entry.filename).resolve()
            if not path.is_relative_to(extracted.resolve()):
                raise SystemExit(f'Unsafe archive member: {entry.filename}')
            data = bundle.read(entry)
            if path.exists():
                if hashlib.sha256(path.read_bytes()).digest() != hashlib.sha256(data).digest():
                    raise SystemExit(f'Preserved extraction differs: {path}')
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
    manifest = json.loads((extracted / 'PACKAGE_SHA256.json').read_text())
    for name, expected in manifest['files'].items():
        if sha(extracted / name) != expected:
            raise SystemExit(f'Package manifest mismatch: {name}')
    for source in (extracted / 'data').rglob('*'):
        if not source.is_file():
            continue
        target = ROOT / source.relative_to(extracted)
        if target.exists() and sha(target) != sha(source):
            raise SystemExit(f'Existing runtime data differs; not overwritten: {target}')
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    model = ROOT / 'models/fluo_hgb_synthetic_v2.joblib'
    if sha(model) != sha(extracted / 'selected_model.joblib'):
        raise SystemExit('Repository and archive model artifacts differ')
    print('Verified archive, all package checksums, original data and selected HGB; no training performed.')


if __name__ == '__main__':
    main()

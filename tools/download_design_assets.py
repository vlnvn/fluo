"""Materialize only asset URLs supplied by Figma design context."""
import hashlib
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'web/public/assets'
OUT.mkdir(parents=True, exist_ok=True)
files = [ROOT / 'docs/implementation/sources/figma-overview-context.txt', *sorted((ROOT / 'docs/implementation/sources').glob('context-*.txt'))]
assets = {}
for file in files:
    for name, url in re.findall(r'const (img\w+) = "([^"]+)"', file.read_text(encoding='utf-8')):
        assets.setdefault(name[3:], {'url': url, 'source_context': file.name})
def download(item):
    name, info = item
    path = OUT / f'{name}.svg'
    if not path.exists() or not path.stat().st_size:
        subprocess.run(['curl.exe', '-f', '-L', '--retry', '2', '--max-time', '45', '-sS', '-o', str(path), info['url']], check=True)
    data = path.read_bytes()
    if not data or b'<svg' not in data[:1000]:
        raise ValueError(f'Invalid asset: {name}')
    root = re.search(rb'<svg\b[^>]*>', data).group(0).decode()
    info.update({'local': f'/assets/{path.name}', 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'root_dimensions': root})
    print(name, len(data))
with ThreadPoolExecutor(max_workers=4) as pool:
    list(pool.map(download, assets.items()))
(ROOT / 'docs/implementation/DESIGN_ASSETS.json').write_text(json.dumps(assets, indent=2), encoding='utf-8')

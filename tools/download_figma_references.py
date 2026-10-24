import hashlib
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
items = json.loads((ROOT / '.local/figma-screens-download.json').read_text())
out = ROOT / 'docs/implementation/qa/figma'
out.mkdir(parents=True, exist_ok=True)


def download(item):
    path = out / f'{item["name"]}.png'
    subprocess.run(['curl.exe','-f','-L','--max-time','45','--retry','2','-sS','-o',str(path),item['image_url']],check=True)
    if not path.stat().st_size:
        raise ValueError(f'Empty Figma reference: {item["name"]}')
    return {k:v for k,v in item.items() if k != 'image_url'} | {'file':str(path.relative_to(ROOT)), 'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}


with ThreadPoolExecutor(max_workers=4) as pool:
    manifest = list(pool.map(download, items))
(ROOT / 'docs/implementation/qa/FIGMA_REFERENCES.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(f'Downloaded {len(manifest)} original Figma references')

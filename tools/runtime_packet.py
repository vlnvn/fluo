"""Package/install only private runtime inputs, never the original research ZIP."""
import argparse
import hashlib
import io
import json
import os
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    'data/original/fluo_sensor_stream.csv.gz': 'f9fe34bf04a31e753df47c6f736f5155a4eaf34a8a6dedf7b6b5a53ed00ce018',
    'data/original/fluo_episode_labels.csv': 'e5b1368942a98452abd8b49e3c93d154b0d07614d33e99ec4e755a8e45611106',
}


def install(data):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        if set(archive.namelist()) != set(FILES):
            raise RuntimeError('Unexpected runtime packet entries')
        for name, digest in FILES.items():
            entry = archive.getinfo(name)
            if entry.file_size > 8 * 1024 * 1024:
                raise RuntimeError('Runtime entry exceeds size limit')
            content = archive.read(name)
            if hashlib.sha256(content).hexdigest() != digest:
                raise RuntimeError('Audited runtime checksum mismatch')
            path = ROOT / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, *args):
        raise RuntimeError('Runtime artifact redirects are not permitted')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--download', action='store_true')
    args = parser.parse_args()
    if args.download:
        url = os.environ.get('FLUO_RUNTIME_URL', '')
        digest = os.environ.get('FLUO_RUNTIME_PACKET_SHA256', '')
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or len(digest) != 64:
            raise SystemExit('Configure the private HTTPS runtime artifact and checksum in provider secret storage')
        request = urllib.request.Request(url)
        token = os.environ.get('FLUO_RUNTIME_BEARER', '')
        if token:
            request.add_header('Authorization', 'Bearer ' + token)
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=30) as response:
            data = response.read(4 * 1024 * 1024 + 1)
        if len(data) > 4 * 1024 * 1024 or hashlib.sha256(data).hexdigest() != digest:
            raise SystemExit('Private runtime packet verification failed')
        install(data)
        print('Verified private runtime inputs installed; no URL or credential logged.')
    else:
        target = ROOT / '.local/fluo-runtime-private.zip'
        target.parent.mkdir(exist_ok=True)
        with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            for name, digest in FILES.items():
                content = (ROOT / name).read_bytes()
                if hashlib.sha256(content).hexdigest() != digest:
                    raise SystemExit('Source runtime input is not the audited version')
                archive.writestr(name, content)
        manifest = {'filename': target.name, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                    'bytes': target.stat().st_size, 'contents': FILES, 'public_upload_authorized': False}
        (ROOT / 'docs/implementation/deployment/RUNTIME_PACKET.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8', newline='\n')
        print('Private runtime packet prepared locally; excluded from Git and public images.')


if __name__ == '__main__':
    main()

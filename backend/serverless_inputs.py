"""Load only audited sensor/catalog bytes from private PostgreSQL into scratch.

No public URLs, user uploads, ground truth, arbitrary filenames, or model download.
Model remains the original checksum-verified repository artifact.
"""
import hashlib
import os
import tempfile
import threading
from pathlib import Path

from psycopg import connect, Error

from .postgres_store import connection_options

FILES = {
    'fluo_sensor_stream.csv.gz': 'f9fe34bf04a31e753df47c6f736f5155a4eaf34a8a6dedf7b6b5a53ed00ce018',
    'fluo_episode_labels.csv': 'e5b1368942a98452abd8b49e3c93d154b0d07614d33e99ec4e755a8e45611106',
}
_lock = threading.Lock()


def prepare_inputs():
    dsn = os.environ.get('FLUO_DATABASE_URL', '')
    if not dsn:
        raise RuntimeError('PRIVATE_RUNTIME_DATABASE_REQUIRED')
    root = Path(tempfile.gettempdir()) / 'fluo-audited-runtime-v1'
    with _lock:
        root.mkdir(mode=0o700, exist_ok=True)
        if all((root / name).is_file() and hashlib.sha256((root / name).read_bytes()).hexdigest() == digest for name, digest in FILES.items()):
            return root
        try:
            with connect(dsn, **connection_options(dsn)) as connection:
                for name, digest in FILES.items():
                    row = connection.execute('SELECT body FROM fluo_artifacts WHERE name=%s AND sha256=%s', (name, digest)).fetchone()
                    if not row or len(row[0]) > 4 * 1024 * 1024 or hashlib.sha256(row[0]).hexdigest() != digest:
                        raise RuntimeError('PRIVATE_RUNTIME_DIGEST_MISMATCH')
                    temporary = root / (name + '.tmp')
                    temporary.write_bytes(row[0])
                    temporary.replace(root / name)
        except Error:
            raise RuntimeError('PRIVATE_RUNTIME_UNAVAILABLE') from None
    return root

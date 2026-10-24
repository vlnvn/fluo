"""Small local SQLite store. No authentication or shared production tenancy."""
import json
import sqlite3
import threading
import time

from .service_errors import DomainError
import uuid
from pathlib import Path


class Store:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.db = sqlite3.connect(path, check_same_thread=False)
        schema_version = self.db.execute('PRAGMA user_version').fetchone()[0]
        if schema_version not in (0, 1, 2):
            self.db.close()
            raise RuntimeError('DB_SCHEMA_UNSUPPORTED: refusing a silent schema downgrade')
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA busy_timeout=5000')
        self.db.execute('PRAGMA max_page_count=32768')
        self.db.execute('PRAGMA user_version=2')
        self.db.execute('CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS reviews (owner TEXT, event_id TEXT, payload TEXT NOT NULL, PRIMARY KEY(owner,event_id))')
        self.db.execute('CREATE TABLE IF NOT EXISTS preferences (owner TEXT PRIMARY KEY, payload TEXT NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS guest_principals (digest TEXT PRIMARY KEY, csrf TEXT NOT NULL, expires REAL NOT NULL, revoked INTEGER NOT NULL DEFAULT 0, mutations INTEGER NOT NULL DEFAULT 0)')
        self.db.execute('CREATE TABLE IF NOT EXISTS session_owners (session_id TEXT PRIMARY KEY, digest TEXT NOT NULL)')
        self.db.commit()

    def create(self, scenario, cursor, owner_digest=None, maximum=5):
        session = {'id': str(uuid.uuid4()), 'scenario_id': scenario, 'cursor': cursor, 'speed': 1, 'playing': False, 'anchor': time.time()}
        with self.lock, self.db:
            if owner_digest and self.db.execute('SELECT COUNT(*) FROM session_owners WHERE digest=?',(owner_digest,)).fetchone()[0] >= maximum:
                raise DomainError('SESSION_QUOTA', 'This guest workspace reached its replay-session limit.', 429)
            self.db.execute('INSERT INTO sessions VALUES (?,?)',(session['id'],json.dumps(session)))
            if owner_digest:
                self.db.execute('INSERT INTO session_owners VALUES (?,?)',(session['id'],owner_digest))
        return session

    def session(self, session_id):
        with self.lock:
            row = self.db.execute('SELECT payload FROM sessions WHERE id=?', (session_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def save_session(self, session):
        with self.lock, self.db:
            self.db.execute('INSERT OR REPLACE INTO sessions VALUES (?,?)', (session['id'], json.dumps(session)))
            self.db.commit()

    def review(self, owner, event_id):
        with self.lock:
            row = self.db.execute('SELECT payload FROM reviews WHERE owner=? AND event_id=?', (owner, event_id)).fetchone()
        return json.loads(row[0]) if row else None

    def save_review(self, owner, event_id, review):
        if review.get('revision', 0) > 30:
            raise DomainError('REVIEW_QUOTA', 'This guest review reached its revision limit.', 429)
        with self.lock, self.db:
            self.db.execute('INSERT OR REPLACE INTO reviews VALUES (?,?,?)', (owner, event_id, json.dumps(review)))
            self.db.commit()

    def preferences(self, owner):
        with self.lock:
            row = self.db.execute('SELECT payload FROM preferences WHERE owner=?', (owner,)).fetchone()
        return json.loads(row[0]) if row else {'warning_sound': False}

    def save_preferences(self, owner, data):
        with self.lock, self.db:
            self.db.execute('INSERT OR REPLACE INTO preferences VALUES (?,?)', (owner, json.dumps(data)))
            self.db.commit()

    def close(self):
        with self.lock:
            self.db.close()

    def backup(self, destination):
        with self.lock, sqlite3.connect(destination) as target:
            self.db.backup(target)

    def guest(self, digest):
        with self.lock:
            row = self.db.execute('SELECT digest,csrf,expires,revoked,mutations FROM guest_principals WHERE digest=?', (digest,)).fetchone()
        return dict(zip(['digest','csrf','expires','revoked','mutations'], row)) if row else None

    def create_guest(self, owner, maximum):
        with self.lock, self.db:
            expired = [r[0] for r in self.db.execute('SELECT digest FROM guest_principals WHERE expires<=? OR revoked=1', (time.time(),))]
            for digest in expired:
                ids = [r[0] for r in self.db.execute('SELECT session_id FROM session_owners WHERE digest=?', (digest,))]
                for sid in ids:
                    self.db.execute('DELETE FROM reviews WHERE owner=?', (sid,))
                    self.db.execute('DELETE FROM preferences WHERE owner=?', (sid,))
                    self.db.execute('DELETE FROM sessions WHERE id=?', (sid,))
                self.db.execute('DELETE FROM session_owners WHERE digest=?', (digest,))
                self.db.execute('DELETE FROM guest_principals WHERE digest=?', (digest,))
            if self.db.execute('SELECT COUNT(*) FROM guest_principals').fetchone()[0] >= maximum:
                raise DomainError('GUEST_CAPACITY', 'The demonstration is at capacity. Please try later.', 503)
            self.db.execute('INSERT INTO guest_principals VALUES (?,?,?,?,?)', (owner['digest'],owner['csrf'],owner['expires'],0,0))

    def revoke_guest(self, digest):
        with self.lock, self.db:
            self.db.execute('UPDATE guest_principals SET revoked=1 WHERE digest=?', (digest,))

    def consume_guest_mutation(self, digest, maximum):
        with self.lock, self.db:
            result = self.db.execute('UPDATE guest_principals SET mutations=mutations+1 WHERE digest=? AND mutations<?', (digest, maximum))
            if result.rowcount != 1:
                raise DomainError('GUEST_QUOTA', 'This guest workspace reached its action limit.', 429)

    def owns_session(self, digest, session_id):
        with self.lock:
            return self.db.execute('SELECT 1 FROM session_owners WHERE digest=? AND session_id=?', (digest,session_id)).fetchone() is not None

    def claim_session(self, digest, session_id, maximum):
        with self.lock, self.db:
            if self.db.execute('SELECT COUNT(*) FROM session_owners WHERE digest=?', (digest,)).fetchone()[0] >= maximum:
                raise DomainError('SESSION_QUOTA', 'This guest workspace reached its replay-session limit.', 429)
            self.db.execute('INSERT INTO session_owners VALUES (?,?)', (session_id,digest))

"""Small local SQLite store. No authentication or shared production tenancy."""
import json
import sqlite3
import threading
import time
import uuid
from pathlib import Path


class Store:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.db = sqlite3.connect(path, check_same_thread=False)
        schema_version = self.db.execute('PRAGMA user_version').fetchone()[0]
        if schema_version not in (0, 1):
            self.db.close()
            raise RuntimeError('DB_SCHEMA_UNSUPPORTED: refusing a silent schema downgrade')
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA busy_timeout=5000')
        self.db.execute('PRAGMA user_version=1')
        self.db.execute('CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS reviews (owner TEXT, event_id TEXT, payload TEXT NOT NULL, PRIMARY KEY(owner,event_id))')
        self.db.execute('CREATE TABLE IF NOT EXISTS preferences (owner TEXT PRIMARY KEY, payload TEXT NOT NULL)')
        self.db.commit()

    def create(self, scenario, cursor):
        session = {'id': str(uuid.uuid4()), 'scenario_id': scenario, 'cursor': cursor, 'speed': 1, 'playing': False, 'anchor': time.time()}
        self.save_session(session)
        return session

    def session(self, session_id):
        with self.lock:
            row = self.db.execute('SELECT payload FROM sessions WHERE id=?', (session_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def save_session(self, session):
        with self.lock:
            self.db.execute('INSERT OR REPLACE INTO sessions VALUES (?,?)', (session['id'], json.dumps(session)))
            self.db.commit()

    def review(self, owner, event_id):
        with self.lock:
            row = self.db.execute('SELECT payload FROM reviews WHERE owner=? AND event_id=?', (owner, event_id)).fetchone()
        return json.loads(row[0]) if row else None

    def save_review(self, owner, event_id, review):
        with self.lock:
            self.db.execute('INSERT OR REPLACE INTO reviews VALUES (?,?,?)', (owner, event_id, json.dumps(review)))
            self.db.commit()

    def preferences(self, owner):
        with self.lock:
            row = self.db.execute('SELECT payload FROM preferences WHERE owner=?', (owner,)).fetchone()
        return json.loads(row[0]) if row else {'warning_sound': False}

    def save_preferences(self, owner, data):
        with self.lock:
            self.db.execute('INSERT OR REPLACE INTO preferences VALUES (?,?)', (owner, json.dumps(data)))
            self.db.commit()

    def close(self):
        with self.lock:
            self.db.close()

    def backup(self, destination):
        with self.lock, sqlite3.connect(destination) as target:
            self.db.backup(target)

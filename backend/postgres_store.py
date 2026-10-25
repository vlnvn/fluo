"""Persistent guest state for serverless instances; no SQLite import or ML storage."""
import threading
import sys
import time
import uuid
from pathlib import Path
import certifi

from psycopg import Error
from psycopg.conninfo import conninfo_to_dict
from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool, PoolTimeout, TooManyRequests

from .service_errors import DomainError


def connection_options(dsn):
    try:
        options = conninfo_to_dict(dsn)
    except Exception:
        raise RuntimeError('DATABASE_CONFIGURATION_INVALID') from None
    host = options.get('host', '')
    if not host:
        raise RuntimeError('DATABASE_HOST_REQUIRED')
    kwargs = {'connect_timeout': 5, 'prepare_threshold': None}
    if host not in ('localhost', '127.0.0.1', '::1'):
        kwargs.update(sslmode='verify-full', sslrootcert=certifi.where())
    return kwargs


class TransactionLock:
    """Reentrant per-thread transaction; advisory lock also spans instances.

    A deliberately conservative single demo-wide lock preserves the existing
    service's read/modify/write boundaries. This is not a high-throughput design.
    """
    def __init__(self, pool):
        self.pool = pool
        self.local = threading.local()

    def __enter__(self):
        if getattr(self.local, 'depth', 0):
            self.local.depth += 1
            return self
        context = self.pool.connection(timeout=5)
        try:
            conn = context.__enter__()
            conn.execute("SET LOCAL lock_timeout = '5s'")
            conn.execute("SET LOCAL statement_timeout = '5s'")
            conn.execute('SELECT pg_advisory_xact_lock(20261025, 3)')
        except (Error, PoolTimeout, TooManyRequests):
            if 'conn' in locals():
                context.__exit__(*sys.exc_info())
            raise DomainError('STATE_UNAVAILABLE', 'Workspace storage is temporarily unavailable. Retry shortly.', 503) from None
        self.local.context, self.local.conn, self.local.depth = context, conn, 1
        return self

    def __exit__(self, kind, error, traceback):
        self.local.depth -= 1
        if self.local.depth:
            return False
        try:
            return self.local.context.__exit__(kind, error, traceback)
        except Error:
            raise DomainError('STATE_UNAVAILABLE', 'Workspace storage is temporarily unavailable. Retry shortly.', 503) from None
        finally:
            self.local.conn = None


class PostgresStore:
    shared_budgets = True
    description = 'Private PostgreSQL guest workspace; human operator identity is unverified.'

    def __init__(self, dsn):
        kwargs = connection_options(dsn)
        self.pool = ConnectionPool(dsn, min_size=0, max_size=2, max_waiting=8, timeout=5,
                                   max_idle=30, max_lifetime=300, kwargs=kwargs,
                                   check=ConnectionPool.check_connection, open=True)
        self.lock = TransactionLock(self.pool)
        try:
            with self.lock:
                version = self._one('SELECT version FROM fluo_schema WHERE singleton=TRUE')
                if not version or version[0] != 1:
                    raise RuntimeError('POSTGRES_SCHEMA_UNSUPPORTED: run the reviewed migration explicitly')
        except BaseException:
            self.pool.close()
            raise

    def _query(self, statement, params=()):
        try:
            return self.lock.local.conn.execute(statement, params)
        except Error:
            raise DomainError('STATE_UNAVAILABLE', 'Workspace storage is temporarily unavailable. Retry shortly.', 503) from None

    def _one(self, statement, params=()):
        return self._query(statement, params).fetchone()

    def create(self, scenario, cursor, owner_digest=None, maximum=5):
        if not owner_digest:
            raise DomainError('AUTH_REQUIRED', 'Start a private guest workspace.', 401)
        session = {'id': str(uuid.uuid4()), 'scenario_id': scenario, 'cursor': cursor,
                   'speed': 1, 'playing': False, 'anchor': time.time()}
        with self.lock:
            count = self._one('SELECT count(*) FROM fluo_sessions WHERE digest=%s', (owner_digest,))[0]
            if count >= maximum:
                raise DomainError('SESSION_QUOTA', 'This guest workspace reached its replay-session limit.', 429)
            self._query('INSERT INTO fluo_sessions(id,digest,payload) VALUES(%s,%s,%s)',
                        (session['id'], owner_digest, Jsonb(session)))
        return session

    def session(self, session_id):
        with self.lock:
            row = self._one('SELECT payload FROM fluo_sessions WHERE id=%s', (session_id,))
        return row[0] if row else None

    def save_session(self, session):
        with self.lock:
            self._query('UPDATE fluo_sessions SET payload=%s WHERE id=%s', (Jsonb(session), session['id']))

    def review(self, owner, event_id):
        with self.lock:
            row = self._one('SELECT payload FROM fluo_reviews WHERE session_id=%s AND event_id=%s', (owner, event_id))
        return row[0] if row else None

    def reviews(self, owner):
        with self.lock:
            return dict(self._query('SELECT event_id,payload FROM fluo_reviews WHERE session_id=%s', (owner,)).fetchall())

    def save_review(self, owner, event_id, review):
        if review.get('revision', 0) > 30:
            raise DomainError('REVIEW_QUOTA', 'This guest review reached its revision limit.', 429)
        with self.lock:
            row = self._one('SELECT payload FROM fluo_reviews WHERE session_id=%s AND event_id=%s', (owner, event_id))
            prior = row[0]['revision'] if row else 0
            if review['revision'] != prior + 1:
                raise DomainError('REVISION_CONFLICT', 'Review changed; reload before saving.', 409)
            self._query('INSERT INTO fluo_reviews VALUES(%s,%s,%s) ON CONFLICT(session_id,event_id) DO UPDATE SET payload=EXCLUDED.payload',
                        (owner, event_id, Jsonb(review)))

    def preferences(self, owner):
        with self.lock:
            row = self._one('SELECT payload FROM fluo_preferences WHERE session_id=%s', (owner,))
        return row[0] if row else {'warning_sound': False}

    def save_preferences(self, owner, data):
        with self.lock:
            self._query('INSERT INTO fluo_preferences VALUES(%s,%s) ON CONFLICT(session_id) DO UPDATE SET payload=EXCLUDED.payload', (owner, Jsonb(data)))

    def guest(self, digest):
        with self.lock:
            row = self._one('SELECT digest,csrf,expires,revoked,mutations FROM fluo_guests WHERE digest=%s', (digest,))
        return dict(zip(['digest', 'csrf', 'expires', 'revoked', 'mutations'], row)) if row else None

    def create_guest(self, owner, maximum):
        with self.lock:
            self._query('DELETE FROM fluo_guests WHERE expires<=%s OR revoked=TRUE', (time.time(),))
            if self._one('SELECT count(*) FROM fluo_guests')[0] >= maximum:
                raise DomainError('GUEST_CAPACITY', 'The demonstration is at capacity. Please try later.', 503)
            self._query('INSERT INTO fluo_guests(digest,csrf,expires) VALUES(%s,%s,%s)',
                        (owner['digest'], owner['csrf'], owner['expires']))

    def revoke_guest(self, digest):
        with self.lock:
            self._query('UPDATE fluo_guests SET revoked=TRUE WHERE digest=%s', (digest,))

    def consume_guest_mutation(self, digest, maximum):
        with self.lock:
            row = self._query('UPDATE fluo_guests SET mutations=mutations+1 WHERE digest=%s AND mutations<%s AND NOT revoked AND expires>%s', (digest, maximum, time.time()))
            if row.rowcount != 1:
                raise DomainError('GUEST_QUOTA', 'This guest workspace reached its action limit or expired.', 429)

    def owns_session(self, digest, session_id):
        with self.lock:
            return self._one('SELECT 1 FROM fluo_sessions s JOIN fluo_guests g ON g.digest=s.digest WHERE s.digest=%s AND s.id=%s AND NOT g.revoked AND g.expires>%s', (digest, session_id, time.time())) is not None

    def consume_request_budget(self, guest_entry=False):
        now = int(time.time())
        limits = [('minute', now // 60, 1200), ('hour', now // 3600, 12000)]
        if guest_entry:
            limits.append(('entry-hour', now // 3600, 60))
        with self.lock:
            self._query('DELETE FROM fluo_budgets WHERE expires<%s', (now,))
            for name, window, maximum in limits:
                row = self._one('INSERT INTO fluo_budgets(name,period,hits,expires) VALUES(%s,%s,1,%s) ON CONFLICT(name,period) DO UPDATE SET hits=fluo_budgets.hits+1 WHERE fluo_budgets.hits<%s RETURNING hits',
                                (name, window, now + 7200, maximum))
                if not row:
                    raise DomainError('DEMO_RATE_LIMIT', 'The shared demo request budget is temporarily exhausted. Please try later.', 429)

    def ready(self):
        with self.lock:
            return self._one('SELECT version FROM fluo_schema WHERE singleton=TRUE')[0] == 1

    def close(self):
        self.pool.close()


def migrate(dsn):
    """Explicit deployment operation; never imports local SQLite state."""
    from psycopg import connect
    with connect(dsn, **connection_options(dsn)) as connection:
        connection.execute('SELECT pg_advisory_xact_lock(20261025, 3)')
        connection.execute((Path(__file__).parent / 'migrations/001_postgres.sql').read_text())

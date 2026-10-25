"""Real PostgreSQL integration suite. Set FLUO_TEST_POSTGRES_URL explicitly."""
import copy
import os
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.auth import GuestAccess, GuestSettings, token_digest
from backend.postgres_store import PostgresStore, migrate
from backend.service import ReplayService
from backend.service_errors import DomainError
from backend.schemas import ReviewUpdate
from tests.test_guest_security import test_two_guests_and_anonymous_have_no_cross_object_access as ownership_check
from tests.test_guest_security import test_public_cookie_capabilities_docs_and_headers as public_check

DSN = os.environ.get('FLUO_TEST_POSTGRES_URL')
pytestmark = pytest.mark.skipif(not DSN, reason='Real PostgreSQL test URL must be provided explicitly')


def ensure_schema():
    if os.environ.get('FLUO_TEST_POSTGRES_PREMIGRATED') != '1':
        migrate(DSN)


def test_postgres_store_without_research_files():
    ensure_schema()
    store = PostgresStore(DSN)
    access = GuestAccess(store, GuestSettings())
    _, owner = access.create()
    session = store.create('normal', 5, owner['digest'])
    store.save_review(session['id'], 'EV-CI', {'revision': 1, 'note': 'Synthetic CI store test'})
    peer = PostgresStore(DSN)
    assert peer.owns_session(owner['digest'], session['id'])
    assert peer.review(session['id'], 'EV-CI')['revision'] == 1
    with pytest.raises(DomainError, match='changed'):
        peer.save_review(session['id'], 'EV-CI', {'revision': 1})
    peer.save_preferences(session['id'], {'warning_sound': True})
    assert store.preferences(session['id'])['warning_sound'] is True
    peer.revoke_guest(owner['digest'])
    access.create()
    assert peer.session(session['id']) is None
    peer.close()
    store.close()


@pytest.fixture(scope='module')
def service(tmp_path_factory):
    ensure_schema()
    result = ReplayService(db_path=tmp_path_factory.mktemp('pg-science') / 'unused.sqlite3')
    result.store.close()
    result.store = PostgresStore(DSN)
    yield result
    result.store.close()


def test_real_postgres_ownership_all_json_pdf_html_routes(service):
    ownership_check(service)


def test_real_postgres_public_cookie_headers_capabilities(service):
    public_check(service)


def test_real_postgres_two_instances_atomic_review_and_persistence(service):
    settings = GuestSettings()
    token, owner = GuestAccess(service.store, settings).create()
    session = service.create('return-diversion', owner['digest'])
    state = service.snapshot(session['id'])
    event = state['events'][0]['id']
    peer = copy.copy(service)
    peer.store = PostgresStore(DSN)
    update = ReviewUpdate(checked_steps=[], note='Actual PostgreSQL concurrent review', revision=0)

    def save(instance):
        try:
            instance.update_review(session['id'], event, update)
            return 200
        except DomainError as error:
            return error.status

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(save, [service, peer])) == [200, 409]
    peer.store.save_preferences(session['id'], {'warning_sound': True})
    peer.store.close()
    reopened = PostgresStore(DSN)
    assert reopened.owns_session(token_digest(token), session['id'])
    assert reopened.review(session['id'], event)['revision'] == 1
    assert reopened.preferences(session['id']) == {'warning_sound': True}
    reopened.close()


def test_real_postgres_csrf_expiry_logout_and_cleanup(service):
    with TestClient(create_app(service)) as client:
        value = client.post('/api/v1/auth/guest', headers={'X-Fluo-Intent': 'guest'})
        csrf = value.json()['csrf_token']
        cookie = client.cookies.get('fluo_guest')
        assert client.post('/api/v1/sessions', json={}).status_code == 403
        client.headers['X-CSRF-Token'] = csrf
        state = client.post('/api/v1/sessions', json={}).json()
        assert client.post('/api/v1/auth/logout').status_code == 204
        client.cookies.set('fluo_guest', cookie, domain='testserver.local', path='/')
        assert client.get('/api/v1/auth/session').status_code == 401
        client.cookies.clear()
        assert client.get('/api/v1/auth/session', headers={'X-User': 'admin'}).status_code == 401
        access = GuestAccess(service.store, GuestSettings(ttl_seconds=-1))
        expired, owner = access.create()
        service.store.create('normal', 0, owner['digest'])
        client.cookies.set('fluo_guest', expired, domain='testserver.local', path='/')
        assert client.get('/api/v1/auth/session').status_code == 401
        access.create()
        assert service.store.guest(owner['digest']) is None
        assert service.store.session(state['session_id']) is None


def test_real_postgres_quotas_and_shared_rate_budget(service):
    _, owner = GuestAccess(service.store, GuestSettings()).create()
    service.store.create('normal', 0, owner['digest'], 1)
    peer = PostgresStore(DSN)
    with pytest.raises(DomainError, match='session limit'):
        peer.create('normal', 0, owner['digest'], 1)
    service.store.consume_guest_mutation(owner['digest'], 1)
    with pytest.raises(DomainError, match='action limit'):
        peer.consume_guest_mutation(owner['digest'], 1)
    # Saturate only this explicit disposable test database's global minute bucket.
    now = int(time.time())
    with service.store.lock:
        service.store._query('INSERT INTO fluo_budgets VALUES(%s,%s,%s,%s) ON CONFLICT(name,period) DO UPDATE SET hits=EXCLUDED.hits', ('minute', now // 60, 1200, now + 7200))
    try:
        with pytest.raises(DomainError, match='budget'):
            peer.consume_request_budget()
    finally:
        with service.store.lock:
            service.store._query('DELETE FROM fluo_budgets WHERE name=%s AND period=%s', ('minute', now // 60))
        peer.close()

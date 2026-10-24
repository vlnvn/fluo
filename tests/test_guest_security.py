import sqlite3

import pytest
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.auth import GuestAccess, GuestSettings, token_digest
from backend.service import ReplayService
from backend.service_errors import DomainError
from backend.store import Store


@pytest.fixture(scope='module')
def service(tmp_path_factory):
    result = ReplayService(db_path=tmp_path_factory.mktemp('guest-security') / 'state.sqlite3')
    yield result
    result.store.close()


def entry(client):
    result = client.post('/api/v1/auth/guest', headers={'X-Fluo-Intent':'guest'})
    assert result.status_code == 200
    client.headers['X-CSRF-Token'] = result.json()['csrf_token']
    return result


def create(client):
    response = client.post('/api/v1/sessions', json={})
    assert response.status_code == 201
    return response.json()


def test_two_guests_and_anonymous_have_no_cross_object_access(service):
    app = create_app(service)
    with TestClient(app) as a, TestClient(app) as b, TestClient(app) as anonymous:
        entry(a)
        entry(b)
        first, second = create(a), create(b)
        sid = first['session_id']
        paths = [f'/sessions/{sid}', f'/sessions/{sid}/preview?cursor=0', f'/sessions/{sid}/events?search=EV&order=asc', f'/sessions/{sid}/preferences']
        for event in first['events'][:4]:
            paths += [f'/sessions/{sid}/events/{event["id"]}{suffix}' for suffix in ['', '/report.pdf', '/print', '/print?embedded=true']]
        for path in paths:
            assert a.get('/api/v1' + path).status_code == 200
            assert b.get('/api/v1' + path).status_code == 404
            assert anonymous.get('/api/v1' + path).status_code == 401
        event = first['events'][0]['id']
        for method, suffix, body in [('post','replay',{'action':'seek','cursor':0}), ('put','preferences',{'warning_sound':True}), ('put',f'events/{event}/review',{'checked_steps':[],'note':'forbidden','revision':0}), ('post',f'events/{event}/review/submit',{'checked_steps':[],'note':'forbidden','revision':0})]:
            assert getattr(b, method)(f'/api/v1/sessions/{sid}/{suffix}', json=body).status_code == 404
        assert a.get(f'/api/v1/sessions/{sid}').json()['cursor'] == first['cursor']
        assert b.get(f'/api/v1/sessions/{second["session_id"]}').status_code == 200
        assert anonymous.get('/api/v1/scenarios', headers={'X-User':'admin','X-Guest-ID':'forged'}).status_code == 401


def test_csrf_logout_expiry_and_forgery(service):
    app = create_app(service)
    with TestClient(app) as client:
        assert client.post('/api/v1/auth/guest').status_code == 403
        entry(client)
        state = create(client)
        saved_cookie = client.cookies.get('fluo_guest')
        assert client.post('/api/v1/sessions', json={}, headers={'X-CSRF-Token':'wrong'}).status_code == 403
        assert client.post('/api/v1/sessions', json={}, headers={'Origin':'https://evil.invalid'}).status_code == 403
        assert client.post('/api/v1/auth/logout').status_code == 204
        client.cookies.set('fluo_guest', saved_cookie, domain='testserver.local', path='/')
        assert client.get('/api/v1/auth/session').status_code == 401
        entry(client)
        assert client.get(f'/api/v1/sessions/{state["session_id"]}').status_code == 404
        current = client.cookies.get('fluo_guest')
        with service.store.lock, service.store.db:
            service.store.db.execute('UPDATE guest_principals SET expires=0 WHERE digest=?', (token_digest(current),))
        assert client.get('/api/v1/auth/session').status_code == 401
        client.cookies.clear()
        client.cookies.set('fluo_guest','x' * 43)
        assert client.get('/api/v1/auth/session').status_code == 401


def test_public_cookie_capabilities_docs_and_headers(service):
    settings = GuestSettings(public=True, public_origin='https://demo.example')
    with TestClient(create_app(service, settings), base_url='https://demo.example') as client:
        response = entry(client)
        cookie = response.headers['set-cookie']
        assert cookie.startswith('__Host-fluo_guest=') and 'HttpOnly' in cookie and 'Secure' in cookie and 'SameSite=strict' in cookie
        assert 'Domain=' not in cookie and 'Path=/' in cookie
        assert 'csrf_token' in response.json() and 'token' not in response.json()
        assert client.post('/api/v1/inference', json={}).status_code == 403
        assert client.get('/api/v1/health').headers['strict-transport-security'] == 'max-age=31536000'
        for path in ['/docs','/redoc','/openapi.json','/.git/config','/.env','/models/fluo_hgb_synthetic_v2.joblib','/data/original/fluo_sensor_stream.csv.gz']:
            assert client.get(path).status_code == 404
        assert client.get('/health/ready').json() == {'status':'ready','model_loaded':True}


def test_guest_limits_cleanup_and_persistence(tmp_path):
    path = tmp_path / 'quota.sqlite3'
    store = Store(path)
    settings = GuestSettings(max_guests=2, mutations_per_guest=2)
    access = GuestAccess(store, settings)
    token, owner = access.create()
    access.create()
    with pytest.raises(DomainError, match='capacity'):
        access.create()
    store.consume_guest_mutation(owner['digest'], 2)
    store.consume_guest_mutation(owner['digest'], 2)
    with pytest.raises(DomainError, match='action limit'):
        store.consume_guest_mutation(owner['digest'], 2)
    session = store.create('normal',0)
    store.claim_session(owner['digest'], session['id'],1)
    store.save_review(session['id'],'EV-001',{'revision':1,'note':'private retained state'})
    store.close()
    reopened = Store(path)
    assert reopened.guest(token_digest(token)) and reopened.owns_session(owner['digest'],session['id'])
    backup = tmp_path / 'backup.sqlite3'
    reopened.backup(backup)
    reopened.revoke_guest(owner['digest'])
    GuestAccess(reopened,settings).create()
    assert reopened.session(session['id']) is None and reopened.review(session['id'],'EV-001') is None
    reopened.close()
    with sqlite3.connect(backup) as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert db.execute('SELECT COUNT(*) FROM session_owners').fetchone()[0] == 1

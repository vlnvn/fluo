import re
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.security import LocalBoundary, assert_local_release
from backend.service import ReplayService
from backend.store import Store


@pytest.fixture(scope='module')
def audit_service(tmp_path_factory):
    value = ReplayService(db_path=tmp_path_factory.mktemp('audit') / 'audit.sqlite3')
    yield value
    value.store.close()


@pytest.fixture
def api(audit_service):
    with TestClient(create_app(audit_service), raise_server_exceptions=False) as value:
        yield value


def make_session(api):
    return api.post('/api/v1/sessions', json={}).json()


def test_preview_has_exact_frames_without_mutating_clock_or_rescoring(api, audit_service, monkeypatch):
    state = make_session(api)
    sid = state['session_id']
    stored = audit_service.store.session(sid)
    monkeypatch.setattr('backend.service.score_telemetry', lambda *args: pytest.fail('Unexpected rescoring'))
    for cursor in [0, 30, state['scenario']['total_frames'] - 1, 8]:
        preview = api.get(f'/api/v1/sessions/{sid}/preview?cursor={cursor}').json()
        assert preview['is_preview'] and preview['cursor'] == cursor
        assert all(e['timestamp'] <= preview['current']['timestamp'] for e in preview['events'])
        assert audit_service.store.session(sid) == stored
        committed = api.post(f'/api/v1/sessions/{sid}/replay', json={'action': 'seek', 'cursor': cursor}).json()
        assert committed['current'] == preview['current'] and committed['frames'] == preview['frames']
        api.post(f'/api/v1/sessions/{sid}/replay', json={'action': 'seek', 'cursor': state['cursor']})
        # Compare immutable clock data after returning to the baseline cursor.
        stored = audit_service.store.session(sid)
    assert api.get(f'/api/v1/sessions/{sid}/preview?cursor=999999').status_code == 400
    assert api.get(f'/api/v1/sessions/{sid}/preview?cursor=-1').status_code == 422


def test_request_boundary_limits_chunked_body_rate_origin_and_host():
    app = FastAPI()
    app.add_middleware(LocalBoundary, max_body=32, rate_limit=2, allow_test_host=True)

    @app.post('/api/write')
    async def write():
        return {'ok': True}

    with TestClient(app) as client:
        assert client.post('/api/write', content=(b'x' * 20 for _ in range(2))).status_code == 413
        assert client.post('/api/write').status_code == 200
        assert client.post('/api/write').status_code == 429
        assert client.post('/api/write', headers={'Origin': 'https://attacker.invalid'}).status_code == 403
        assert client.get('/', headers={'Host': 'attacker.invalid'}).status_code == 400


def test_headers_report_nonce_liveness_and_safe_errors(api, audit_service, monkeypatch):
    state = make_session(api)
    sid, event = state['session_id'], state['events'][0]['id']
    report = api.get(f'/api/v1/sessions/{sid}/events/{event}/print?embedded=true')
    nonce = re.search(r'<script nonce="([^"]+)"', report.text).group(1)
    assert f"'nonce-{nonce}'" in report.headers['content-security-policy']
    assert report.headers['x-frame-options'] == 'SAMEORIGIN'
    assert report.headers['x-content-type-options'] == 'nosniff'
    assert api.get('/health/live').json() == {'status': 'alive'}
    assert api.get('/health/ready').json()['status'] == 'ready'
    monkeypatch.setattr(audit_service, 'snapshot', lambda *args: (_ for _ in ()).throw(RuntimeError('private filesystem path')))
    result = api.get(f'/api/v1/sessions/{sid}')
    assert result.status_code == 500 and result.json()['error']['code'] == 'INTERNAL_ERROR'
    assert 'private filesystem' not in result.text


def test_concurrent_review_revision_conflict_is_atomic(api):
    state = make_session(api)
    path = f'/api/v1/sessions/{state["session_id"]}/events/{state["events"][0]["id"]}/review'
    update = {'checked_steps': [], 'note': 'Concurrent review test', 'revision': 0}
    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(lambda _: api.put(path, json=update).status_code, range(2)))
    assert sorted(statuses) == [200, 409]


def test_database_backup_reopen_and_revision_survive_restart(tmp_path):
    source = tmp_path / 'source.sqlite3'
    backup = tmp_path / 'backup.sqlite3'
    store = Store(source)
    session = store.create('normal', 5)
    store.save_review(session['id'], 'EV-001', {'revision': 2, 'note': 'Saved before restart'})
    store.backup(backup)
    store.close()
    for path in [source, backup]:
        reopened = Store(path)
        assert reopened.session(session['id'])['cursor'] == 5
        assert reopened.review(session['id'], 'EV-001')['revision'] == 2
        assert reopened.db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        reopened.close()
    import sqlite3
    with sqlite3.connect(source) as connection:
        connection.execute('PRAGMA user_version=2')
    with pytest.raises(RuntimeError, match='DB_SCHEMA_UNSUPPORTED'):
        Store(source)


def test_public_release_mode_fails_closed(monkeypatch):
    monkeypatch.setenv('FLUO_RELEASE_MODE', 'staging')
    with pytest.raises(RuntimeError, match='BLOCKED_FOR_PUBLIC_ACCESS'):
        assert_local_release()


def test_corrupt_runtime_dataset_fails_before_inference(tmp_path):
    (tmp_path / 'fluo_sensor_stream.csv.gz').write_bytes(b'not the audited stream')
    with pytest.raises(RuntimeError, match='DATASET_MISMATCH'):
        ReplayService(data_dir=tmp_path, db_path=tmp_path / 'unused.sqlite3')


@pytest.mark.xfail(strict=True, reason='Release blocker: local prototype has no server-side identity/ownership; never expose publicly')
def test_anonymous_client_cannot_read_another_session(api, audit_service):
    state = make_session(api)
    with TestClient(create_app(audit_service)) as anonymous:
        assert anonymous.get(f'/api/v1/sessions/{state["session_id"]}').status_code in (401, 403, 404)

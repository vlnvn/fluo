import io
import time

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader

from backend.app import create_app
from backend.inference_adapter import FrozenEstimator, score_telemetry
from backend.service import ReplayService
from run_fluo_v2 import inference


@pytest.fixture(scope='module')
def service(tmp_path_factory):
    return ReplayService(db_path=tmp_path_factory.mktemp('db') / 'test.sqlite3')


@pytest.fixture
def client(service):
    with TestClient(create_app(service)) as api:
        identity = api.post('/api/v1/auth/guest', headers={'X-Fluo-Intent':'guest'}).json()
        api.headers['X-CSRF-Token'] = identity['csrf_token']
        yield api


def session(client):
    result = client.post('/api/v1/sessions', json={})
    assert result.status_code == 201, result.text
    return result.json()


def command(client, state, **data):
    response = client.post(f'/api/v1/sessions/{state["session_id"]}/replay', json=data)
    assert response.status_code == 200, response.text
    return response.json()


def test_health_model_and_provenance(client):
    response = client.get('/api/v1/health')
    assert response.status_code == 200
    assert response.headers['x-correlation-id']
    health = response.json()
    assert health['model_loaded'] and not health['training_performed']
    assert not health['lineage']['field_validation']
    assert health['lineage']['source_kind'] == 'simulated research telemetry'


def test_adapter_exact_parity_and_zero_valid_prefix(service):
    source = service.sensor[service.sensor.site_id.eq('CFG_B')].head(1000)
    reference = inference(source, service.model.model)
    result = score_telemetry(source, service.model)
    pd.testing.assert_frame_equal(reference, result, check_exact=True)
    result = score_telemetry(source.head(20), service.model)
    assert result.gb_signature_score.isna().all()
    assert not result.gb_signature_warning.any()


def test_corrupt_artifact_rejected_before_load(tmp_path):
    bad = tmp_path / 'bad.joblib'
    bad.write_bytes(b'not a trusted pickle')
    with pytest.raises(RuntimeError, match='ARTIFACT_MISMATCH'):
        FrozenEstimator(bad)


def test_scenarios_have_original_timestamps_and_no_oracle(client):
    scenarios = client.get('/api/v1/scenarios').json()
    assert len(scenarios) == 9
    assert {s['id'] for s in scenarios} >= {'normal','return-diversion','return-pipe-loss','trap-blowthrough','return-meter-bias','transport-delay','connection-outage'}
    state = session(client)
    assert state['current']['inference']['warning']
    assert state['current']['inference']['score'] > .90
    assert state['current']['inference']['auto_actuation_allowed'] is False
    assert state['current']['inference']['recovery_eligibility'] == 'UNKNOWN_REQUIRES_SITE_ASSESSMENT'
    assert all(f['minute_id'] <= state['current']['minute_id'] for f in state['frames'])
    assert not {'event_type','event_group','true_loss','oracle'} & set(state['current'])


def test_pause_play_reset_seek_and_speed(client):
    state = session(client)
    state = command(client, state, action='reset')
    assert state['cursor'] == 0 and state['playback'] == 'PAUSED'
    state = command(client, state, action='play')
    time.sleep(1.1)
    state = command(client, state, action='pause')
    assert state['cursor'] >= 1
    frozen = state['cursor']
    time.sleep(.1)
    assert client.get(f'/api/v1/sessions/{state["session_id"]}').json()['cursor'] == frozen
    first = command(client, state, action='seek', cursor=70)
    command(client, state, action='seek', cursor=10)
    second = command(client, state, action='seek', cursor=70)
    assert first['current'] == second['current'] and first['frames'] == second['frames']
    assert command(client, state, action='speed', speed=2)['speed'] == 2
    assert command(client, state, action='rewind')['cursor'] == 60
    assert command(client, state, action='forward')['cursor'] == 70
    last = state['scenario']['total_frames'] - 1
    command(client, state, action='seek', cursor=last - 2)
    assert command(client, state, action='forward')['cursor'] == last
    command(client, state, action='reset')
    assert command(client, state, action='rewind')['cursor'] == 0


@pytest.mark.parametrize('scenario_id', ['normal','return-meter-bias','transport-delay','connection-outage','meter-dropout','mode-change'])
def test_scenario_switch_resets_and_quality_gates(client, scenario_id):
    state = command(client, session(client), action='scenario', scenario_id=scenario_id)
    assert state['cursor'] == 0 and state['playback'] == 'PAUSED'
    for cursor in [0, min(50, state['scenario']['total_frames'] - 1), state['scenario']['total_frames'] - 1]:
        sample = command(client, state, action='seek', cursor=cursor)
        for frame in sample['frames']:
            if frame['quality_action'] != 'SCORE_ALLOWED':
                assert not frame['inference']['warning']
                assert frame['inference']['score'] is None


def test_events_filter_four_reports_reviews_and_isolation(client):
    state = session(client)
    sid = state['session_id']
    all_events = client.get(f'/api/v1/sessions/{sid}/events').json()
    assert len(all_events) >= 4
    for category in ['return','quality']:
        filtered = client.get(f'/api/v1/sessions/{sid}/events?category={category}').json()
        assert all(e['category'] == category for e in filtered)
    checked_id = all_events[0]['id']
    for event in all_events[:4]:
        url = f'/api/v1/sessions/{sid}/events/{event["id"]}'
        detail = client.get(url).json()
        assert detail['event']['id'] == event['id']
        assert len(detail['review']['steps']) == 4
        assert detail['frame']['minute_id'] == event['minute_id']
        pdf = client.get(url + '/report.pdf')
        assert pdf.status_code == 200 and pdf.content.startswith(b'%PDF-')
        reader = PdfReader(io.BytesIO(pdf.content))
        text = '\n'.join(page.extract_text() for page in reader.pages)
        assert event['id'] in text and event['timestamp'] in text
        assert 'simulated research telemetry' in text.lower()
        assert 'Guest operator (unverified)' in text
        assert abs(float(reader.pages[0].mediabox.width) - 595.2756) < 1
        assert abs(float(reader.pages[0].mediabox.height) - 841.8898) < 1
    path = f'/api/v1/sessions/{sid}/events/{checked_id}/review'
    review = client.get(f'/api/v1/sessions/{sid}/events/{checked_id}').json()['review']
    update = {'checked_steps': [review['steps'][0]['step_id']], 'note': '<script>unsafe</script> inspected locally', 'revision': 0}
    draft = client.put(path, json=update).json()
    assert draft['status'] == 'draft' and draft['steps'][0]['checked']
    assert client.put(path, json=update).status_code == 409
    update['revision'] = draft['revision']
    submitted = client.post(path + '/submit', json=update).json()
    assert submitted['status'] == 'submitted' and len(submitted['audit']) == 2
    saved = client.get(f'/api/v1/sessions/{sid}/events/{checked_id}').json()
    assert saved['review'] == submitted
    assert saved['event']['state'] == 'Investigate — unconfirmed'
    assert not saved['frame']['inference']['auto_actuation_allowed']
    html = client.get(f'/api/v1/sessions/{sid}/events/{checked_id}/print').text
    assert '&lt;script&gt;unsafe&lt;/script&gt;' in html
    assert 'window.print()' in html and '@page{size:A4' in html
    other = session(client)
    isolated = client.get(f'/api/v1/sessions/{other["session_id"]}/events/{checked_id}').json()
    assert isolated['review']['revision'] == 0


def test_preferences_persist_and_no_actuation_routes(client):
    state = session(client)
    path = f'/api/v1/sessions/{state["session_id"]}/preferences'
    assert client.get(path).json()['warning_sound'] is False
    assert client.put(path, json={'warning_sound': True}).status_code == 200
    assert client.get(path).json()['warning_sound'] is True
    assert client.get('/openapi.json').status_code == 404
    schema = client.app.openapi()
    assert not any('valve' in route or 'boiler' in route for route in schema['paths'])


def test_schema_errors_and_sensor_only_inference(client, service):
    row = service.sensor.iloc[0].replace({np.nan: None}).to_dict()
    assert client.post('/api/v1/inference', json={'rows':[row]}).status_code == 200
    for extra in ['event_type','true_loss','event_id']:
        rejected = client.post('/api/v1/inference', json={'rows':[{**row, extra:'oracle'}]})
        assert rejected.status_code == 422 and rejected.json()['error']['code'] == 'INVALID_SCHEMA'
    negative = {**row, 'steam_flow_obs_kg_h': -1}
    assert client.post('/api/v1/inference', json={'rows':[negative]}).status_code == 422
    assert client.post('/api/v1/inference', json={'rows':[row], 'run_mode':'FIELD_DEPLOYMENT'}).status_code == 422
    assert client.get('/api/v1/sessions/not-real').status_code == 404
    state = session(client)
    assert client.post(f'/api/v1/sessions/{state["session_id"]}/replay', json={'action':'seek','cursor':1000000}).status_code == 400
    assert client.post(f'/api/v1/sessions/{state["session_id"]}/replay', json={'action':'scenario','scenario_id':'not-real'}).status_code == 404

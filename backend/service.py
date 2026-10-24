"""Deterministic scenario windows and state-change events from scored telemetry."""
import hashlib
import math
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from .inference_adapter import ROOT, MODEL_SHA, FrozenEstimator, persistence_counts, score_telemetry
from .store import Store
from .service_errors import DomainError

SOURCE_KIND = 'simulated research telemetry'
LIMITATIONS = [
    'Synthetic research replay; no measurements from a verified textile factory.',
    'Signature score is uncalibrated and does not establish physical loss or fault location.',
    'Meter under-reading, transport lag and physical return deficit may be indistinguishable.',
    'Recovery eligibility is not established: quality tests, site assessment and engineer authorization are required.',
    'Read-only software: automatic actuation is disabled.',
]
LABELS = {
    'GATEWAY_OFFLINE': 'Connection unavailable',
    'VERIFY_RETURN_METER': 'Return meter interrupted',
    'NONPRODUCTION_MONITORING_ONLY': 'Process conditions changed',
    'MODE_STABILIZATION': 'Mode stabilization',
    'INSUFFICIENT_VALID_HISTORY': 'Rebuilding valid history',
    'SCORE_ALLOWED': 'Data connection restored',
}
STEPS = {
    'return': [
        ('timestamp-mode', 'Confirm timestamp and mode transitions'),
        ('meter-calibration', 'Compare steam and return meter calibration'),
        ('return-routing', 'Inspect condensate routing and steam trap'),
        ('field-evidence', 'Record field evidence before classifying cause'),
    ],
    'quality': [
        ('timestamp-mode', 'Confirm timestamp and operating mode'),
        ('connection-history', 'Check gateway connection and valid history'),
        ('sensor-readings', 'Verify meter availability and calibration'),
        ('field-evidence', 'Record evidence before resuming interpretation'),
    ],
}



def finite(value):
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (np.floating, float)):
        return float(value) if math.isfinite(value) else None
    return value


class ReplayService:
    def __init__(self, data_dir=None, db_path=None):
        self.data_dir = Path(data_dir or os.environ.get('FLUO_DATA_DIR', ROOT / 'data/original'))
        sensor_file = self.data_dir / 'fluo_sensor_stream.csv.gz'
        if not sensor_file.exists():
            raise RuntimeError('DATA_UNAVAILABLE: run python tools/prepare_runtime.py with the supplied archive')
        self.model = FrozenEstimator()
        self.dataset_sha = hashlib.sha256(sensor_file.read_bytes()).hexdigest()
        if self.dataset_sha != 'f9fe34bf04a31e753df47c6f736f5155a4eaf34a8a6dedf7b6b5a53ed00ce018':
            raise RuntimeError('DATASET_MISMATCH: audited sensor stream checksum failed')
        if hashlib.sha256((self.data_dir / 'fluo_episode_labels.csv').read_bytes()).hexdigest() != 'e5b1368942a98452abd8b49e3c93d154b0d07614d33e99ec4e755a8e45611106':
            raise RuntimeError('DATASET_MISMATCH: audited scenario catalog checksum failed')
        self.sensor = pd.read_csv(sensor_file)
        self.predictions = score_telemetry(self.sensor, self.model)
        self.predictions['persistence_hits'] = persistence_counts(self.predictions)
        self.sites = {}
        self.events = {}
        self.event_lookup = {}
        for site, raw in self.sensor.groupby('site_id', sort=True):
            raw = raw.sort_values('minute_id').reset_index(drop=True)
            pred = self.predictions[self.predictions.site_id.eq(site)].sort_values('minute_id').reset_index(drop=True)
            self.sites[site] = (raw, pred)
            self.events[site] = self._events(site, pred)
            self.event_lookup.update({e['id']: e for e in self.events[site]})
        self.scenarios = self._scenarios()
        self.store = Store(db_path or os.environ.get('FLUO_DB_PATH', ROOT / '.local/fluo.sqlite3'))
        self.lineage = {
            'model_sha256': MODEL_SHA, 'dataset_sha256': self.dataset_sha,
            'model': 'HistGradientBoostingClassifier / frozen synthetic deficit signature',
            'source_kind': SOURCE_KIND, 'sample_period_seconds': 60,
            'replay_seconds_per_sample_at_1x': 1, 'field_validation': False, 'facility_is_fictional': True,
        }

    def _events(self, site, pred):
        events = []
        active = None
        previous = None
        for index, row in enumerate(pred.itertuples()):
            state = 'RETURN_DEFICIT_UNCONFIRMED' if row.gb_signature_warning else row.quality_action
            if state != previous:
                if active is not None:
                    active['_end'] = index - 1
                    active['end_timestamp'] = str(pred.iloc[index - 1].timestamp)
                    active['duration_min'] = index - active['_start']
                category = 'return' if row.gb_signature_warning else 'quality'
                # Do not turn the first warmup sample or every ordinary monitor row into an event.
                meaningful = state == 'RETURN_DEFICIT_UNCONFIRMED' or (previous is not None and (state != 'SCORE_ALLOWED' or previous in ('GATEWAY_OFFLINE', 'VERIFY_RETURN_METER', 'INSUFFICIENT_VALID_HISTORY')))
                if meaningful:
                    number = len(events) + 1
                    event_id = f'EV-{number:03d}' if site == 'CFG_B' else f'EV-{site.removeprefix("CFG_")}-{number:03d}'
                    active = {
                        'id': event_id, 'site_id': site, 'timestamp': str(row.timestamp),
                        'end_timestamp': str(row.timestamp), 'category': category,
                        'title': 'Return-flow deviation' if category == 'return' else LABELS.get(state, 'Sensor check'),
                        'state': 'Investigate — unconfirmed' if category == 'return' else ('Monitoring restored' if state == 'SCORE_ALLOWED' else 'Data / mode check'),
                        'duration_min': 1, 'minute_id': int(row.minute_id), 'peak_score': finite(row.gb_signature_score),
                        'evidence': [f'Process: {row.operating_mode}', f'Connectivity: {"online" if row.link_online else "offline"}', f'Quality: {row.quality_action}', f'Persistence: {int(row.persistence_hits)} of 10 samples'],
                        'review_status': 'pending', '_start': index, '_end': index, '_quality': row.quality_action,
                    }
                    events.append(active)
                else:
                    active = None
                previous = state
            if active is not None:
                active['_end'] = index
                active['end_timestamp'] = str(row.timestamp)
                active['duration_min'] = index - active['_start'] + 1
                score = finite(row.gb_signature_score)
                if score is not None:
                    active['peak_score'] = max(active['peak_score'] or 0, score)
        return events

    def _scenarios(self):
        # Read annotations only for selecting documented experiment windows.
        # The scored frames/events above never read or join these annotations.
        labels = pd.read_csv(self.data_dir / 'fluo_episode_labels.csv')
        definitions = [
            ('normal', 'Normal operation', 'REFERENCE', None),
            ('return-diversion', 'Return diversion', 'PHYSICAL', 'diversion_to_pit'),
            ('return-pipe-loss', 'Return pipe loss', 'PHYSICAL', 'return_pipe_loss'),
            ('trap-blowthrough', 'Trap blowthrough', 'PHYSICAL', 'trap_blowthrough'),
            ('return-meter-bias', 'Return meter bias', 'INSTRUMENT', 'return_meter_bias'),
            ('transport-delay', 'Transport delay shift', 'PROCESS', 'transport_delay_shift'),
            ('connection-outage', 'Connection outage', 'DATA', 'network_outage'),
            ('meter-dropout', 'Return meter interruption', 'DATA', 'return_meter_dropout'),
            ('mode-change', 'Mode transition', 'PROCESS', 'mode-transition'),
        ]
        result = {}
        for scenario_id, name, group, injected in definitions:
            site = 'CFG_B'
            raw, pred = self.sites[site]
            if injected is None:
                start, end = 8 * 60 + 60, 8 * 60 + 60 + 180
            elif injected == 'mode-transition':
                changes = raw.operating_mode.ne(raw.operating_mode.shift()) & raw.index.to_series().gt(500)
                center = int(np.flatnonzero(changes)[0])
                start, end = center - 35, center + 100
            else:
                matches = labels[labels.event_type.eq(injected)]
                preferred = matches[matches.site_id.eq(site)]
                if not len(matches):
                    continue
                episode = (preferred if len(preferred) else matches).iloc[0]
                site = str(episode.site_id)
                raw, pred = self.sites[site]
                center = int(np.flatnonzero(raw.timestamp.eq(episode.start_timestamp))[0])
                start = max(0, center - 45)
                end = min(len(raw) - 1, center + int(episode.duration_min) + 35)
            end = min(end, len(raw) - 1)
            default = min(end - start, 50)
            if scenario_id == 'return-diversion':
                hits = np.flatnonzero(pred.iloc[start:end + 1].gb_signature_warning.to_numpy())
                default = min(int(hits[0]) + 3, end - start) if len(hits) else default
            result[scenario_id] = {
                'id': scenario_id, 'name': name, 'group': group, 'description': 'Recorded simulator experiment setup; the detector does not diagnose the injected cause.',
                'site_id': site, 'start_timestamp': str(raw.iloc[start].timestamp), 'end_timestamp': str(raw.iloc[end].timestamp),
                'total_frames': end - start + 1, 'default_cursor': default, 'source_kind': SOURCE_KIND,
                'setup_is_not_diagnosis': True, '_start': start, '_end': end,
            }
        return result

    @staticmethod
    def public(data):
        return {k: v for k, v in data.items() if not k.startswith('_')}

    def scenario(self, scenario_id):
        if scenario_id not in self.scenarios:
            raise DomainError('UNKNOWN_SCENARIO', 'The requested replay scenario does not exist.', 404)
        return self.scenarios[scenario_id]

    def session(self, session_id):
        session = self.store.session(session_id)
        if not session:
            raise DomainError('UNKNOWN_SESSION', 'Replay session not found. Start a new local session.', 404)
        return session

    def position(self, session):
        maximum = self.scenario(session['scenario_id'])['total_frames'] - 1
        cursor = session['cursor']
        if session['playing']:
            cursor += int(max(0, time.time() - session['anchor']) * session['speed'])
        return min(cursor, maximum)

    def create(self, scenario_id, owner_digest=None, maximum=5):
        scenario = self.scenario(scenario_id)
        return self.store.create(scenario_id, scenario['default_cursor'], owner_digest, maximum)

    def command(self, session_id, command):
        with self.store.lock:
            session = self.session(session_id)
            cursor = self.position(session)
            action = command.action
            if action == 'scenario':
                if not command.scenario_id:
                    raise DomainError('INVALID_COMMAND', 'scenario_id is required')
                self.scenario(command.scenario_id)
                session.update(scenario_id=command.scenario_id, playing=False)
                cursor = 0
            elif action == 'seek':
                if command.cursor is None or command.cursor >= self.scenario(session['scenario_id'])['total_frames']:
                    raise DomainError('INVALID_CURSOR', 'Cursor is outside this recorded scenario')
                cursor = command.cursor
            elif action == 'reset':
                cursor = 0
                session['playing'] = False
            elif action == 'rewind':
                cursor = max(0, cursor - 10)
            elif action == 'forward':
                cursor = min(self.scenario(session['scenario_id'])['total_frames'] - 1, cursor + 10)
            elif action == 'play':
                if cursor >= self.scenario(session['scenario_id'])['total_frames'] - 1:
                    raise DomainError('REPLAY_ENDED', 'Reset or rewind before playing again', 409)
                session['playing'] = True
            elif action == 'pause':
                session['playing'] = False
            elif action == 'speed':
                if command.speed is None:
                    raise DomainError('INVALID_COMMAND', 'speed must be 1 or 2')
                session['speed'] = command.speed
            session.update(cursor=cursor, anchor=time.time())
            self.store.save_session(session)
        return self.snapshot(session_id)

    def frame(self, site, index):
        raw, pred = self.sites[site]
        measured, scored = raw.iloc[index], pred.iloc[index]
        return {
            'timestamp': str(scored.timestamp), 'minute_id': int(scored.minute_id), 'site_id': site,
            'operating_mode': str(scored.operating_mode), 'link_online': bool(scored.link_online),
            'data_quality_flag': str(scored.data_quality_flag), 'quality_action': str(scored.quality_action),
            'readings': {'steam_kg_h': finite(scored.steam_flow_obs_kg_h), 'return_kg_h': finite(scored.condensate_return_obs_kg_h), 'pressure_barg': finite(scored.steam_pressure_obs_barg), 'steam_temperature_C': finite(measured.steam_temperature_obs_C), 'return_temperature_C': finite(scored.return_temperature_obs_C)},
            'inference': {'score': finite(scored.gb_signature_score), 'warning': bool(scored.gb_signature_warning), 'persistence_hits': int(scored.persistence_hits), 'triage_status': str(scored.triage_status), 'score_meaning': str(scored.score_meaning), 'next_safe_action': str(scored.next_safe_action), 'recovery_eligibility': str(scored.recovery_eligibility), 'auto_actuation_allowed': False, 'fixed_ratio_warning': bool(scored.fixed_ratio_warning), 'physics_residual_warning': bool(scored.physics_residual_warning)},
        }

    def visible_event(self, event, absolute, session_id):
        result = self.public(event)
        result['quality_action'] = str(event['_quality'])
        pred = self.sites[event['site_id']][1]
        end = min(absolute, event['_end'])
        result.update(end_timestamp=str(pred.iloc[end].timestamp), duration_min=end - event['_start'] + 1)
        scores = pred.iloc[event['_start']:end + 1].gb_signature_score.dropna()
        result['peak_score'] = float(scores.max()) if len(scores) else None
        review = self.store.review(session_id, event['id'])
        result['review_status'] = review['status'] if review else 'pending'
        return result

    def snapshot(self, session_id, preview_cursor=None):
        session = self.session(session_id)
        scenario = self.scenario(session['scenario_id'])
        cursor = self.position(session) if preview_cursor is None else preview_cursor
        if cursor < 0 or cursor >= scenario['total_frames']:
            raise DomainError('INVALID_CURSOR', 'Cursor is outside this recorded scenario')
        absolute = scenario['_start'] + cursor
        site = scenario['site_id']
        events = [self.visible_event(e, absolute, session_id) for e in self.events[site] if e['_start'] <= absolute][-100:][::-1]
        current = self.frame(site, absolute)
        # Only past samples are sent to charts; immutable inference used complete past history.
        frames = [self.frame(site, i) for i in range(max(scenario['_start'], absolute - 24), absolute + 1)]
        active = next((e for e in events if self.event_lookup[e['id']]['_start'] <= absolute <= self.event_lookup[e['id']]['_end']), None)
        playback = 'ENDED' if cursor == scenario['total_frames'] - 1 else ('PLAYING' if session['playing'] else 'PAUSED')
        return {'schema_version': '1.0', 'is_preview': preview_cursor is not None, 'session_id': session_id, 'scenario': self.public(scenario), 'cursor': cursor, 'speed': session['speed'], 'playback': playback, 'current': current, 'frames': frames, 'events': events, 'active_event_id': active['id'] if active else None, 'lineage': self.lineage, 'review_scope': 'Local SQLite research session; operator identity is unverified.'}

    def detail(self, session_id, event_id):
        state = self.snapshot(session_id)
        event = self.event_lookup.get(event_id)
        scenario = self.scenario(state['scenario']['id'])
        absolute = scenario['_start'] + state['cursor']
        if not event or event['site_id'] != scenario['site_id'] or event['_start'] > absolute:
            raise DomainError('UNKNOWN_EVENT', 'Event is not present in this replay history.', 404)
        point = event['_start']
        end = min(absolute, point + 12)
        context = [self.frame(event['site_id'], i) for i in range(max(0, point - 12), end + 1)]
        return {'event': self.visible_event(event, absolute, session_id), 'frame': self.frame(event['site_id'], point), 'context': context, 'review': self.review(session_id, event), 'lineage': self.lineage, 'limitations': LIMITATIONS}

    def review(self, owner, event):
        saved = self.store.review(owner, event['id'])
        if saved:
            return saved
        return {'event_id': event['id'], 'operator_id': owner, 'operator_label': 'Guest operator (unverified)', 'authenticated': False, 'revision': 0, 'status': 'pending', 'steps': [{'step_id': key, 'label': label, 'checked': False, 'evidence': ''} for key, label in STEPS[event['category']]], 'note': '', 'updated_at': None, 'submitted_at': None, 'audit': []}

    def update_review(self, session_id, event_id, update, submit=False):
        with self.store.lock:
            detail = self.detail(session_id, event_id)
            review = detail['review']
            if update.revision != review['revision']:
                raise DomainError('REVISION_CONFLICT', 'Review changed; reload before saving.', 409)
            allowed = {s['step_id'] for s in review['steps']}
            if len(set(update.checked_steps)) != len(update.checked_steps) or not set(update.checked_steps) <= allowed:
                raise DomainError('INVALID_REVIEW_STEPS', 'Only the four verification steps for this event are accepted.', 422)
            now = datetime.now(timezone.utc).isoformat()
            for step in review['steps']:
                step['checked'] = step['step_id'] in update.checked_steps
                step['evidence'] = update.note if step['checked'] else ''
            review.update(revision=review['revision'] + 1, note=update.note, updated_at=now, submitted_at=now if submit else review['submitted_at'], status='submitted' if submit else 'draft')
            review['audit'].append({'at': now, 'action': 'submit' if submit else 'save_draft', 'revision': review['revision'], 'operator_id': session_id, 'checked_steps': update.checked_steps, 'note': update.note, 'authenticated': False})
            self.store.save_review(session_id, event_id, review)
            return review

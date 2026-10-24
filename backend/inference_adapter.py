"""A thin, checksum-verified adapter around the unchanged research pipeline."""
import hashlib
import os
import warnings
from pathlib import Path

os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')

import joblib
import numpy as np
import pandas as pd

from run_fluo_v2 import FEATURES, THRESHOLDS, inference

ROOT = Path(__file__).resolve().parents[1]
MODEL_SHA = '5237917ae6ccfccd2ff21d288b92201536c923028d8931599aaf9715033e9b09'
REQUIRED = (
    'timestamp', 'site_id', 'minute_id', 'split', 'operating_mode', 'throughput_index',
    'steam_flow_obs_kg_h', 'condensate_return_obs_kg_h', 'steam_pressure_obs_barg',
    'steam_temperature_obs_C', 'return_temperature_obs_C', 'link_online', 'data_quality_flag',
)


class FrozenEstimator:
    """Preserve the original predictor; allow the upstream zero-scoreable-row case."""

    def __init__(self, path=None):
        path = Path(path or ROOT / 'models/fluo_hgb_synthetic_v2.joblib')
        if hashlib.sha256(path.read_bytes()).hexdigest() != MODEL_SHA:
            raise RuntimeError('ARTIFACT_MISMATCH: refusing model deserialization')
        self.model = joblib.load(path)
        if type(self.model).__name__ != 'HistGradientBoostingClassifier' or self.model.n_features_in_ != len(FEATURES):
            raise RuntimeError('ARTIFACT_MISMATCH: wrong estimator or feature count')

    def predict_proba(self, values):
        if len(values) == 0:
            return np.empty((0, 2), dtype=float)
        # The audited compare_models.py fitted ndarray inputs. Preserve original
        # feature order and predictions, suppress only sklearn's cosmetic warning.
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', message='X has feature names, but HistGradientBoostingClassifier was fitted without feature names')
            return self.model.predict_proba(values)


def score_telemetry(sensor, model):
    """Strict sensor-only boundary, plus the original causal features/gates."""
    if set(sensor.columns) != set(REQUIRED):
        raise ValueError('INVALID_SCHEMA: exactly the 13 observed telemetry fields are accepted')
    if sensor.empty:
        raise ValueError('INVALID_SCHEMA: at least one row is required')
    if sensor[['timestamp', 'site_id', 'minute_id', 'operating_mode', 'link_online', 'data_quality_flag']].isna().any().any():
        raise ValueError('INVALID_SCHEMA: required metadata must be present')
    for _, group in sensor.groupby('site_id', sort=False):
        ordered = group.sort_values('minute_id')
        times = pd.to_datetime(ordered.timestamp, utc=True)
        if len(times) > 1 and not times.diff().dropna().dt.total_seconds().eq(60).all():
            raise ValueError('INVALID_CADENCE: replay requires chronological one-minute readings per site')
        if len(ordered) > 1 and not ordered.minute_id.diff().dropna().eq(1).all():
            raise ValueError('INVALID_CADENCE: minute indices must be contiguous')
    return inference(sensor[list(REQUIRED)], model, run_mode='SYNTHETIC_REPLAY')


def persistence_counts(prediction):
    valid = prediction.quality_action.eq('SCORE_ALLOWED')
    candidates = valid & prediction.gb_signature_score.gt(THRESHOLDS['gb_signature'])
    return candidates.groupby(prediction.site_id).transform(lambda x: x.rolling(10, min_periods=1).sum()).astype(int)

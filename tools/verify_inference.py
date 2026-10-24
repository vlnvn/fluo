"""Gate 1: exercise frozen inference and legacy safeguards without training."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from importlib.metadata import version
from pathlib import Path

os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import joblib
import pandas as pd
from run_fluo_v2 import FEATURES, inference


def digest(data):
    return hashlib.sha256(data.to_csv(index=False, float_format='%.12g', na_rep='null').encode()).hexdigest()


def main():
    source = ROOT.parent / 'source-audit/ml-20261024'
    dataset = ROOT / 'data'
    if not dataset.exists():
        shutil.copytree(source / 'data', dataset)
    model_path = ROOT / 'models/fluo_hgb_synthetic_v2.joblib'
    expected = '5237917ae6ccfccd2ff21d288b92201536c923028d8931599aaf9715033e9b09'
    assert hashlib.sha256(model_path.read_bytes()).hexdigest() == expected
    model = joblib.load(model_path)
    assert model.__class__.__name__ == 'HistGradientBoostingClassifier'
    frozen = json.loads((ROOT / 'reports/frozen_experiment_config.json').read_text())
    assert model.n_features_in_ == len(FEATURES)
    assert frozen['train']['input_features'] == FEATURES
    if hasattr(model, 'feature_names_in_'):
        assert list(model.feature_names_in_) == FEATURES
    sensor = pd.read_csv(dataset / 'locked/20261201/fluo_sensor_stream.csv.gz')
    start = time.perf_counter()
    prediction = inference(sensor, model)
    duration = time.perf_counter() - start
    repeated = inference(sensor, model)
    pd.testing.assert_frame_equal(prediction, repeated, check_exact=True)
    causal = []
    zero_valid_prefixes = 0
    for site in sensor.site_id.unique():
        rows = sensor[sensor.site_id.eq(site)].reset_index(drop=True)
        complete = inference(rows, model)
        for size in (26, 75, 250, 1000):
            try:
                prefix = inference(rows.iloc[:size], model)
            except ValueError as error:
                if '0 sample(s)' not in str(error):
                    raise
                assert complete.iloc[:size].gb_signature_score.isna().all()
                zero_valid_prefixes += 1
                continue
            pd.testing.assert_frame_equal(prefix, complete.iloc[:size], check_exact=True)
        causal.append(str(site))
    cadence = sensor.groupby('site_id').timestamp.apply(lambda x: pd.to_datetime(x, utc=True).diff().dropna().dt.total_seconds().unique().tolist()).to_dict()
    legacy = ROOT / '.local/legacy-qa'
    legacy.mkdir(parents=True, exist_ok=True)
    for name in ('qa_and_demo.py', 'run_fluo_v2.py', 'run_fluo_ml_v1.py'):
        shutil.copy2(source / name, legacy / name)
    shutil.copy2(model_path, legacy / 'fluo_gb_signature_model.joblib')
    if not (legacy / 'data/locked/20261201').exists():
        shutil.copytree(dataset / 'locked/20261201', legacy / 'data/locked/20261201')
    run = subprocess.run([sys.executable, 'qa_and_demo.py'], cwd=legacy, capture_output=True, text=True)
    out = ROOT / 'docs/implementation/qa'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'legacy-qa.log').write_text(run.stdout + run.stderr, encoding='utf-8')
    assert run.returncode == 0, run.stdout + run.stderr
    report = {'status': 'PASS', 'python': sys.version, 'dependencies': {m: version(m) for m in ('numpy', 'pandas', 'scipy', 'scikit-learn', 'joblib')},
              'artifact_sha256': expected, 'estimator': type(model).__name__, 'model_params': model.get_params(), 'features': FEATURES,
              'dataset_sha256': hashlib.sha256((dataset / 'locked/20261201/fluo_sensor_stream.csv.gz').read_bytes()).hexdigest(),
              'telemetry_rows': len(sensor), 'input_columns': list(sensor.columns), 'cadence_seconds_by_site': cadence,
              'warning_minutes': int(prediction.gb_signature_warning.sum()), 'quality_states': prediction.quality_action.value_counts().to_dict(),
              'output_digest': digest(prediction), 'repeat_exact': True, 'prefix_parity_exact_sites': causal,
              'tolerance': 0, 'inference_seconds': duration, 'legacy_qa_exit_code': run.returncode, 'training_performed': False,
              'upstream_zero_valid_prefix_error_count': zero_valid_prefixes,
              'upstream_limitation': 'Original inference calls predict_proba with zero rows during all-gated prefixes. Adapter must return no scores for those rows without changing scored behavior.'}
    (out / 'INFERENCE_VERIFICATION.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()

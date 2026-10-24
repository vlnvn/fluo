# Reconciliation of sources

| Claim / source A | Source B / evidence | Implementation decision | Consequence |
|---|---|---|---|
| Archive selected_model.joblib | Git models/fluo_hgb_synthetic_v2.joblib; byte hashes in SOURCE_MANIFEST.json | Compare hashes and estimator settings before loading; use verified incumbent, no retraining | Explicit model lineage |
| Existing qa_and_demo.py expects root fluo_gb_signature_model.joblib | Committed selected artifact is under models/ | Use an adapter and parity tests; run legacy QA in a temporary isolated copy with the expected path | Original experiment code/reports preserved |
| Source comment says persistence resets after invalid rows | Implementation rolls 10 row candidates, invalid rows count false; valid gate suppresses alerts during invalid history | Match executable implementation exactly; test boundary behavior | No silent model-policy change |
| Figma shows EV-018/017/016/015 and illustrative readings | Runtime detections must derive from chronological model output | Event IDs mapped deterministically to actual replay detections; dynamic values replace illustrations | Figma styling retained, readings and evidence remain authentic |
| Figma scenario names describe injected causes | Model only flags an ambiguous deficit signature | Scenario names are documented experiment setup; event diagnosis remains unconfirmed | No oracle leakage into runtime features/diagnosis |
| Figma print preview is a visual state | User requires real downloads and browser print | Generate event-specific A4 PDFs server-side and actual printable HTML | Functionality goes beyond static Figma |
| Docs describes modular AI-IoT architecture | Current evidence is software replay only | Python gateway inference, read-only, explicit simulated-research provenance | No invented ESP32 connection or plant partner |
| Freeze environment Python 3.13.5, sklearn 1.8.0 | Local bundled runtime Python 3.12.14 | Pin sklearn 1.8.0 and matching data libraries; require exact prediction parity | Cross-Python execution disclosed |

Technical source hashes and any observed parity discrepancies are recorded by executable audit scripts rather than assumed.

Observed upstream edge case: original inference calls predict_proba on zero rows for all-gated prefixes. FrozenEstimator returns an empty (0,2) matrix only for these calls. All scored rows use the original predictor; tests and exact prefix parity verify the distinction.

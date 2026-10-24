# Model comparison and synthetic evaluation

Research snapshot: 24 October 2026. **All records and outcomes are synthetic**. The results do not establish accuracy at a textile plant.

## Training and model selection

Models: histogram gradient boosting (HGB), ExtraTrees, LightGBM. Each was trained on the original dataset's designated A/B training split. The supervised target combines simulated physical loss and return-meter underreading; this is **not a fault-location label**. Labels do not enter the input features.

Fixed development candidates: score thresholds 0.70, 0.80, 0.90 and 0.95, with 5-of-10-minute persistence. Development-only selection required physical-event recall at least 98% and at most 0.5 clean-window alarm clusters per 100 hours, then minimized transport-delay alerts and alarm burden. Selection used three synthetic seeds, not the earlier v2 locked test or the later fresh holdout.

HGB at 0.90 met the development gate: 49/49 physical episodes detected and 1/14 transport-delay episodes alerted. Neither ExtraTrees nor LightGBM strictly improved the selected trade-off. See `reports/development_summary.csv` and `reports/frozen_selection.json`.

## Fresh holdout

After model selection, two additional seeds (20270111 and 20270112, **numeric seed IDs, not experiment dates**) were generated with five simulated configurations each. All configurations still use the same generator family.

| Metric | HGB / frozen threshold 0.90 |
|---|---:|
| Records | 172,800 |
| Physical-loss episodes alerted | 69/71 (97.18%) |
| Transport-delay episodes alerted | 4/13 |
| Return-meter bias episodes alerted | 21/22 |
| Clean-window alert clusters | 0 over ~1,353.5 hours |
| Warning minutes in unmarked valid periods (including aftereffects) | 520 / 91,936 |

The two definitions of “normal” above are not interchangeable. The clean-window metric excludes ±45 minutes around injected events; unmarked normal includes aftereffects and is more demanding. Neither is a verified plant false-alarm rate.

A descriptive Clopper–Pearson 95% interval for 69/71 is roughly 90.2–99.7%; it ignores scenario dependence and **must not be extrapolated to industrial recall**.

## Instrument shifts (post-selection stress)

| Modified sensor condition | Physical events alerted | Transport-delay events alerted | Warning minutes in unmarked valid periods |
|---|---:|---:|---:|
| As generated | 69/71 | 4/13 | 520 / 91,936 |
| Return meter -5% | 71/71 | 4/13 | 817 / 91,936 |
| Return meter -10% | 71/71 | 13/13 | **66,603 / 91,936** |
| Steam meter +5% | 71/71 | 3/13 | 756 / 91,936 |

A 10% systematic return-meter underreading is a severe failure condition for the current detector. A physically leaking return line and a biased flowmeter can produce indistinguishable measurements. No choice of classifier alone can guarantee a correct causal diagnosis without additional evidence.

## Deployment boundary

**Permitted:** research demonstrations on synthetic replay, training comparisons, baseline evaluation, read-only inspection triage.

**Not permitted:** claim of proven factory recall/precision, diagnosis of a specific leaking trap, production automation, autonomous valve control, safety approval or verified savings.

The highest-priority next evidence is instrument-quality assessment and measurements from a consenting plant, with documented meter locations, operations and independent inspection outcome. Continued tuning to synthetic scenarios would not close this external-validity gap.

## Reproduce

```bash
python -m pip install -r requirements.txt
python bootstrap_dataset.py
python prepare_cohorts.py
python compare_models.py
python generate_final_holdout.py
python final_validation.py
```

Use the frozen `reports/frozen_selection.json` before running the final holdout. Generating new seeds does not produce independent field evidence.

# Fluo synthetic deficit-signature detector

**Purpose:** flag persistent steam/condensate-return discrepancy for human investigation in an offline research replay. Output does not identify a specific physical defect.

**Model:** HistGradientBoostingClassifier, max_iter=75, max_leaf_nodes=9, min_samples_leaf=70, learning_rate=.05, L2=3, random_state=71; synthetic score cutoff 0.90, 5 of 10 consecutive minutes, mode stabilization and quality checks.

**Inputs:** observed steam and return flow; their causal rolling residuals; steam rate changes and rolling variability. No future windows, oracle labels or hidden true flows as inference inputs. Operational metadata and quality flags gate scoring.

**Target:** simulated physical deficit or observed return-meter underreading; supervised synthetic surrogate, not independently validated cause or calibrated physical-loss probability.

**Dataset:** A/B split training on v1; three development seeds for selection; two fresh seeds with five simulated configurations for final evaluation. All derive from one simulator family.

**Known failure modes:** return-meter calibration drift, uncertain meter locations, unseen steam process modes, flash recovery configurations that differ from the simulation, unobserved drain flow, and label-proxy mismatch. -10% meter shift fails the stress test severely. Novel facility profiles require commissioning and recalibration.

**Required controls:** fail closed for field operation, verify meters and timestamps, never approve return of potentially contaminated condensate, never actuate boiler/valves automatically, and request authorized inspection where appropriate.

**Status:** research-only; no field validation, industrial recall, verified resource savings, or TKT4 certification.

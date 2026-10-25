# Vercel Hobby feasibility — 25 October 2026

Decision: **actual fullstack Vercel Python + Neon is technically feasible**. Final hosted release status is generated in `RELEASE_DECISION.json`; exact build, SHA and evidence are in `qa/vercel/CLOUD_RELEASE.json`. Branch deploy/vercel-hobby starts at d604748b6ec542b4a0a88fb736df217f5f2b5f6f. Original research requirements, HGB, data and research code are preserved. No precomputed prediction fallback is used.

## Account, terms and free resources

Verified through the authenticated API: team vlnvns-projects, team_zwZnclCELlEBLoZg5s1LX6HA, plan hobby. The owner explicitly confirmed current use is a personal educational demo without a financial purpose. Future sales, paid development, prize/funding solicitation or commercial use requires a fresh eligibility review; this is not a general legal approval. [Hobby](https://vercel.com/docs/plans/hobby), [fair use](https://vercel.com/docs/limits/fair-use-guidelines), [terms](https://vercel.com/legal/terms).

Project fluo: prj_jUCHbMO505j8ZiTo7upVT4mYEPpp. Separate non-ML runtime probe: prj_RifkoONamCU4jtw4zce7q8jJQZrV. Region sin1. No paid plan, trial upgrade, custom domain purchase or card was selected.

Neon Marketplace resource fluo-guest-state: store_2wSPyO8xU9Ig5KBO; installation icfg_4Qk22PCkIr61tlmR09q38ZoU. Actual plan catalog verified free_v3, paymentMethodRequired=false,1GB/project,100CU-hours/project/month. Singapore, auth=false,realtime=false. Terms accepted by the owner. CLI provisioning succeeded once; provider skill installation failed and was not mistaken for a failed resource creation. [Neon pricing](https://neon.com/pricing), [pooling](https://neon.com/docs/connect/connection-pooling).

## Objective runtime measurements

VERCEL_LOCAL_MEASUREMENTS.json contains actual fresh-process Windows results, not cloud estimates:4.054s initialization including Python imports/model scoring,275165184-byte peak RSS,9.68ms snapshot p95,7.81ms mean snapshot CPU,31072-byte sample JSON.31 Linux CPython3.12 wheels total310115949 uncompressed bytes (93837597 downloaded). This is a dependency-content measurement, **not the actual deployed function bundle**. Original model32826bytes, SHA5237917ae6ccfccd2ff21d288b92201536c923028d8931599aaf9715033e9b09.

Official standard Python bundle limit500MB; large-function beta up to5GB on eligible Fluid projects is available but not required by the measured dependency content. Hobby2GB/1vCPU, duration300s maximum; app configured60s. Request/response cap4.5MB; app body cap4MiB. Filesystem is not durable; only scratch is used for read-only audited inputs, never authoritative state. [Python runtime](https://vercel.com/docs/functions/runtimes/python), [limits](https://vercel.com/docs/functions/limitations).

Hobby included quotas:4active CPU-hours,360GB-hours provisioned memory,1million function invocations/month,100GB fast transfer. These are quotas, not a capacity guarantee. At fixed2GB, a five-minute allocated instance consumes approximately0.167GB-hours; actual instance reuse, idle billing and request CPU must be observed. Exceeding free allowances may pause service rather than providing dependable industrial availability.

The real Vite+FastAPI probe reached READY and returned Python3.12.14/GCC on HTTPS in sin1. It contains no ML/private data and is not Fluo completion. Two failed attempts exposed real packaging requirements: Node packages require an explicit install in the FastAPI build; public/ is CDN-promoted and absent from the function. Removing its redundant Python static mount fixed the probe. Full Fluo keeps web/dist in the function and disables static promotion so existing CSP/middleware behavior is retained.

## State, artifacts and restrictions

SQLite local mode remains intact. Vercel refuses startup without public mode and a real PostgreSQL URL; no online SQLite fallback. Postgres schema1 has foreign keys/cascades, unique objects, bounded JSON, transactions and a cross-instance advisory transaction lock preserving read/modify/write review boundaries. This conservative global lock is not a throughput claim. Pool0–2 connections/instance,5s waits, statement/lock timeouts, Neon pooled endpoint, prepare_threshold=None. TLS verify-full uses pinned Mozilla CA; validation was never disabled.

Global DB budgets:1200API requests/minute,12000/hour,60guest entries/hour. Vercel guests:50active,2sessions,200mutations; TTL2hours and30review revisions. Quotas span instances. Requests still consume platform/DB resources before rejection; no DDoS resistance or unlimited free uptime is claimed.

Only two owner-approved runtime files are stored as private bytea rows in Neon. The app role can SELECT them but cannot UPDATE them. Exact names, size limits and original SHA256 are checked again before scoring. Files are retrieved into ephemeral scratch; neither private packet, archive, labels for evaluation, proposal, local DB nor notes enter public Git/static/build uploads. Runtime catalog labels select reviewed windows; model inference remains sensor-only. Vercel owner explicitly approved storing the restricted app-role DSN in project Secret settings. Database credentials are not printed or versioned. The private-tool OIDC logging incident and mitigation are documented in the final security audit.

The runtime stream has 51,840 rows. Its canonical LF CSV fingerprint (12 significant digits) is `2f334f76816f7cff05f843d77f64a85f393e2ca18336c4acae33eec320a34ac3`, matching actual Linux inference and local Windows inference with the same serialization. The earlier Windows CRLF fingerprint `cdd1a7...` differed solely in line endings, verified by hashing both serializations of identical predictions. The code now explicitly uses LF. This is a serialization parity check, distinct from the separate 86,400-row locked evaluation with exact repeat/prefix parity; it is not a field accuracy claim.

## Gates at this checkpoint

G0 baseline 26 API tests and browser smoke passed. Migrated local suite 34 passed; real Neon suite 6 passed; built and DEV browser suites 18 each passed. G1 actual Python/Vite probe passes. G2 adapter/private artifacts/secrets implemented. Full HTTPS API, security, browser and persistence evidence is recorded under `qa/vercel`; the release gate reads those files and remains blocked if any required scope fails.

## Actual cloud observations

The complete frozen HGB pipeline ran on Vercel Python 3.12.14/GCC, not a mocked service. One observed instance reported lifespan initialization 3.460 seconds and peak RSS 351,277,056 bytes. This includes private-input fetch/scoring but excludes platform queue/boot time. An actual browser auth request took 9.476 seconds; most API requests in that trace were approximately 74–250 ms. These are samples, not a p95/SLA or guaranteed cold-start bound. First observed readiness in the API capture was 177 ms on an already responsive deployment, not a cold-start claim.

The build log reported **297.05 MB before dependency optimization**, then compiled bytecode and completed. The provider did not return a final optimized bundle byte count in the inspected output, so the local wheel measurement must not be called that final size or used to certify beta eligibility. Actual deployment completed successfully within the configured runtime.

Test runs intentionally retained database budgets. The cumulative guest-entry suite hit the 60/hour cap and returned 429; subsequent release testing waits for a fresh clock-hour window rather than clearing shared counters. There was also a corrected test fixture import-cache issue and a CI lint failure from a Playwright callback named `use`; both are recorded in the final QA report. Provider protection was never disabled to pass tests.

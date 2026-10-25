# Vercel Hobby feasibility — 25 October 2026

Decision before full deployment: **technically feasible; hosted release tests pending**. Current branch deploy/vercel-hobby starts at d604748b6ec542b4a0a88fb736df217f5f2b5f6f. Original research requirements, HGB, data and research code are preserved. No precomputed prediction fallback is used.

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

Only two owner-approved runtime files are stored as private bytea rows in Neon. The app role can SELECT them but cannot UPDATE them. Exact names, size limits and original SHA256 are checked again before scoring. Files are retrieved into ephemeral scratch; neither private packet, archive, labels for evaluation, proposal, local DB nor notes enter public Git/static/build uploads. Runtime catalog labels select reviewed windows; model inference remains sensor-only. Vercel owner explicitly approved storing the restricted app-role DSN in project Secret settings. No credential is printed or versioned.

The runtime stream has51840rows; its model-produced output CSV fingerprint (12-significant-digit serialization) is cdd1a7a7c46d27b63482860ca193890b7e98c0357e82d9b634daf82a2e8df81d. This differs from the separate86400-row locked evaluation, whose exact local repeat/prefix parity was rerun. Hosted runtime fingerprint comparison must be recorded after full deployment; no industrial accuracy claim follows.

## Gates at this checkpoint

G0 baseline26API passes and real browser smoke passed. Migrated local suite34passes; real Neon suite6passes; built browser18passes; DEV run/security scans finishing. G1 minimal actual Python/Vite probe passes. G2 adapter/private artifacts/secrets implemented. G3/G4/G5 full hosted tests still pending. RELEASE_DECISION must remain PUBLIC_DEPLOYMENT_BLOCKED until actual fullstack/security/persistence/browser/PDF evidence exists.

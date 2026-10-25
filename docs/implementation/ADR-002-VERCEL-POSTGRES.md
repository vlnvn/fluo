# ADR002 — Single-origin FastAPI, live frozen HGB and private PostgreSQL

Date2026-10-25. Continue the reviewed prototype on deploy/vercel-hobby; no frontend redesign, scientific retraining or research manifest replacement.

Choose native Python3.12 FastAPI plus its existing Vite build on one Vercel origin. pyproject.toml adds exact deployment dependencies and server:app entrypoint while retaining pytest/Ruff configuration. Original requirements.txt remains the research manifest. Full model scoring runs once per function instance on the original51840-row runtime stream; immutable in-memory predictions support deterministic replay. This is not precomputed hosted inference.

Choose Neon Free Postgres for all hosted guest/session/review/preference/CSRF/expiry/quota state. Keep SQLite only for local mode. Explicit SQL migration is an administrative operation; runtime role cannot create/alter schema or change private artifacts. No local legacy data is migrated.

Store only the two explicitly approved, checksummed sensor/catalog inputs privately in the same database. App loads fixed bytea rows into scratch and verifies their hashes; the original model remains checksum-guarded. This avoids private build files, arbitrary download URLs and a second paid storage service. No browser route exposes database artifacts. Secrets remain in provider settings and ignored local files.

Use transaction-scoped advisory locking across instances to preserve the existing service lock semantics, plus review revision checks and database constraints. Batch review reads per snapshot to avoid one network query per historical event. The single demo-wide lock intentionally favors correctness over throughput. Short pool limits and shared database quotas bound resource use but do not prevent platform quota exhaustion or DDoS.

Rejected: online SQLite (ephemeral/multiple instances), fake state or predictions, new ML algorithms, a separate unprotected Python origin, buying Render/Pro, and treating a static/probe URL as complete Fluo. No fallback changes the scientific demonstration without further user authorization.

Deployment remains guarded by original guest capability authentication and provider preview protection. Test Vercel protection using authenticated CLI/origin-scoped short-lived test headers; do not remove protection to make tests pass. Only a verified SHA can be released, and actual provider persistence/redeploy/backup plus full browser/PDF checks must precede the final release claim.

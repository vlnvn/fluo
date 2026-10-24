# Deployment runbook

Current outcome: **LOCAL_DEMO_READY; external deployment BLOCKED.** No protected HTTPS URL exists. Do not expose this unauthenticated API, use a public tunnel, or loosen ingress to bypass the gate.

## Verified local path

```powershell
cd C:\College\DEEPX\fluo
# Stop an existing launcher before setup.
.\setup.ps1
.\.venv\Scripts\python.exe tools\dev.py
```

Open http://127.0.0.1:5173. Built single-origin alternative:

```powershell
cd web
npm run build
cd ..
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --workers 1 --no-server-header
```

Open http://127.0.0.1:8000. `/health/live` and `/health/ready` are implemented. Research docs remain local at `/docs`. Setup requires the original audited archive and never trains.

## Local container recipe — NOT EXECUTED

Docker CLI/engine was absent. On an approved build host, install Docker, run preparation and review `.dockerignore`. Its allowlist excludes ZIP/private docs/DB/source exports and packages only minimal sensor/catalog/model/runtime files. Confirm rights before a remote build/registry upload.

```powershell
.\.venv\Scripts\python.exe tools/prepare_runtime.py
docker compose -f compose.local.yaml build
docker compose -f compose.local.yaml up
```

Compose publishes127.0.0.1:8000 only; nonroot10001, persistent named volume, read-only root, dropped capabilities and one worker. Stop ordinary Fluo before using the same port. Verify build, Linux startup, reports, volume ownership/restart and full tests before treating packaging as ready. Back up state; do not delete the volume to troubleshoot. Resolve base tags to reviewed immutable digests and record the final image digest; current recipe is not a future byte-for-byte build guarantee.

## Minimal external prerequisites and release sequence

1. Supply a private container-host account/project with confirmed plan, region, CPU/RAM, durable disk and budget. Connector returned no visible Vercel teams/Fluo project; no container-host/IdP entitlement was available. No account or price is invented.
2. Implement verified server principal and explicit owner/guest authorization for every API, preview, session, review, preference and HTML/PDF endpoint. Preserve local notes through a deliberate migration. Anonymous/cross-owner tests must pass normally, not xfail.
3. Configure trusted identity-aware HTTPS ingress, validate signed assertions and prevent direct origin/IP/hostname/port bypass. Protect frontend and backend together. Verify anonymous direct URLs, including docs/health exceptions under an explicit policy.
4. Define expiry/logout/invalidation, Secure/HttpOnly/SameSite cookies and CSRF if cookie auth is chosen. Review exact hosts/origins. Current local allowlist/nonlocal startup refusal must not be loosened before real auth/tests exist.
5. Mount durable state or implement another tested durable store; keep one worker until concurrency is redesigned. Define backup/restore/retention, migrations and two authenticated-owner tests.
6. Build audited code/data/model using reviewed image digests and lockfiles; no training or untrusted model download at startup. Execute all local gates before deploying privately.
7. On the actual HTTPS URL, run anonymous/login/logout/expiry, cross-owner/guest, direct API/PDF/preview, CSRF/XSS/rate/size, full UI/media/report/visual tests, restart+redeploy durability, rollback, logs and capacity/budget checks. Only then record DEPLOYED_ACCESS_CONTROLLED with a tested URL.

`python tools/release_gate.py --target local` checks evidence/digests; `--target staging` currently exits2 with blockers. Editing a PASS file is not implementing access control.

## Provider and cost limits

Private persistent container is a candidate, not a purchased service. [Render disks](https://render.com/docs/disks) documents ephemeral defaults and eligible paid persistence. Region, sleep/cold-start, fees, latency and credits remain unverified. A static frontend alone is not this fullstack deployment. No external billing resource was created.

Use simulated telemetry/fictional facility disclosures and unverified local operator identity. Never claim plant diagnosis, savings, recovery authority or physical device integration. Avoid sensitive real customer notes in this local installation.

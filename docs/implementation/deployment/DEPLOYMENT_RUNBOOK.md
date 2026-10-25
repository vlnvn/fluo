# Secure guest deployment runbook — 25 October 2026

**Historical Render recipe; superseded by [VERCEL_RELEASE_RUNBOOK.md](VERCEL_RELEASE_RUNBOOK.md).** The current Vercel/Neon decision and executed evidence are in `RELEASE_DECISION.json` and `qa/vercel/`. The Render instructions below were never provisioned and must not be used to purchase resources for this free-tier release.

## Local reproduction

Run setup.ps1 then .venv/Scripts/python.exe tools/dev.py. Requires the original audited archive; never trains. Loopback ports 5173/8000. Built single-origin alternative: npm ci and npm run build in web, then .venv/Scripts/python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --workers 1 --no-server-header. Open http://127.0.0.1:8000 and explicitly start a guest workspace. /docs, /redoc and /openapi.json are disabled.

Guest capability authentication does not verify a human operator. Anyone may create their own empty workspace; this is the intentional reviewer entry policy. Logout revokes access. Legacy unowned records remain offline and are never auto-assigned. Back up the database before migration; never publish it.

## Prepared Render native Python path (not provisioned)

render.yaml builds frontend and API on one origin, one worker, Singapore Starter service, 1GB persistent disk at /var/data. Native Python avoids the unavailable Docker engine. Docker base digests are recorded in BASE_IMAGES.json; that recipe was not built.

Required user actions:
1. Sign in at https://dashboard.render.com/ and connect vlnvn/fluo with authority to create the service. Read-only inspection reached /login.
2. Approve recurring plan/disk costs. Checked [Render pricing](https://render.com/pricing): Starter US$7/month plus disk US$0.25/GB/month, approximately US$7.25/month before tax/egress or other resources. Confirm current checkout terms. No purchase was made.
3. Provide approved private HTTPS build-artifact storage. The ignored .local/fluo-runtime-private.zip contains only two audited runtime files; RUNTIME_PACKET.json records exact hashes. Confirm permission for this private upload. Never put signed URLs, bearer secrets or private data in Git/video/chat.

Then:
1. Import blueprint from release/fluo-secure-guest-demo; review final commit/billing. Keep automatic deployments off during release review.
2. Set FLUO_RUNTIME_URL, FLUO_RUNTIME_PACKET_SHA256 and optional FLUO_RUNTIME_BEARER in provider secret settings. Downloader requires HTTPS, rejects redirects, limits size and validates exact packet members/digests. No public artifact URL.
3. Confirm FLUO_RELEASE_MODE=public, FLUO_DB_PATH=/var/data/fluo.sqlite3 and provider-owned RENDER_EXTERNAL_URL. Only set FLUO_PUBLIC_ORIGIN for a verified custom domain. Exact HTTPS host, no wildcard CORS. Public cookie is __Host-/Secure/HttpOnly/SameSite=Strict; public raw research inference is forbidden.
4. Deploy reviewed commit. Save sanitized build/start logs and actual URL/commit. Check /health/live and /health/ready. Minimal readiness is public; all research/session/report endpoints require ownership. Startup validates model/data/catalog.
5. Run browser tests against the ACTUAL HTTPS URL using FLUO_BASE_URL. Use two independent guests and anonymous requests on every session/preview/event/report/preference/mutation route. Verify 401/404, CSRF403, expiry/logout, Secure cookie, exact hosts/origins, docs/raw inference/file denial and direct-origin behavior. TestClient is not hosted TLS evidence.
6. Create test review/preferences, restart and redeploy, verify both survive. Take an online SQLite backup via private provider console; restore to a separate test path and verify integrity/revisions/ownership. Never ordinary-copy a live WAL database. Keep one worker.
7. Test all Full/Compact routes, keyboard/axe, report download/print, opt-in chime, parity, bounded load and provider logs/budget/disk alerts. A 512MB plan is not capacity-validated.
8. Only after real hosted evidence, add reviewed URL/commit/results and extend release_gate.py to consume those records. Current gate deliberately cannot claim deployment from local results.

Default guest TTL two hours, max200 active guests, five sessions/guest,500 mutations/guest,30 review revisions. Expired data cleaned when another workspace opens; no periodic deletion SLA. Process-local limits are not distributed DDoS defense.

Rollback: backup before migration. Schema2 preserves legacy data; do not downgrade a schema2 database into an older app. Restore compatible application and online backup together during maintenance; test provider restore. fluo-local-baseline-20261025 preserves pre-auth code but is unsafe publicly.

Synthetic telemetry, fictional facility, no field savings, verified human identity or physical actuation.

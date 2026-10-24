# Release deployment decision — 25 October 2026

**LOCAL_DEMO_READY; PUBLIC_DEPLOYMENT_BLOCKED.** Guest identity/ownership is now implemented and tested; previous reports of missing application auth are historical. No public URL, paid resource or private artifact upload exists.

Keep the existing frontend build served by FastAPI, original frozen inference and one-worker SQLite. The prepared Render native-Python blueprint adds persistent disk without requiring local Docker. Vercel split frontend/serverless is not selected because persistence and a second origin would add unverified boundaries. Read-only Vercel inventory found no visible teams/Fluo projects; Render browser inspection reached /login. No provider entitlement or billing consent is inferred.

The exact next actions and checked estimated cost are in DEPLOYMENT_RUNBOOK.md. Public entry intentionally permits a new isolated guest workspace, not access to other guests' data. Deployment must prove HTTPS/cookie/host policy, negative ownership tests and restart/redeploy durability on the actual host before any deployed claim.

Git release branch and draft PR were created using existing authorized Git transport/connector. No merge/reset/rebuild of research was performed. Docker base manifests were resolved to immutable digests, but image build, Linux host startup and capacity remain unexecuted.

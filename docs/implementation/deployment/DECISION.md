# Deployment decision — 25 October 2026

Implementation `e84b5ca`. **LOCAL_DEMO_READY + BLOCKED_FOR_PUBLIC_ACCESS.** No protected HTTPS deployment exists. No cloud resources, billing commitment, DNS, public ingress, Git push or private artifact upload was created.

Retain the existing single-origin Vite build served by FastAPI. Its startup-scored in-memory HGB and one-worker SQLite fit a persistent container better than a split ephemeral frontend/function arrangement. This is an architecture assessment, not a provisioned service guarantee.

Inventory: connected Vercel returned no visible teams and no Fluo project. That does not prove no account exists, but supplies no verified protected staging entitlement. No Render/container-host/IdP configuration was available. Docker CLI/engine was absent. gh exists; no remote repository mutation was necessary.

Options:

1. Current trusted loopback demonstration: selected now, existing code and state preserved.
2. Future private managed container + durable disk + identity-aware HTTPS ingress: preferred candidate once identity, ownership, account/plan and on-host negative tests exist. A private service alone does not establish browser/SSO access.
3. Vercel frontend plus separate Python origin: not selected; introduces another protected origin and persistence boundary without verified entitlement. A static frontend alone would not be this fullstack demo.

Dockerfile/compose.local.yaml are a minimal local-only recipe, **NOT BUILT here**: Node22/Python3.12 stages, tested runtime version lock, nonroot10001, one worker, loopback host publication, persistent named volume, read-only root and dropped capabilities. They package only model/sensor/catalog/runtime assets, not ZIP, ground truth, documents, reports, credentials or current DB. External build/publish still needs rights and gate review. Base-image tags must be resolved to reviewed immutable digests before release; current tags are not a byte-for-byte reproducibility claim.

Observed Windows API process RSS225857536 bytes, peak298786816 bytes after testing: one sample, not capacity/soak evidence. Linux image startup/CPU/RAM and cloud costs are NOT TESTED. No region, sleep behavior, credit, fee or cold-start is assumed.

References: [Render persistent disks](https://render.com/docs/disks) documents ephemeral default storage and eligible paid disks; [public/private services](https://render.com/docs/web-services); [FastAPI trusted proxies](https://fastapi.tiangolo.com/advanced/behind-a-proxy/).

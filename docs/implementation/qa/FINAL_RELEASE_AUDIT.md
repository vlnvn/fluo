# Final release audit — 25 October 2026

Decision: **LOCAL_DEMO_READY / PUBLIC_DEPLOYMENT_BLOCKED**. No public HTTPS URL exists. Branch release/fluo-secure-guest-demo; draft PR https://github.com/vlnvn/fluo/pull/1 targets main and is not merged. Baseline tag fluo-local-baseline-20261025 preserves a3b4bf4. No reset/rebuild/retraining or proposal edits.

## Executed evidence

| Check | Result | Evidence |
|---|---|---|
| Python API/store/security |26 passed,0 skipped,0 xfail;1 upstream Starlette/httpx deprecation warning |guest-api.xml; guest-security-api.log|
| Frontend unit |3 passed|final-web-checks.log|
| DEV browser |18 passed,0 skipped/unexpected/flaky;56.3s|final-dev-e2e.json/log|
| Built single-origin browser |18 passed,0 skipped/unexpected/flaky;51.0s|final-built-e2e.json/log|
| Visual regression |8 assertions on four routes Full/Compact; no baseline updates|visual-regression.spec.ts and browser JSON|
| Accessibility |11 scoped Axe scans with0 violations, including guest entry; keyboard entry and dialogs|browser tests; not full WCAG certification or screen-reader testing|
| Typecheck/lint/build/Ruff |PASS|final-web-checks.log,final-web-build.log; Ruff executed on backend/tools/tests|
| Model parity |86,400 locked rows, exact repeat/prefix parity5sites, tolerance0|INFERENCE_VERIFICATION.json; digest276bcd03bcd1be4d1d7c708f53e4cba49cce4b5b18b1b6bb5161345a24c3cf93|
| Dependency advisories |0 known in executed npm/runtime/installed scans|final-npm-audit.json,release-python-audit.json,release-installed-audit.json|
| Bandit/source history |0 Bandit findings;0 detected secret patterns in18 commits/308 unique text blobs at pre-final scan|guest-bandit.json,SECURITY_INVENTORY.json; bounded detection only|
| Video |Actual continuous local capture,185.8s,H264/1440x980/25fps,muted; full decode0;13 sampled QA frames|../demo/VIDEO_PROVENANCE.json; actual MP4 ignored locally|
| PDF/print/media |Actual event PDF downloaded and parsed in tests; real A4 paths and original chime/native playback exercised|browser/API cases; demo real PDF and150/153s sampled preview|
| Real public HTTPS/security/persistence |NOT EXECUTED|No approved hosting/billing/artifact storage or deployed URL|

Security implementation f7d4ae9; recorded app0c0fe3b. Final application adds only a semantic main landmark to guest entry after that capture. TESTED_SOURCE_MANIFEST.json records exact tested source files. Historical audit files predate guest isolation and should not be quoted as current results. CI runs public-source checks only; private-data ML/full browser evidence is local and separately versioned.

## Independent review of boundaries and true issue ledger

| Severity / finding | Resolution / evidence | Status |
|---|---|---|
|P0 anonymous and cross-session object exposure|Cryptographic guest cookie, server-side expiry/revocation/ownership before object routes, all PDF/HTML/preview/preferences/review endpoints negative-tested; former xfail now normal PASS|CLOSED in local implementation; real host checks pending|
|P1 new guest page lacks main landmark|Added main; new unfiltered guest-entry Axe and keyboard test passes|CLOSED|
|P1 final Home-after-End test raced an in-flight seek|Wait for enabled control before next keyboard command; no assertion removed;18 built and18DEV pass|CLOSED test synchronization defect|
|P1 recorder stale scenario/check state|Wait for selected/ready scenario and async server-confirmed check; two stopped attempts not delivered|CLOSED recorder defect|
|P2 encoded captions initially overlapped UI|Reduced subtitle size; re-encoded from original continuous source; sampled frames show caption strip below UI|CLOSED|
|Release blocker: provider account, budget and private artifact storage|Native blueprint/private packet/secret configuration/runbook prepared; Render inspection reached login|OPEN external action|
|Release blocker: actual TLS, hostname/origin, Linux startup, disk restart/redeploy/restore, capacity|Must execute on actual provider; never substitute TestClient/local screenshots|OPEN until hosting exists|

The already-correct sidebar, Production capitalization, shared notification state, actual histogram/progress/sparkline data, single report action toolbar, operator button spacing and Forward/Rewind/live scrub are preserved and covered by corrections/post-audit tests. The83-frame Figma inventory is retained; guest entry/expiry/logout intentionally extend the operator design for security. No fresh claim of pixel-perfect matching of every frame.

Independent boundary inspection confirmed authorization precedes all current API object routes, ignores user-supplied identity headers, and covers reports as well as JSON. Public mode refuses raw inference, uses exact HTTPS origin/host and secure cookies. Minimal live/ready and static guest entry are intentionally public; starting a guest grants only a new isolated sandbox. Human operator identity remains unverified. Cookies authenticate possession, not employment or industrial authorization.

Residual risks: one worker/process-local abuse budgets; open guest entry can consume quota; no distributed DDoS defense; guest cleanup occurs on subsequent entry; no verified named identities; local cookie HTTP is not equivalent to public Secure TLS; no hosted capacity/disaster-recovery evidence; scanner blind spots and future dependency changes. SQLite migration preserves old unowned records privately, and no new guest can auto-claim them. No physical sensors, actuation, field diagnosis, measured savings, partner commitment or TKT4 claim.

Reproduce local setup/build/API/browser using README and deployment runbook. Gate local exits0; staging deliberately returns nonzero and records PUBLIC_DEPLOYMENT_BLOCKED. Deployment is unfinished, not waived.

Exact tested application/source commit: **4b21a7203f4ec7e9b07e2ca734c32176eceb421f**. This final documentation update changes no application/test/model code; the tested source manifest still matches. Secret scan covers history through that commit.

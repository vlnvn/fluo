# Final Vercel release audit — 25 October 2026

Hosted source `ab3ebc9650cabdc9e90f46b3e27df0959a904f50` at https://fluo-o3h0wtwma-vlnvns-projects.vercel.app, preview deployment `dpl_AtmJuJn8gAH4po1h1mbwiWYe7XHa`. Final machine decision: `deployment/RELEASE_DECISION.json`; provider/source/test hashes in `qa/vercel/`. Both deployed-commit GitHub quality workflows passed. PR#2 remains draft and unmerged; PR#1 unchanged.

| Executed scope | Result | Evidence |
|---|---|---|
| Final local Python / real PG18.6 |34 passed,0 skipped/xfail; one Starlette/httpx deprecation warning |vercel/final-local-api.xml|
| Actual Neon restricted-role suite |6 passed |vercel/neon-api.xml|
| Local DEV / built browser |18 passed each |vercel/local-dev-e2e.json; earlier private logs|
| Actual final HTTPS browser |18 passed,0 skipped/unexpected/flaky |vercel/hosted-e2e.json|
| Visual / accessibility / media |8 screenshot assertions unchanged;11 scoped Axe scans0 violations; keyboard and actual opt-in audio passed |same browser suite; existing Figma audit retained|
| HTTPS API/security/ownership |77 checks +15 additional checks; hostile Host404 and forged forwarding401 |vercel/hosted-capture.json,hosted-security.json,hosted-host-boundary.json|
| Redeploy persistence |7 checks, new instance UUID; review revision/status/note and preferences survive |vercel/hosted-verify.json; credential domain-transfer limitation explicit|
| Official reviewer access without OIDC |5 browser steps passed, including reload and logout |vercel/reviewer-access.json; capability excluded from Git|
| Event PDF / print |Actual downloaded PDF parses as2 A4 pages; four independent browser event reports; CSP/escaping pass |vercel/CLOUD_RELEASE.json and browser/API results|
| Backup / isolated restore |PASS; five exact table comparisons; source unchanged |vercel/hosted-backup-restore.json|
| Frozen model reproduction |86,400 locked-row exact repeat/prefix parity;51,840 actual cloud runtime fingerprint matches canonical local |INFERENCE_VERIFICATION.json;vercel/hosted-capture.json|
| SAST / advisories / source patterns |Bandit0; runtime pip-audit0; npm audit0 in deployed CI;22 commits scanned0 bounded secret-pattern findings at recorded scan |vercel/final-bandit.json,python-audit.json,CI_DEPLOYED_COMMIT.json;SECURITY_INVENTORY.json|

## Failures found and resolved

Initial probe packaging failures were corrected before accepting full Fluo. The first full deployment was unexpectedly assigned production by Vercel, stayed protected, and was not used as the release. API target `staging` is a different environment and OIDC was correctly rejected; official omitted-target preview semantics were verified and guarded against unexpected targets.

Windows/Linux runtime fingerprints initially differed because CSV defaults used CRLF versus LF. Hashing identical predictions with both endings reproduced both hashes; explicit LF fixed portability without touching the model or predictions. A shared imported browser hook registered inconsistently; a context fixture fixed it. CI then caught the callback name `use` as a React hook; renaming it passed lint and both CI workflows. A later06c1a55 browser run had15 passes and3 failures: one auth request9.476s plus initialization exceeded the10s assertion budget, and two guest entries hit the unchanged60/hour bound. Final hosted assertions allow30s and the final complete run used the next hourly window; no counters or protection were cleared. Final suite18/18 is recorded separately from failed runs.

## Practical limits

Actual instance lifespan initialization samples approximately3.4s and peak RSS approximately352MB; this excludes provider boot/queue. An already warm readiness request177ms is not a cold-start claim. Builder reported297.05MB before optimization, not a final bundle byte count. Free-tier capacity and tail latency are unproven; no load/DDoS/uptime claim. Only Chromium was exercised; no independent Safari/Firefox/mobile or screen-reader certification. Logical restore is separate from managedPITR/productionrollback. Provider-protected preview sharing expires, while app guest TTL remains two hours. Synthetic research and fictional facility; no plant/customer/savings validation. Existing real video remains a local recording.

## Temporary OIDC logging incident

An initial Playwright DNS failure printed the short-lived project development OIDC header in private tool output and an ignored local log. The saved log was redacted and the HTTPS helper now reports only a sanitized first error line. The token was not committed; the source/history scan now explicitly includes JWT patterns. No database DSN, database password or guest-owner credential was printed by that failure. The private conversation output cannot be retroactively erased by this agent. Revocation was not verified; its encoded expiry is2026-10-25T15:34:37Z (22:34:37 WIB). Do not share that earlier private output before expiry. Existing provider protection and app guest ownership remain enabled. This incident is not represented as a successful revocation or proof of public disclosure.

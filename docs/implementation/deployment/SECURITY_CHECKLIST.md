# Security gate evidence — 25 October 2026

| Gate | Result | Evidence |
|---|---|---|
| Guest identity and object authorization | PASS locally and on actual HTTPS | qa/vercel/hosted-capture.json,hosted-security.json; independent guest contexts and all JSON/PDF/HTML object routes |
| Expiry/logout/forgery/CSRF | PASS on actual HTTPS | Own disposable guest expired in Neon; revoked cookie401; foreign access404; CSRF/Origin403 |
| Public cookies/headers | PASS on actual HTTPS | Secure/HttpOnly/Strict/__Host-, HSTS; docs/raw inference denied; Host/forwarding negatives separately recorded |
| Migration/revisions/backup/reopen | PASS in executed scope | Real PostgreSQL/Neon tests; concurrent HTTP revision200/409; separate logical restore exact five-table comparison; legacy SQLite not uploaded |
| Frozen model/runtime | PASS | INFERENCE_VERIFICATION.json, digest guards |
| SAST/known advisories | No findings in executed scope | Bandit/pip-audit/npm audit; not proof of absence |
| History/source secrets | No detected patterns | SECURITY_INVENTORY.json; bounded rules |
| Actual HTTPS/redeploy/origin | PASS in executed scope | qa/vercel/hosted-verify.json: new instance and durable review/preferences; explicit test cookie transfer between hostnames; browser reload separately tested |
| Linux runtime | PASS | Native Vercel Python3.12.14 frozen HGB, private input hashes, canonical runtime output parity. Capacity and sustained load remain unproven |

Current decision is generated in RELEASE_DECISION.json from actual evidence. Vercel Hobby and Neon free_v3 were verified; no paid upgrade selected. Vercel Authentication remains enabled, with an actual-tested temporary reviewer share path. App guest authentication and ownership remain independent. TLS uses verified certificates; restricted app role cannot write private artifacts or run schema migrations. Shared database budgets remain active; cumulative QA actually reached guest-entry429. No penetration certification, zero-vulnerability, high-availability or DDoS-resistance claim. See VERCEL_RELEASE_RUNBOOK.md for quota, access-expiry, provider privacy and rollback limitations.

Temporary development OIDC was printed once by an initial private request exception; local log redacted, exception handler sanitized, JWT scan added. No public Git match; revocation not verified, expiry25October2026 22:34:37 WIB. See FINAL_RELEASE_AUDIT.md.

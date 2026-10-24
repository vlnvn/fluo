# Threat model — secure guest revision

Assets: frozen runtime/model, private replay/review/preferences/reports, guest bearer cookies and deployment secrets. Facility is fictional; future operator notes could be sensitive. Boundaries: browser → one-origin API → ownership middleware → SQLite; immutable inference → replay clock; escaped notes → HTML/PDF; private artifact store → build. No equipment boundary exists.

| Threat | Implemented and executed control | Residual |
|---|---|---|
| Anonymous/cross-guest object access | 256-bit random opaque cookie, SHA256 credential storage, server owner lookup before every object endpoint; normal API negatives and independent browser contexts pass | Open entry intentionally creates a new private reviewer workspace; no verified named human |
| Forgery/expiry/logout | Identity headers ignored, server TTL/revocation, HttpOnly, public Secure/Strict/__Host- cookie; tests pass | Local HTTP cookie is not Secure; hosted TLS/direct-origin untested |
| CSRF/rebinding/hostile origin | Separate memory-held CSRF, exact origin/host, guest intent header, no permissive CORS; negative tests pass | XSS/browser/provider remain boundaries |
| HTML/PDF injection | Escaping, nonce CSP, same-origin framing, nosniff, no remote upload/fetch feature | Inline layout styles; no penetration certification |
| Resource abuse | Body/query/time/rate limits;200 guests/5 sessions/500 writes/30 revisions; bounded SQLite; public raw inference denied | One-process limits; hosted RAM/load/disk not tested |
| Conflicting/lost/private legacy records | WAL, transaction lock/rollback, revision checks, schema2 migration, online backup/reopen tests; legacy remains unowned | Single worker; real disk/redeploy/restore untested |
| Supply chain/tampered model | Frozen hashes, lockfiles, pinned Docker base digests, Bandit/dependency/history scans | No Docker build; unknown vulnerabilities possible |
| Artifact exposure | Minimal private packet, HTTPS/no redirects/size/exact-member/digest verification | Cloud storage/permissions not provisioned |
| Scientific/operational overclaim | Synthetic disclosure; ambiguous cause; recovery unknown; no actuation | Simulator performance is not factory validation or savings |

Evidence: ../qa/guest-api.xml (26 passed; zero skipped/xfail), guest-bandit.json, advisory JSON, SECURITY_INVENTORY.json and browser logs. This supports local scope, not certification of an undeployed public service. Report operator identity remains unverified.

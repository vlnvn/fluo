# Threat model

Assets: audited joblib/stream/catalog, event history, sessions/reviews/preferences/notes, reports and future deployment/IdP secrets. Facility identity is fictional, but user-entered notes could be sensitive and remain local/ignored.

Actors: trusted local presenter, future authorized reviewer, another session, malicious website targeting localhost, anonymous internet actor, compromised build/dependency actor.

Boundaries: browser ↔ Vite/loopback FastAPI; JSON schema ↔ original inference; immutable predictions ↔ mutable clock; API ↔ SQLite; note ↔ HTML/PDF; build ↔ future registry/host; future identity proxy ↔ protected origin. No physical equipment boundary exists.

| Threat | Current control / evidence | Residual |
|---|---|---|
|Anonymous / cross-session reads/writes|Separate UUID records are data partitioning only; negative test exposes missing ownership|Critical external blocker; authenticated principal/owner/guest policy needed on every object/PDF/preview route|
|Hostile browser origin / rebinding|Local Host allowlist, hostile mutating Origin rejected, no permissive credential CORS|Direct clients can forge headers; not authentication|
|Oversize/chunk/slow body/request floods|4MiB cap,10s body timeout,8192-byte query, per-process rate windows|Local single-IP budgets are not distributed public abuse control|
|Model/data tampering or oracle leakage|Exact model/sensor/catalog digest guards;13 inputs; original causal gates; startup cache|Same simulator family, no field validation|
|HTML/PDF injection or framing|Escaping, nonce script CSP, same-origin frame policy, nosniff, no remote-URL/upload feature|Inline layout styles remain allowed; no complete browser-security certification|
|Lost/conflicting records|WAL/lock/busy timeout, revision200/409, backup/reopen/integrity and version guard|One worker; cloud volume, multi-process CAS/retention not verified|
|Supply chain/secrets|npm/runtime locks, actual installed advisory scan, Bandit, bounded history pattern scan|Unknown issues and scanner gaps remain; image digest/build unverified|
|Future ingress bypass/HTTP/spoofed identity|Nonlocal release mode refuses startup; no public deployment|Signed identity, private origin, TLS, expiry/logout/CSRF and direct-origin negative tests required|

No actuators, verified industrial savings, physical diagnosis or safe recovery permission. Checklists do not authorize equipment recovery.

Risk-based references, not certification: [ASVS5.0](https://asvs.owasp.org/), [OWASP Top10:2025](https://top10.owasp.org/2025/), [session management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html).

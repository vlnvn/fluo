# Security gate checklist

Verdict: **BLOCKED_FOR_PUBLIC_ACCESS**. Local functional success does not establish authenticated staging. OWASP ASVS5.0 / Top10:2025 were adapted as checklists, not claimed certification.

| Control | Status | Evidence / disposition |
|---|---|---|
|Server identity/authentication, expiry/logout|NOT IMPLEMENTED|Avatar and UUID are not credentials; external blocker|
|Object ownership: sessions/events/reviews/PDF/preview|FAIL PUBLIC GATE|Anonymous negative test xfails because access succeeds; no silent waiver|
|HTTPS identity-aware ingress / signed assertion / origin bypass|NOT AVAILABLE|No verified host/IdP entitlement or external URL|
|Secure/HttpOnly/SameSite session cookies and CSRF|NOT APPLICABLE CURRENT; REQUIRED WITH COOKIE AUTH|No auth cookie. Origin defence is not a substitute for future CSRF/session controls|
|CORS/Host/Origin|PASS LOCAL SCOPE|Exact local hosts; no wildcard credentials; actual Host400/Origin403|
|Input/resource limits and errors|PASS LOCAL SCOPE|Byte/chunk/query/rate/timeout limits and safe correlation500|
|CSP/frame/nosniff/permissions policy|PASS BUILT SCOPE|Nonce-bearing report script, same-origin frames, no server version header; real report flows pass|
|Swagger/schema/debug exposure|LOCAL ONLY|Docs retained for research; future ingress must restrict or disable them|
|Model/data integrity and deserialization|PASS|Fixed trusted model SHA before load; sensor/catalog digests before scoring; corrupt tests|
|Schema and oracle isolation|PASS|13-field finite/timezone/cadence contract; no labels in inference; output quality metadata only|
|SQL/HTML/PDF/path handling|PASS TESTED SCOPE|Parameterized SQL, escaping, built static root, malformed route recovery; no CSV/remote fetch feature|
|Revision conflict / backup / schema|PASS ONE WORKER|Concurrent200/409, restart/backup/integrity and newer-version refusal|
|Cloud persistence / redeploy / disk permissions|NOT TESTED|No provider or Docker runtime; no hosted durability claim|
|Dependency advisories|PASS KNOWN FINDINGS AFTER PATCH|97 initial advisory records in Pillow12.3/pypdf6.10; patched13.0.0/6.21.2; installed/runtime-lock scans now0; ML versions untouched|
|SAST / secret patterns|PASS SCANNED SCOPE|Bandit backend0; bounded history/working-source patterns0; not proof of arbitrary secret absence|
|Build provenance / licenses|PARTIAL|npm/runtime locks and font licenses retained; image digests/build unverified; no research relicense/upload|
|Operations and resource capacity|PARTIAL|Loopback, readiness/live, one worker and bounds; no cloud monitoring/soak/distributed limits/confirmed budget|
|Scientific safety|PASS SOFTWARE CONTRACT|Read-only, provenance, ambiguous cause, recovery unknown; no industrial metrics claim|

`tools/release_gate.py --target staging` exits2. Nonlocal `FLUO_RELEASE_MODE` also refuses startup. No environment flag is a replacement for an auth implementation. Docker recipe is local-only and NOT BUILT here.

Sources: [ASVS](https://asvs.owasp.org/), [Top10:2025](https://top10.owasp.org/2025/).

# Post-implementation audit — 25 October 2026

Baseline: clean `3f393fe`, branch `feat/fluo-fullstack-audited-replay`. Implementation: `e84b5ca5630cfbaa0f3880507a8c7268d1769cf4`. Remote main still `f2c05af115f374848ee3b8592a32af8648afea53`. No reset, rebuild, push or private-source upload. Previously working features were retained.

The verification story is operator action → typed API → immutable audited inference/replay → SQLite review → rendered evidence/report. A fresh code and negative-test pass was performed; this is not an external security certification.

## Issue ledger

| ID | Symptom / source target | Root cause | Change | Severity | Test / evidence | Status |
|---|---|---|---|---|---|---|
|UI-01|Inactive navigation, Figma74/128 shells|Prior neutral styles existed; baseline test sampled a route transition|Retain styles, await canonical aria-current; verify both shells|P1|corrections.spec; screenshots|VERIFIED|
|UI-02|Production casing|Previously corrected display formatter|Retain formatter in pages/detail/report, raw API unchanged|P1|four reports and casing assertions|VERIFIED|
|UI-03|Unread badge inconsistency|Previous exact session/site policy existed; preview needed shared view state|Shared preview/committed selector and recent/unread totals; preserve explicit read action|P1|routes/tabs/reload tests|VERIFIED|
|UI-04|Thick review-items line, Figma bars|Previous13-bin SVG correction existed|Retain real counts, separated bars and zero-bin baseline|P1|sum/gap assertions; Full/Compact|VERIFIED|
|UI-05|Repeated report toolbar|Previous embedded fix existed; new CSP needed script nonce|One visible parent toolbar; nonce-bearing print script|P1|four event PDF/print/back/close tests|VERIFIED|
|UI-06|Review action spacing / duplicate writes|10px gap existed; state-only save lock could race|12px wrapping gap; immediate ref lock; explicit draft feedback|P1|rapid double click,409, reload|FIXED|
|UI-07|Smooth buffered scrub|Thumb changed locally but dependent data waited|Read-only cached snapshot preview; one committed seek|P1|pointer/live chart/no clock mutation|FIXED|
|UI-07A|Legacy slider/scrollbars|Browser-default appearance|Light track/thumb/focus/scrollbar styling and reduced motion|P2|screenshots and motion recording|FIXED|
|UI-07B|Stale data during drag|Only slider state was local|80ms preview throttling, stale abort/version guard, suspend polling; render actual preview frames|P1|touch, playing2x, delayed response tests|FIXED|
|UI-07C|Forward transport|Previously implemented10-sample action|Retain symmetric control and clamps|P1|bounds/round trip API and browser|VERIFIED|
|UI-07D|Chime integration|Exact asset existed; old playback tests instrumented|Verify source hash, decode, native playback and rejection|P1|native-audio.json; SECURITY_INVENTORY|VERIFIED|
|UI-08|Warning popup reliability|No automatic visual cue with sound off|Actionable nonmodal toast on natural new warning; manual bell history|P1|cross-route warning and silent seek tests|FIXED|
|UI-09|Card metric meaning|Interruption total included mode/warmup|Structured quality_action; count only gateway/return-meter interruptions; retain progress/real trends|P1|new unit test; API counts|FIXED|
|UI-10|Missing favicon|No icon/manifest links|Original vector F crop; SVG/ICO/PNG and metadata|P2|built asset checks; inspected render|FIXED|
|AUD-01|Malformed deep-link crash|decodeURIComponent could throw|Safe decode fallback and event recovery|P1|malformed URL / retry E2E|FIXED|
|SEC-01|Anonymous cross-session object access|No authenticated identity/ownership|Keep loopback; explicit negative xfail; block staging|P0 public|test_anonymous_client_cannot_read_another_session|BLOCKED_FOR_PUBLIC_ACCESS|
|SEC-02|Unbounded request surface|Missing byte/rate/host/origin boundary|4MiB/chunk cap,10s body timeout, rate/host/origin limits, CSP and safe500|P1|test_audit.py; live smoke|FIXED_LOCAL_SCOPE|
|SEC-03|Installed advisories|Fresh resolver hid old installed Pillow/pypdf|Patch13.0.0/6.21.2; runtime lock; installed rescan|P1|before/after advisory JSON|FIXED|
|DATA-01|Runtime data integrity|Data hashes were reported but not enforced|Sensor/catalog startup digest guard; original bytes unchanged|P1|corrupt dataset test; preparation|FIXED|
|DB-01|Restart/backup/version evidence|Missing guard/backup/close helpers|WAL/busy timeout, version0→1, newer-schema refusal, backup and concurrency checks|P1|reopen/integrity/200+409 tests|FIXED_LOCAL_SCOPE|
|DEP-01|Protected deployment unavailable|No verified hosting/IdP entitlement; no Docker engine; auth missing|Local packaging/runbook; no external exposure|P0 release|RELEASE_DECISION.json|BLOCKED|

All new fixes above belong to implementation `e84b5ca`; VERIFIED rows retain work from `3f393fe`. ISSUE_MATRIX.json provides the same fields with commit/evidence paths.

## Findings and gates

Baseline:14 API passed; browser7passed/1failed. The failed icon test read computed style during navigation; awaiting aria-current fixed synchronization, not a persistent color defect. Final:21 Python passed plus1 explicit auth xfail;3 frontend units;16 DEV and16 BUILT E2E;8 screenshot assertions;10 scoped Axe scans with0 findings. Ruff/typecheck/ESLint/build passed.

Frozen model, sensor/catalog and86,400-row original inference parity verified; original research scripts/model have no Git diff from main. Initial installed Pillow12.3/pypdf6.10 returned97 advisory records in2 packages; patched installed/runtime-lock scans now0. npm/Bandit and bounded secret-pattern scan show0 findings in their assessed scope.

Before captures: `post-audit/before`; after captures/video: `post-audit/after`. Core comparisons use the default paused scenario/cursor. Live-preview captures intentionally use a dragged cursor. Artifact hashes: POST_AUDIT_ARTIFACTS.json. Figma references/large captures stay local.

Decision: LOCAL_DEMO_READY for a trusted single-user loopback demonstration; BLOCKED_FOR_PUBLIC_ACCESS. Missing authentication and object ownership are unresolved public P0s, not waived by passing functional tests. No zero-bug/pixel-perfect/production/field-validation claim.

# Fluo implementation and QA report

Latest release evidence: [FINAL_RELEASE_AUDIT](docs/implementation/qa/FINAL_RELEASE_AUDIT.md), [handoff](docs/implementation/PROPOSAL_EVIDENCE_HANDOFF.md), [video](docs/implementation/demo/DEMO_SCRIPT.md), [security/release](docs/implementation/deployment/SECURITY_CHECKLIST.md). Current results:26 Python,0 xfail/skips;3 units;18 DEV and18 BUILT E2E. Guest authentication/ownership implemented; PUBLIC_DEPLOYMENT_BLOCKED pending hosting/budget and actual hosted tests. Everything below is historical delivery context.

Latest follow-up: [UI corrections and regression QA](docs/implementation/qa/UI_CORRECTIONS_20261025.md). The initial delivery evidence below is retained as historical context.

25 October 2026 (Asia/Jakarta). Implemented code revision: **f32b0a8dc1c32fe0c0504ca04d59dc8a8f4f133b**; backend revision cb04b96. Branch `feat/fluo-fullstack-audited-replay`, based on verified GitHub main `f2c05af115f374848ee3b8592a32af8648afea53`. This report/evidence is committed separately; `git log -1` identifies the final documentation revision. No push, deployment or private-source upload was performed.

Fluo now runs end-to-end locally: actual frozen HGB inference, recorded telemetry, nine scenarios, replay, four operator pages, event evidence, persisted independent checklists/notes, explicit review submission, contextual overlays/preferences, real PDF and A4 print. Original research code, model, reports and ZIP were preserved.

## Gate result

| Gate | Status | Executed evidence |
|---|---|---|
|0 Forensic inventory|PASS|82 ZIP members, CRC and all available package checksums; identical archive/repository HGB; cloud Doc/Figma read; SOURCE_MANIFEST.json|
|1 Reproducible inference|PASS|86,400 locked rows, exact repeated predictions and chronological-prefix parity on five configurations; tolerance0; original legacy QA exit0; no training|
|2 Architecture/contracts|PASS|ADR, generated Pydantic→OpenAPI/TypeScript, state/token map,83-frame Figma trace|
|3 Figma UI|PASS with documented visual differences|Original SVG/fonts, Full/Compact geometry, Light shell;20 screenshot comparisons; no claim of pixel identity|
|4 Actual model/data integration|PASS|Real original stream scored at startup;13-field sensor-only inference; normal/deficit/bias/lag/outage/mode scenarios and gates exercised|
|5 Interactions|PASS|Replay/navigation/filter/context overlays, local drafts/submission, four event-specific PDF/print contexts, preferences/sound tested|
|6 QA|PASS within stated coverage|14 API/model tests,2 chart unit tests,6 E2E on development and6 on built single-origin server; lint/typecheck/build/Ruff exit0; Overview Axe0 A/AA violations|
|7 Reproducible delivery|PASS|setup.ps1 succeeded from lockfile; one-command dev launcher actually started both servers; HTTP200 for API/dev/built frontend; README and this report|

Visual acceptance here means implemented and compared, with remaining differences disclosed. It does not certify pixel-perfect matching or every possible combination of the83 source frames. Scientific/field readiness is outside these software gates.

## Requirement → source → implementation → evidence

| Requirement | Authoritative source | Implemented file(s) | Test / capture | Status |
|---|---|---|---|---|
|Preserve provenance and frozen artifact|Audited ZIP; GitHub main; DEEPTECH alven2|tools/audit_sources.py; inference_adapter.py; SOURCE_INVENTORY/CONFLICTS|SOURCE_MANIFEST.json; checksum guard test|PASS|
|Original six causal features and gates|run_fluo_v2.py; frozen_selection.json|backend/inference_adapter.py invokes unchanged original|INFERENCE_VERIFICATION.json; legacy-qa.log; tests/test_api.py|PASS|
|No simulator-label leakage or field claim|Model card; masterprompt|strict TelemetryRow; service frame/event derivation; status/report metadata|extra oracle fields rejected; startup lineage; API tests|PASS|
|Typed shared API and replay cursor|Masterprompt E/G|schemas.py; service.py; App.tsx; contracts.ts|OpenAPI; deterministic pause/seek/reload tests|PASS|
|Four pages and Full/Compact|Figma74:2/107/198/302 and128 variants|Views.tsx; Chart.tsx; styles.css|overview/scenario/events/details full+compact PNG; geometry.json|PASS, visual differences documented|
|83 frame mappings / original assets|Figma inventory and reactions|FIGMA_TRACEABILITY.md; public/assets; STATE_AND_TOKENS.md|20 reference comparisons; img naturalWidth checks|PASS for mapping; representative rendering coverage|
|Three filter categories, contextual overlays|Figma124/128 filters;170 overlays|App.tsx; components.tsx Dialog|six filter captures; notification/help/profile/preferences captures; keyboard/focus tests|PASS|
|Actual chart data and gaps|Original CSV timestamps/units|Chart.tsx; immutable sensor frames|2 unit tests; Full/Compact extent assertions; UI/API reading equality|PASS|
|Persist independent operator drafts/submission|Masterprompt checklist contract|store.py; review routes; EventDetails form|four events, Space checkbox, note Save draft/reload, explicit submit; conflict409|PASS|
|Genuine per-event PDF and A4|Figma130:2 and173 reports; masterprompt|reporting.py; App summary/iframe print|four downloaded PDFs; parsed event/time/quality/provenance; browser-print.pdf; A4 render|PASS|
|Opt-in warning audio|Figma Preferences; supplied MP3|App notification effect; local chime asset|sixth E2E crosses an actual HGB warning; no mount/seek/reload cue|PASS logic; audio playback method instrumented|
|Safe local interface|Masterprompt safety|SHA guard; strict schemas; escaped HTML/PDF; local SQLite|corrupted artifact rejected; XSS escaped; no actuation routes|PASS local prototype scope|
|Reproducible installation and run|Masterprompt Gate7|setup.ps1; tools/dev.py; requirements; lockfile|setup.log; STARTUP_VERIFICATION.json; production E2E|PASS on this Windows host|

## Actual source and model verification

ZIP SHA256 `7ad2b4a94a3147241641ff839853c927828ca077858bc801c6e7c157d3c5d5ca` (40,775,479 bytes). Model SHA256 `5237917ae6ccfccd2ff21d288b92201536c923028d8931599aaf9715033e9b09`. Locked verification stream SHA256 `162ed5816208929ce8f95822c16afbcd8d3f8061719bde1f0c471acf5eea5ada`; runtime original stream SHA256 `f9fe34bf04a31e753df47c6f736f5155a4eaf34a8a6dedf7b6b5a53ed00ce018`. They are different evaluation/runtime cohorts, not interchangeable metrics.

Verification output digest `276bcd03bcd1be4d1d7c708f53e4cba49cce4b5b18b1b6bb5161345a24c3cf93`;86,400 locked rows;3,755 warning-minutes. These counts describe reproduced synthetic outputs, not measured factory accuracy/savings. Python3.12.14, numpy2.3.5,pandas2.2.3,scipy1.16.3,sklearn1.8.0,joblib1.5.2. Verification inference took1.220s on this host; not a production throughput guarantee.

Original upstream inference fails on zero-valid-row prefixes. The adapter only intercepts empty predict_proba inputs and returns an empty(0,2) matrix; nonempty calls remain original. Fifteen upstream failures were observed in causal-prefix checks and are recorded explicitly. Original source persistence behavior is preserved despite a contradictory comment. Simulator seed identifiers containing future-looking dates were not interpreted as completed future experiments.

Google Docs DEEPTECH was retrieved with its alven2 tab and24Oct2026 modification metadata. Figma file M1xy04eLqGOsjH505y99mW was accessed through connected API;83 active frames and prototype reactions were inspected. Full source text/reference exports stay local, excluded from commits. No partner/hardware access was inferred.

## Commands actually executed

| Command | Exit | Observed result |
|---|---:|---|
|python tools/prepare_runtime.py|0|ZIP,package checksums,original data,model verified; no training|
|python tools/verify_inference.py|0|Exact repeat/prefix parity and legacyQA0; INFERENCE_VERIFICATION.json|
|python -m pytest -q --basetemp=.local/pytest-final-pass --tb=short|0|14passed,1 Starlette/httpx deprecation warning,7.14s|
|python -m ruff check backend tools tests|0|All checks passed|
|npm run typecheck / npm run lint / npm test / npm run build|0 each|TypeScript/ESLint passed;2 tests passed; Vite production bundle built|
|npx playwright test (5173)|0|6passed,22.5s; e2e.log|
|FLUO_BASE_URL=8000 npx playwright test|0|6passed,20.9s; e2e-production.log and e2e-results.json|
|npm audit --json|0|0 reported vulnerabilities; npm-audit.json|
|setup.ps1, with Fluo stopped|0|Pinned Python dependencies + npm ci;283 packages installed,0 vulnerabilities|
|python tools/dev.py|running|Both services ready; API/dev/built URLs returned200|
|python tools/design_audit.py|0|83 mapped frames,20 comparisons; VISUAL_COMPARISON.json|
|pdftoppm first page ofEV019|0|A4 report rendered and visually inspected|

Failures found and fixed: upstream zero-valid prefix crash; native modal Tab escaping to the background; PDF test capitalization mismatch after the new report; iframe-only A4 screenshot clipping (capture moved to standalone printable document). Setup initially failed because running esbuild.exe was locked by Windows; servers were stopped, a preflight port check added, and setup reran successfully. These superseded failures are not reported as successful runs.

Browser tests assert actual frozen values against API, pause/clock/scenario behavior, persisted state and reviews, filter Apply/Reset/Escape, loaded original images, zero console/HTTP errors in the core route traversal, download bytes and print invocation. Print invocation is instrumented to avoid blocking OS dialogs; Chromium also generated browser-print.pdf from the genuine HTML/A4 CSS. No visible native printer dialog or physical printer output is claimed. Audio.play is instrumented to verify trigger rules; acoustic playback and OS volume are not measured. Downloaded reviewed PDFs contain a summary plus review-note/audit appendix (two pages for tested records).

Accessibility: automated WCAG A/AA scan covers Overview; keyboard paths cover modal focus, Escape, checkbox Space and focus restoration.1180px desktop overflow is checked. This is not a comprehensive screen-reader, mobile or cross-browser certification.

## Visual evidence

Local artifacts: `docs/implementation/qa/figma/` reference images, `screenshots/` actual browser/PDF output, `visual-diffs/` side-by-side Figma/implementation/difference×3. Metrics and explanations are retained in VISUAL_QA.md / VISUAL_COMPARISON.json. Full/Compact core frames, six filters, five contextual dialogs and A4 are compared. Filter reference shadows are cropped23px per side to the specified675×624 panel. Chromium's outward1px A4 screenshot rounding is cropped, not rescaled.

Overview Full mean absolute RGB error4.2886/255,3.7451% pixels with a channel error>20. A4 error5.8582/255,5.7623% pixels>20. These are descriptive image differences, not pass thresholds. Real telemetry, dates, state-derived event IDs, truthful evidence and unconfirmed diagnosis replace Figma's illustrative contents. Windows font rasterization, additional seek/search/submission controls and metadata also differ. Report notes/audit use an appendix so they do not overlap the Figma A4 summary. Original SVGs are rendered as assets; screenshots are not used as the UI.

## Exact run and next validation

From `C:\College\DEEPX\fluo`, run `.\setup.ps1` once with servers stopped, then `.\.venv\Scripts\python.exe tools\dev.py`. Open http://127.0.0.1:5173. Stop withCtrl+C. Production build and all test commands, prerequisites and environment overrides are in README.md. Existing .local SQLite data persists; new browser sessions isolate operator review records.

Remaining limits: this is a local research prototype with unverified operator identities and synthetic telemetry, not industrial validation/TKT4 or a production deployment. No valve/boiler/pump control, connected ESP32, diagnosed physical loss, validated savings, safe recovery authorization or plant partner is implied. Recovery requires independent instrument, quality, installation and SOP review. Do not expose the unauthenticated local service publicly. The model/joblib source is trusted only after its fixed hash matches. Original rights/license restrictions remain in force; external sharing needs the owner's authorization.

Practical next steps: the team should review remaining visual differences in the supplied comparison sheets; conduct a supervised operator walkthrough with the real intended customer; then obtain authorized telemetry/meter calibration and engineering input for field validation. Extend accessibility/browser/device coverage before broader deployment. Those actions are future validation, not implemented or successful pilot claims.

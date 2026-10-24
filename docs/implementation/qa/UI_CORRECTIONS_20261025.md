# UI corrections — 25 October 2026

Implemented from the user's six screenshots and listed behavior gaps, on the existing Fluo branch. Original HGB, research results and source telemetry were not changed. Final local revision is available with `git log -1`; baseline was33682e2.

| Reported issue | Correction | Verification |
|---|---|---|
|Blue inactive navigation icon|Inactive sidebar/utility icons use the muted color filter; active navigation retains blue. Original SVG files preserved.|Each route's active/inactive computed styles and visual Full/Compact inspection|
|Lowercase production label|Presentation formatter displays Production in Overview, event evidence, summary and HTML/PDF qualification. Raw ML/API mode remains production.|Overview, detail and printable evidence assertions|
|Inconsistent notification counts|One exact unread count from the current session/site event snapshot, without9+ truncation. Opening the panel no longer silently marks all read. Explicit Mark all as read persists session/site-scoped IDs. Browser storage events synchronize open tabs.|Stable count across three routes, open/close, reload; two tabs synchronize the explicit read action|
|Review-items visual becomes a solid bar|Replace flex-stretched, near-flat reading bars with13 separate SVG bins counting actual return events over the returned recorded history. Zero-event bins are baseline marks, not invented events.|13 rectangles with real gaps; sum equals the corresponding counter; no added/random samples|
|Empty right sides of other summary cards|Data interruptions uses the same histogram language with the exact quality-event subset used by its counter. Review window shows elapsed replay percentage. Overview's three numeric cards include small trends from available actual frames.|Counts compared to API events; progress label; Full/Compact screenshot inspection|
|Repeated print toolbar|Embedded report URL uses?embedded=true; its own toolbar is hidden. The parent preview owns one Close, Print A4 and Back to summary. Standalone report retains its toolbar.|Four event reports; embedded visible buttons0, parent Close1/Print1; genuine downloads and print-invocation tests|
|Touching review buttons|A wrapping flex action group has a10px gap.|Bounding rectangles and review-actions.png|
|Choppy seek dragging|Range input maintains a local draft while pointer is held, captures its pointer and commits one backend seek on release. Keyboard seek commits on key-up; non-pointer input has a120ms fallback. Backend frames still provide committed values.|30 pointer moves with zero seek requests during drag, exactly one after release; input remains enabled during drag; keyboard Home/End|
|Missing forward control|Add Forward10samples using the original rewind icon mirrored; backend advances10 and clamps to the final sample. Rewind remains10 and clamps at0. Generated OpenAPI/TS contract updated.|Browser forward/backward round trip and endpoints; API near-end and start-boundary assertions|

## Actual final verification

- `npm run typecheck`, `npm run lint`, `npm test`, `npm run build`: exit0;2 chart unit tests passed.
- `python -m ruff check backend tools tests`: exit0.
- `python -m pytest -q --basetemp=.local/pytest-corrections-final --tb=short`: exit0;14passed in8.60s. Existing Starlette/httpx deprecation warning remains.
- `FLUO_BASE_URL=http://127.0.0.1:8000 npx playwright test`: exit0;8passed in32.3s on the latest production bundle. It includes the original route/replay/filter/review/PDF/audio/accessibility cases and two targeted correction workflows.
- Initial correction QA exposed an ambiguous test heading selector, a pointer test targeting the off-screen range, and embedded-toolbar CSS overridden by a later generic rule. Tests were corrected to target the intended heading/visible range, pointer capture was added, and embedded hiding was made authoritative; full suite reran successfully.
- Screenshots were visually inspected for1440×900 Full/Compact layouts, one-toolbar A4 preview, review-action spacing and1180px Compact scenario controls. Existing Overview Axe scan remains zero violations within its stated A/AA coverage; this is not an all-browser/accessibility certification.

## Evidence

Screenshots are local (ignored by Git); file dimensions and hashes are committed in CORRECTIONS_SCREENSHOTS.json.

- [Overview, muted inactive icons and observed mini trends](corrections/overview-full.png)
- [Event summaries, Full](corrections/events-full.png)
- [Event summaries, Compact](corrections/events-compact.png)
- [Review button spacing](corrections/review-actions.png)
- [One print toolbar](corrections/print-single-toolbar.png)
- [Forward control and replay range, Full](corrections/scenario-controls-full.png)
- [Forward control and replay range, Compact](corrections/scenario-controls-compact.png)
- [Narrower desktop](corrections/scenario-controls-narrow.png)

Logs: e2e-corrections-production.log, api-corrections.log. Latest structured browser results: e2e-results.json. Figma comparisons were regenerated for20 representative states; VISUAL_COMPARISON.json / VISUAL_QA.md describe the differences. The additional visuals and forward control follow the user's requested extension of the original design; they are not claimed to exist in Figma.

## Semantics and limits

Badge counts can legitimately change as replay advances, the cursor moves backward or the selected scenario/configuration changes. They do not change merely because a page or notification panel opens. Read state is scoped to a local session/site and synchronized between same-origin browser tabs; localhost:5173 andlocalhost:8000 remain distinct browser origins.

Histogram heights represent counts of the returned recorded events, not condensate volume, fault probabilities or invented telemetry. Empty bins retain only a faint baseline. Review-window percentage is cursor/(total_frames-1), zero at the start and100 at the end. Small reading trends are independently scaled per sensor and leave missing values as gaps; their accessible labels disclose this. Detail charts change after committing a seek, while the slider/position label follows the pointer locally.

No inference parameters, scientific metrics or model artifact changed. No external deployment or Git push was performed. Application remains read-only and based on simulated research telemetry.

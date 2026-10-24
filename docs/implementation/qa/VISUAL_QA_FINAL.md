# Visual QA — final

Current Figma file `M1xy04eLqGOsjH505y99mW` was re-read:83 active frames; Full74:2 / Compact128:5. Shell/icon/filter/card properties and prototype reactions were inspected. Existing high-fidelity contexts, original SVGs and20 trusted exported references were reused. Google Docs DEEPTECH/alven2 remained readable; no private text dump was published.

Windows/Chromium153.0.8010.12; scale1;1440×900; bundled Archivo/Barlow Condensed. Screenshots disable animations, while the motion video retains them. Dynamic readings/history/event IDs differ from illustrative Figma contents. Windows font rasterization also differs. Neither MAE nor screenshot regression implies pixel identity.

Full metrics: VISUAL_COMPARISON.json / VISUAL_QA.md. Twenty comparisons include eight core Full/Compact frames, six filters, five contextual panels and A4. Filter reference shadows are cropped to675×624; A4 screenshot rounding crops1px without rescaling. Eight paused implementation baselines pass Playwright toHaveScreenshot with animations disabled and maxDiffPixels100, without updates during final suites. Their purpose is regression stability, separate from Figma comparison.

Frame mapping: Overview74:2/128:5; Scenario74:107/128:144; Events74:198/128:286; Details74:302/128:422; filters124/128; notifications170:2; summary170:106; A4130:2. FIGMA_TRACEABILITY maps83 states and identifies representative coverage.

Spatial evidence: post-audit/after/geometry-final.json contains header/sidebar/first-card bounds and overflow for all routes in Full/Compact. Header70px and sidebar225/76px remain canonical. Chart extent/expansion and filter dimensions are asserted. Additional1024/1280 Compact probes report0 horizontal overflow;1180px coverage is retained. Full and Compact screenshots, review spacing, one-toolbar print, live preview and actual motion video are available locally; hashes in POST_AUDIT_ARTIFACTS.json.

Before/after use matching default paused scenario/cursor for core views. Drag captures intentionally use another cursor. New graphics/forward/F favicon/slider styling are user-approved extensions, not claimed original Figma components. Interruptions now mean only gateway offline or interrupted return-meter gates; mode/warmup/restoration are excluded. Histograms use actual counts, faint empty baselines and no fabricated staggered heights. Overview mini trends are independently scaled from available readings.

Residual differences include truthful scientific content/provenance, additional controls and platform font rendering. All83 combinations and browsers were not rendered. The recording probe initially needed the matching encoder, then base-URL/loading synchronization fixes; only its completed exit0 pass is claimed. Intermediate failed probe clips remain local and are not presented as successful motion evidence.

## Measured Figma comparison

| State | Mean RGB error (0–255) | Pixels with channel error >20 |
|---|---:|---:|
|overview-full|4.3279|0.038087|
|overview-compact|4.3237|0.037614|
|scenario-full|9.4743|0.142357|
|scenario-compact|4.073|0.035586|
|events-full|3.6521|0.035914|
|events-compact|3.5909|0.036172|
|details-full|4.7071|0.045051|
|details-compact|4.6815|0.045035|
|filter-all-full|10.7096|0.14632|
|filter-return-full|10.7419|0.143079|
|filter-quality-full|10.7694|0.147429|
|filter-all-compact|10.7067|0.14632|
|filter-return-compact|10.739|0.143079|
|filter-quality-compact|10.7665|0.147429|
|notifications|7.4854|0.061083|
|preferences|8.0143|0.060074|
|help|7.4149|0.063099|
|profile|5.3638|0.047818|
|inspection-summary|9.0186|0.077224|
|a4-document|5.8514|0.0576|

SPATIAL_CHECKS.json reports header/sidebar absolute size errors of0px and0 horizontal overflow in the measured probes. These spatial facts do not imply every label/card matches Figma. BEFORE_AFTER_COMPARISON.json separately compares matched baseline/current paused captures.

# Visual QA — measured differences

The application is not claimed pixel-identical. Original Figma renders are compared to actual Chromium screenshots at 1440×900. Charts, values, dates, event identifiers, gate states, queue counts and provenance are sourced from real archived synthetic telemetry and intentionally differ from illustrative Figma values. Full-frame error is therefore not a pure layout metric. Overlay comparisons crop the panel; filters compare the standalone white panel. Windows Chromium and Figma font rasterization also differ.

| State | Mean RGB error (0–255) | Pixels with >20 channel error | Comparison |
|---|---:|---:|---|
| overview-full | 4.3279 | 0.038087 | COMPARED_NOT_PIXEL_IDENTICAL |
| overview-compact | 4.3237 | 0.037614 | COMPARED_NOT_PIXEL_IDENTICAL |
| scenario-full | 3.9382 | 0.033892 | COMPARED_NOT_PIXEL_IDENTICAL |
| scenario-compact | 4.073 | 0.035586 | COMPARED_NOT_PIXEL_IDENTICAL |
| events-full | 3.7858 | 0.037219 | COMPARED_NOT_PIXEL_IDENTICAL |
| events-compact | 3.7392 | 0.037519 | COMPARED_NOT_PIXEL_IDENTICAL |
| details-full | 4.7071 | 0.045051 | COMPARED_NOT_PIXEL_IDENTICAL |
| details-compact | 4.6815 | 0.045035 | COMPARED_NOT_PIXEL_IDENTICAL |
| filter-all-full | 10.7096 | 0.14632 | COMPARED_NOT_PIXEL_IDENTICAL |
| filter-return-full | 10.7419 | 0.143079 | COMPARED_NOT_PIXEL_IDENTICAL |
| filter-quality-full | 10.7694 | 0.147429 | COMPARED_NOT_PIXEL_IDENTICAL |
| filter-all-compact | 10.7067 | 0.14632 | COMPARED_NOT_PIXEL_IDENTICAL |
| filter-return-compact | 10.739 | 0.143079 | COMPARED_NOT_PIXEL_IDENTICAL |
| filter-quality-compact | 10.7665 | 0.147429 | COMPARED_NOT_PIXEL_IDENTICAL |
| notifications | 7.3111 | 0.060069 | COMPARED_NOT_PIXEL_IDENTICAL |
| preferences | 8.0143 | 0.060074 | COMPARED_NOT_PIXEL_IDENTICAL |
| help | 7.0124 | 0.060547 | COMPARED_NOT_PIXEL_IDENTICAL |
| profile | 5.3638 | 0.047818 | COMPARED_NOT_PIXEL_IDENTICAL |
| inspection-summary | 9.0186 | 0.077224 | COMPARED_NOT_PIXEL_IDENTICAL |
| a4-document | 5.8514 | 0.0576 | COMPARED_NOT_PIXEL_IDENTICAL |

## Deliberate implementation differences

- Illustrative readings and fixed EV-018 contents are replaced by actual scored replay values and deterministic state-change IDs.
- Data provenance is visible in a restrained status footer and report metadata.
- Search/pagination, replay seek and the explicit evidence/review submission form extend the static design to satisfy functional requirements; the review form is below the canonical first viewport.
- The seven principal scenarios retain the Figma ordering. Two additional archived quality/mode windows are available below the scrollable scenario library.
- Filters and contextual overlays retain the white Light panel geometry; no navy canvas is used.
- User-directed corrections (25 October): exact unread badges and explicit read action; muted inactive icons; capitalized mode labels; 13-bin event histograms, replay-window progress and small observed KPI trends; forward replay, local drag scrubbing and one embedded print toolbar. New visuals/controls intentionally extend the original Figma.
- No numeric threshold is used to relabel these differences as pixel-perfect. Original references, implementation captures and ×3 difference images are retained locally.

Geometry assertions, real asset load checks, native keyboard controls, modal focus containment, reduced motion and narrower desktop overflow are tested in Playwright. See `screenshots/geometry.json` and `e2e-results.json`.
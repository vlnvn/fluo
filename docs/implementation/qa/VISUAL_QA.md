# Visual QA — measured differences

The application is not claimed pixel-identical. Original Figma renders are compared to actual Chromium screenshots at 1440×900. Charts, values, dates, event identifiers, gate states, queue counts and provenance are sourced from real archived synthetic telemetry and intentionally differ from illustrative Figma values. Full-frame error is therefore not a pure layout metric. Overlay comparisons crop the panel; filters compare the standalone white panel. Windows Chromium and Figma font rasterization also differ.

| State | Mean RGB error (0–255) | Pixels with >20 channel error | Comparison |
|---|---:|---:|---|
| overview-full | 4.2886 | 0.037451 | COMPARED_NOT_PIXEL_IDENTICAL |
| overview-compact | 4.2844 | 0.036978 | COMPARED_NOT_PIXEL_IDENTICAL |
| scenario-full | 3.7179 | 0.031762 | COMPARED_NOT_PIXEL_IDENTICAL |
| scenario-compact | 3.8567 | 0.033431 | COMPARED_NOT_PIXEL_IDENTICAL |
| events-full | 3.5466 | 0.03451 | COMPARED_NOT_PIXEL_IDENTICAL |
| events-compact | 3.5009 | 0.035097 | COMPARED_NOT_PIXEL_IDENTICAL |
| details-full | 4.7131 | 0.045221 | COMPARED_NOT_PIXEL_IDENTICAL |
| details-compact | 4.6876 | 0.045205 | COMPARED_NOT_PIXEL_IDENTICAL |
| filter-all-full | 10.7096 | 0.14632 | COMPARED_NOT_PIXEL_IDENTICAL |
| filter-return-full | 10.7419 | 0.143079 | COMPARED_NOT_PIXEL_IDENTICAL |
| filter-quality-full | 10.7694 | 0.147429 | COMPARED_NOT_PIXEL_IDENTICAL |
| filter-all-compact | 10.7084 | 0.14632 | COMPARED_NOT_PIXEL_IDENTICAL |
| filter-return-compact | 10.7407 | 0.143079 | COMPARED_NOT_PIXEL_IDENTICAL |
| filter-quality-compact | 10.7682 | 0.147429 | COMPARED_NOT_PIXEL_IDENTICAL |
| notifications | 7.1996 | 0.059338 | COMPARED_NOT_PIXEL_IDENTICAL |
| preferences | 8.0143 | 0.060074 | COMPARED_NOT_PIXEL_IDENTICAL |
| help | 7.0124 | 0.060547 | COMPARED_NOT_PIXEL_IDENTICAL |
| profile | 5.3638 | 0.047818 | COMPARED_NOT_PIXEL_IDENTICAL |
| inspection-summary | 9.0175 | 0.077218 | COMPARED_NOT_PIXEL_IDENTICAL |
| a4-document | 5.8582 | 0.057623 | COMPARED_NOT_PIXEL_IDENTICAL |

## Deliberate implementation differences

- Illustrative readings and fixed EV-018 contents are replaced by actual scored replay values and deterministic state-change IDs.
- Data provenance is visible in a restrained status footer and report metadata.
- Search/pagination, replay seek and the explicit evidence/review submission form extend the static design to satisfy functional requirements; the review form is below the canonical first viewport.
- The seven principal scenarios retain the Figma ordering. Two additional archived quality/mode windows are available below the scrollable scenario library.
- Filters and contextual overlays retain the white Light panel geometry; no navy canvas is used.
- No numeric threshold is used to relabel these differences as pixel-perfect. Original references, implementation captures and ×3 difference images are retained locally.

Geometry assertions, real asset load checks, native keyboard controls, modal focus containment, reduced motion and narrower desktop overflow are tested in Playwright. See `screenshots/geometry.json` and `e2e-results.json`.
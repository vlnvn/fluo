# Runtime API contract
Current security contract (25 October 2026): /docs, /redoc and /openapi.json HTTP endpoints are disabled. The generated file is an offline route/schema reference; middleware enforces authentication/ownership outside schema declarations. POST /api/v1/auth/guest requires X-Fluo-Intent: guest and a permitted Origin/Host. It returns guest expiry and a CSRF token, and sets an opaque HttpOnly cookie (public: __Host-fluo_guest, Secure, Strict). GET /api/v1/auth/session requires that cookie. All other /api/v1 routes require a valid unexpired/unrevoked guest. Every session-ID route checks server ownership before execution; anonymous401, foreign object404. Mutations require X-CSRF-Token (403 otherwise). POST /api/v1/auth/logout revokes server access and clears the cookie. CSRF stays in browser memory; localStorage retains only replay UUID/UI preferences. Public raw /inference is forbidden403; local research inference requires a guest and CSRF. /health/live and /health/ready are intentionally public minimal probes. Guest capability authentication does not verify human operator identity. Schema2 migration preserves legacy records privately; they are not auto-claimed by new guests.

The authoritative generated OpenAPI is `openapi.json`; TypeScript interfaces in `web/src/contracts.ts` are generated from Pydantic with `python tools/generate_contracts.py`. All endpoints are implemented under `/api/v1`.

| Capability | Request |
|---|---|
| Model/dataset lineage and availability | GET `/health` |
| Nine supported recorded scenario windows | GET `/scenarios` |
| Create a local replay session | POST `/sessions` `{ "scenario_id": "return-diversion" }` |
| Current snapshot, recent chart frames, historical events | GET `/sessions/{id}` |
| Replay controls | POST `/sessions/{id}/replay` `{ "action": "play" }`; pause, reset, rewind/forward (10 samples, clamped at bounds); seek with cursor; speed with 1/2; scenario with scenario_id |
| Search/filter/sort past events | GET `/sessions/{id}/events?category=all&search=&order=desc` |
| Event-specific context, evidence, review | GET `/sessions/{id}/events/{event}` |
| Persist draft | PUT `/sessions/{id}/events/{event}/review` `{ "checked_steps": [], "note": "", "revision": 0 }` |
| Explicitly submit local review | POST `/sessions/{id}/events/{event}/review/submit` same revisioned body |
| Preferences | GET/PUT `/sessions/{id}/preferences` `{ "warning_sound": false }` |
| Genuine A4 PDF attachment | GET `/sessions/{id}/events/{event}/report.pdf` |
| Escaped, event-specific printable HTML; ?embedded=true hides its toolbar inside the app | GET `/sessions/{id}/events/{event}/print` |
| Sensor-only frozen inference | POST `/inference` `{ "rows": [13-field telemetry], "run_mode": "SYNTHETIC_REPLAY" }` |

Snapshot `schema_version=1.0` includes session/scenario, cursor, speed, PLAYING/PAUSED/ENDED, current measurements, original triage/gate output, causal persistence count, up to 25 past chart frames, past events and lineage. Timestamps preserve source offsets; UI times use Asia/Jakarta. Steam/return are kg/h, pressure bar(g), temperatures °C. Missing readings/scores serialize as null; no interpolation over missing measurements.

One sample is one recorded minute. At 1× replay advances one sample per wall-clock second, at 2× two. This acceleration is a review interaction, not live industrial telemetry. Session state persists in local SQLite and the browser retains its local session ID. Scenarios reset deterministically to their first selected sample. The original full chronological site history supplies feature/gate history before a scenario window; seek never retrains or resets the scientific pipeline.

Event category comes from detector/gate state, never injected event labels. IDs follow per-configuration chronological transitions. CFG_B uses EV-001 etc.; other configurations include a site prefix. Thus illustrative EV-018 data in Figma is not copied into runtime EV-018. Time windows can include past state-change records before the selected chart interval; the event toolbar explicitly says recorded history through current time. Future event timestamps/peak scores are withheld.

Errors are non-200 JSON: `{ "error": { "code": "UNKNOWN_SESSION", "message": "...", "correlation_id": "..." } }`. Schema errors are 422, unknown resources 404, invalid cursor 400, conflicting review revision 409. No physical control routes exist. This is a loopback-only research application without verified identity/authentication; do not expose it publicly.

## Post-audit extension

GET /sessions/{id}/preview?cursor=N returns the same typed snapshot with is_preview=true without changing the stored clock/cursor or rescoring. Quality events expose original quality_action; Data interruptions counts only GATEWAY_OFFLINE/VERIFY_RETURN_METER. Preview polling is throttled80ms, versioned/aborted and never generates new-warning sound. Health/live and health/ready are separate local endpoints. See deployment/security docs for local-only guards and the unresolved authentication blocker.

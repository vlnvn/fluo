# Reviewer access and live Overview recording — 25 October 2026

P0 and P1 COMPLETE. Scope limited to reviewer-link rotation and video tooling. No application bug fix was needed. No proposal, ML research, frozen model, Figma, database or production deployment was changed; no rate limit was weakened and no paid resource was selected. Full prior audits were not repeated.

## P0 — access during judging

The old 23-hour capability was revoked and regenerated **without TTL** on the existing protected preview. The official API specifies no expiration when TTL is omitted. The complete link is only in ignored `.local/FLUO_REVIEWER_LINK.txt` / `.local/reviewer-link.json`; provider response is also private. Do not commit the capability or put it in the proposal. It still requires manual revocation after judging; no scheduled end date was invented.

Targeted fresh Chromium regression without OIDC: six steps passed—provider link, guest entry, Overview, navigation to Scenario Review and back, reload, logout. Separate clean HTTP checks: anonymous origin302, revoked old link302. Evidence: `../qa/vercel/reviewer-access-judging.json` and `reviewer-access-boundary-judging.json`. The unchanged hosted SHA is `ab3ebc9650cabdc9e90f46b3e27df0959a904f50`. See `../deployment/REVIEWER_ACCESS_JUDGING.md` for manual revocation and provider-cookie limitations. Existing guest TTL and database ownership remain unchanged. No-TTL does not guarantee provider uptime or protect a publicly leaked capability.

## P1 — actual local recording

Deliverables: `FLUO_LIVE_OVERVIEW.mp4`, `.srt`, `FLUO_LIVE_OVERVIEW_EVENT.pdf`, `LIVE_OVERVIEW_RECORDING.json`, `LIVE_OVERVIEW_PROVENANCE.json`, `LIVE_OVERVIEW_PLAYBACK.json`, `LIVE_OVERVIEW_SHA256SUMS.txt`. Binary files remain local under the existing ignore policy; the script, captions and proof JSON are reviewable in Git.

The old MP4 hash still matches its original provenance. Its recorder paused in Scenario Review before returning to Overview, used English captions, and produced 185.8 seconds. Original video/captions/provenance were preserved.

The new video is **144.64 seconds (2:24.64)**, 1440×980 H264/yuv420p, 25 fps, without audio. Continuous real Playwright capture plus Indonesian captions in an added bottom strip; no cuts, playback-speed edits, injected telemetry or fabricated UI animation. It is explicitly a **local** recording at `http://127.0.0.1:8000`, not a hosted capture. The recorded checkout was `a2f753f42d8fbc5ac2f9301d09681e3c2779eae4`; 76 application files match the deployed application manifest. Exact working-tree recorder SHA is retained in provenance.

Flow: Guest → Overview → Scenario Review → Return diversion → Play → Overview while PLAYING → real warning transition → Connection outage quality gate → Event Center → Event Details → operator draft/submit → reload → actual PDF download/A4 view → synthetic-data limitations.

Twenty live Overview samples all remained PLAYING, with 20 distinct timestamps, 20 steam readings, 18 return readings, 20 return-chart paths, and both false/true warning states. The offline quality gate withheld the score. Review checkbox/note persisted through reload, and the downloaded event PDF parsed with the recorded Indonesian note. These are playback/workflow assertions, not new scientific accuracy or plant-savings results.

All 3,616 MP4 frames decoded successfully with FFmpeg `-xerror`, exit 0 and no decode errors. Actual Chromium video playback reached `ended=true` at 144.64 seconds. Player QA used 8× only to save execution time; delivered MP4 timing is unchanged. Twelve representative frames were inspected as a contact sheet, with full-size inspection of live Overview and the A4 report; readable captions and no sampled clipping. This does not claim human review of every frame.

Targeted checks only: recorder assertions, clean reviewer browser/HTTP checks, full video decode/player, PDF parsing, script syntax and Ruff. One initial recorder attempt on 8001 correctly failed the existing Origin boundary; it was not presented as success. The corrected attempt used allowed 8000 without changing the app's allowlist.

## Reproduce

Start the existing app on allowed loopback 8000 with one OMP/BLAS thread and a separate local recording DB. Run `node tools/record_live_overview.mjs`, then `.venv/Scripts/python.exe tools/finish_live_overview.py`. Raw recordings and sampled frames are ignored under `.local/`. Native OS printing is not invoked: the recording downloads a real PDF and shows the real application A4 preview. Follow-up visual verification is required after re-encoding because provenance resets its visual-review field to pending.

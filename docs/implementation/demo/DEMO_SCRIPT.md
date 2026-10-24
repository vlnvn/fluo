# Recorded demonstration script

The delivered MP4 is one actual local Playwright browser recording, about3m06s, H264/1440x980/25fps, muted. The original1440x900 application is retained; an80px caption strip is added below. It does not show a hosted service.

Sequence: explicit guest entry → Overview/frozen research telemetry → opt-in sound preference → Normal operation play/pause → Return diversion warning crossing → continuous live scrub → meter-bias caveat → connection quality gate → event filter/detail → check one verification step, save draft and explicitly record review → reload persistence → real PDF download and A4 preview → notifications and Compact navigation → final synthetic/no-field-validation disclosure.

Captions and exact scene timings: FLUO_DEMO_END_TO_END.srt and RECORDING.json. The recorder reads preview data only to find a genuine quality-gated cursor; it does not inject fabricated UI/model outputs. Native OS print is suppressed only in the recorder to keep the capture in-browser. Actual browser-generated A4/print and PDF paths are covered in E2E tests. MP4 has no audio track; opt-in native chime playback is separately tested.

Reproduce after local setup/build/server:
1. Install requirements-video.txt in the existing virtualenv.
2. Run node tools/record_demo.mjs from repository root. FLUO_BASE_URL defaults to http://127.0.0.1:8000; FLUO_BROWSER_PATH can select an installed Chromium.
3. Run .venv/Scripts/python.exe tools/finish_demo.py. FFmpeg encodes the captured WebM, decodes the entire MP4 and extracts QA frames.
4. Visually review frames and the resulting video, check SHA256, then update provenance with actual findings. No re-encoding changes model or UI state.

Two earlier attempts stopped on recorder synchronization and were not delivered. The successful recorder waits for committed scenario and async checklist state. RECORDING.json discloses the app commit and recorder working-tree change. Later guest main-landmark semantics leave the visible layout unchanged. Private guest cookies/CSRF values are never added to captions.

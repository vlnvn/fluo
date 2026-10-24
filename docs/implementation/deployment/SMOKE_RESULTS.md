# Current smoke evidence — 25 October 2026

Local DEV and built single-origin application exercised with original HGB. See qa/RELEASE_EVIDENCE.json and qa/FINAL_RELEASE_AUDIT.md for final counts and scope. Guest API JUnit has26 normal passes and no expected failures. Browser tests include real reports, chime playback, continuous seek, pointer cancellation, guest isolation and all four routes Full/Compact.

A continuous local browser video and real PDF were captured; source metadata/hash and full H264 decode are in demo/VIDEO_PROVENANCE.json. This is not a public deployment recording.

Real provider HTTPS, Linux startup, direct-origin checks, disk durability across redeploy and public load are NOT EXECUTED. RELEASE_DECISION.json intentionally retains PUBLIC_DEPLOYMENT_BLOCKED. There is no actual public URL to probe. Historical pre-auth logs are retained as historical evidence, not final release results.

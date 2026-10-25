# Release status

**Engineering evidence snapshot:** 25 October 2026. This page identifies the tested cloud artifact without implying an unrestricted public release.

| Item | Recorded state |
|---|---|
| Deployment type | Protected Vercel preview |
| Provider status | `READY` |
| Hosted origin | https://fluo-o3h0wtwma-vlnvns-projects.vercel.app |
| Vercel deployment ID | `dpl_AtmJuJn8gAH4po1h1mbwiWYe7XHa` |
| Exact deployed Git SHA | `ab3ebc9650cabdc9e90f46b3e27df0959a904f50` |
| Git workflow | [Draft PR #2](https://github.com/vlnvn/fluo/pull/2) is unmerged; [draft PR #1](https://github.com/vlnvn/fluo/pull/1) remains separate |
| Backend/state | FastAPI on Vercel, restricted-role Neon PostgreSQL |
| Data/model | Synthetic telemetry, original frozen HGB; no retraining |
| Reviewer access | Vercel Authentication or explicit revocable share, then separate guest workspace |

The preview origin is not a guarantee that an arbitrary visitor can reach the app: Vercel Deployment Protection remains in force. Do not store the share URL, OIDC header, session cookies, database DSNs or a secret bypass parameter in this repository.

The reported deployment passed provider READY verification, final hosted Chromium 18/18 E2E, relevant hosted security checks, cloud inference fingerprinting, persistence across instances and isolated logical restore. The detailed results and known limitations are in [Validation](VALIDATION.md).

**Operational restrictions:** neither a production branch promotion nor a public SLA was established. Guest workspaces expire, free-tier quotas apply, reviewer shares may expire or be revoked, and long-term availability depends on platform retention. Release status must be rechecked if the deployment is superseded.

### Release evidence

- [Machine decision](https://github.com/vlnvn/fluo/blob/deploy/vercel-hobby/docs/implementation/deployment/RELEASE_DECISION.json)
- [Vercel provider proof](https://github.com/vlnvn/fluo/blob/deploy/vercel-hobby/docs/implementation/qa/vercel/DEPLOYMENT.json)
- [Cloud release summary](https://github.com/vlnvn/fluo/blob/deploy/vercel-hobby/docs/implementation/qa/vercel/CLOUD_RELEASE.json)
- [Full release audit](https://github.com/vlnvn/fluo/blob/deploy/vercel-hobby/docs/implementation/qa/FINAL_RELEASE_AUDIT.md)
- [Deployment and rollback runbook](https://github.com/vlnvn/fluo/blob/deploy/vercel-hobby/docs/implementation/deployment/VERCEL_RELEASE_RUNBOOK.md)
- [Evidence-to-proposal language](https://github.com/vlnvn/fluo/blob/deploy/vercel-hobby/docs/implementation/PROPOSAL_EVIDENCE_HANDOFF.md)

These are records from the branch's executed audit, not a new independent certification by the authors of this documentation.

# Validation and limits

Fluo has **two different kinds of evidence**: scientific evaluation using simulated data, and executed tests of the software prototype. They must not be combined into one performance claim.

## Scientific evaluation

The selected model is an original frozen `HistGradientBoostingClassifier`, using six causal features, strict score > 0.90, and 5/10-minute persistence with data/mode gates.

The recorded fresh synthetic holdout reports:

| Synthetic outcome | Recorded result |
|---|---:|
| Physical-loss episodes alerted | 69 / 71 (97.18%) |
| Return-meter-bias episodes alerted | 21 / 22 |
| Transport-delay episodes alerted | 4 / 13 |
| Clean-window warning clusters | 0 in specifically selected clean windows, ~1,353.5 simulated hours |

**Critical failure:** A negative 10% return-meter reading shift caused 66,603 unmarked warning minutes in 91,936 valid minutes in one stress evaluation. Physical condensate loss and instrument bias remain observationally ambiguous. The score cannot be read as a calibrated probability of leakage. Simulation-based generalization to a factory is not established.

Source: [research results](RESULTS.md), [model card](MODEL_CARD.md), [data lineage](DATA_SOURCES.md). These figures are not facility performance, uptime or savings claims.

## Application and hosted verification

The following figures are from the versioned engineering release audit dated **25 October 2026**, associated with source `ab3ebc9650cabdc9e90f46b3e27df0959a904f50`:

| Test scope | Reported outcome | Important boundary |
|---|---|---|
| Local API / PostgreSQL test suite | 34 passed, zero skipped/xfail | A Starlette/httpx deprecation warning was recorded |
| Restricted Neon integration tests | 6 passed | Specific authorized staging database |
| Hosted HTTPS Chromium E2E | 18 passed, zero skipped/flaky/unexpected | No Safari, Firefox or screen-reader certification |
| Hosted security API | 77 plus 15 further checks | Not a penetration-test certificate |
| Screenshot assertions | 8 | Not universal pixel identity with Figma |
| Scoped Axe accessibility scans | 11, zero findings | Not WCAG certification |
| Runtime model output | 51,840 hosted synthetic-row fingerprint agreement | Reproduction, not new accuracy evidence |
| Locked inference repeat/prefix checks | 86,400 rows | Separate local synthetic verification |
| Redeployment persistence | 7 checks across instances | Separate-domain cookies require explicit handling |
| Isolated logical backup/restore | Five exact table comparisons | Not PITR, production rollback or disaster-recovery SLA |

Primary evidence: [final release audit](https://github.com/vlnvn/fluo/blob/deploy/vercel-hobby/docs/implementation/qa/FINAL_RELEASE_AUDIT.md), [release decision](https://github.com/vlnvn/fluo/blob/deploy/vercel-hobby/docs/implementation/deployment/RELEASE_DECISION.json), [cloud release summary](https://github.com/vlnvn/fluo/blob/deploy/vercel-hobby/docs/implementation/qa/vercel/CLOUD_RELEASE.json), [evidence handoff](https://github.com/vlnvn/fluo/blob/deploy/vercel-hobby/docs/implementation/PROPOSAL_EVIDENCE_HANDOFF.md).

## Prior failures are not erased

An intermediate hosted browser run passed 15 of 18 assertions; two requests encountered the 60-new-guests/hour limit, and one auth/page-initialization path exceeded the older 10-second assertion budget. The final 18/18 pass belongs to a *separate* execution with a 30-second assertion allowance and a new quota window.

Cold-start tail latency, free-tier capacity, long-term availability, cross-browser behavior, field instrumentation and physical benefit are **not verified**. A previously exposed temporary development OIDC token in private tooling output was documented; containment and expiry were reported, revocation was not established. Do not publish private credentials or the reviewer bypass capability.

The hosted preview is access-controlled; it is not a branch-`main` production promotion. See [release status](RELEASE_STATUS.md).

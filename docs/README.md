# Fluo documentation

This directory is the entry point for the **research repository** on `main`. The reviewed full-stack prototype lives on the [application branch](https://github.com/vlnvn/fluo/tree/deploy/vercel-hobby). These are different source states.

## Find the right document

| Need | Start with | Source |
|---|---|---|
| Understand Fluo in five minutes | [Project overview](../README.md) | Curated |
| Open the preview or reproduce locally | [Getting started](GETTING_STARTED.md) | How-to |
| Follow data, inference, session and reporting flow | [Architecture](ARCHITECTURE.md) | Explanation |
| Evaluate scientific and software claims | [Validation and limitations](VALIDATION.md) | Evidence |
| Identify the deployed source and access restrictions | [Release status](RELEASE_STATUS.md) | Release reference |
| Understand research sources and assumptions | [Data sources](DATA_SOURCES.md) | Research reference |
| Inspect model comparison and synthetic tests | [Results](RESULTS.md) | Research reference |
| Review model caveats | [Model card](MODEL_CARD.md) | Research reference |
| Examine historical experiments | [Historical v2 report](HISTORICAL_V2_REPORT.md) | Archived research |

## Engineering references

The following are maintained alongside the application on `deploy/vercel-hobby`; the links do not refer to files on `main`:

- [Architecture decision: local application](https://github.com/vlnvn/fluo/blob/deploy/vercel-hobby/docs/implementation/ADR-001.md)
- [Architecture decision: serverless PostgreSQL](https://github.com/vlnvn/fluo/blob/deploy/vercel-hobby/docs/implementation/ADR-002-VERCEL-POSTGRES.md)
- [API contract](https://github.com/vlnvn/fluo/blob/deploy/vercel-hobby/docs/implementation/API_CONTRACT.md)
- [Threat model](https://github.com/vlnvn/fluo/blob/deploy/vercel-hobby/docs/implementation/deployment/THREAT_MODEL.md)
- [Vercel release runbook](https://github.com/vlnvn/fluo/blob/deploy/vercel-hobby/docs/implementation/deployment/VERCEL_RELEASE_RUNBOOK.md)
- [Final audited release](https://github.com/vlnvn/fluo/blob/deploy/vercel-hobby/docs/implementation/qa/FINAL_RELEASE_AUDIT.md)
- [Figma traceability](https://github.com/vlnvn/fluo/blob/deploy/vercel-hobby/docs/implementation/FIGMA_TRACEABILITY.md)

## Reading rules

- A **synthetic experiment** is not a field trial.
- A **browser/API test** is not evidence of industrial performance.
- A **protected preview** is not a promoted production release.
- A **model score** is not a calibrated physical-leak probability.
- Event-review completion never authorizes condensate recovery or equipment actuation.

For proposed changes to claims or datasets, see [Contributing](../CONTRIBUTING.md).

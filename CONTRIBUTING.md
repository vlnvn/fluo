# Contributing to Fluo

Thanks for taking the time to review the project. Fluo is currently an **educational research prototype**, not an open-source library or production service.

## Before contributing

The repository is publicly readable, but **no open-source license has been granted**. Do not assume permission to reuse, redistribute or incorporate code elsewhere. Until the maintainers resolve licensing and third-party asset rights, code contributions should come only from authorized project collaborators. Documentation corrections and factual issue reports are welcome for review.

Open an issue for a proposed change before undertaking work that would affect the model, research data, event semantics, privacy boundary or release configuration. The two existing release PRs are draft and unmerged; don't merge them as part of a documentation cleanup.

## Make a focused change

1. Identify the correct source branch. `main` contains research lineage; `deploy/vercel-hobby` contains the hosted full-stack prototype.
2. Branch from the branch you intend to target. Keep feature, security and documentation changes separate.
3. State **what changed and why**. Include actual reproduced evidence, not success statements inferred from code inspection.
4. Test the paths you touched and record the commands and outcomes. For code changes, see the [app test commands](https://github.com/vlnvn/fluo/blob/deploy/vercel-hobby/README.md#verification).
5. Open a PR using the template. Preserve failure logs and limitations rather than overwriting the audit history.

## Research integrity

- Original archived telemetry and event labels are **synthetic**; never describe them as measured at a plant.
- Preserve the audited model checksum and frozen inference rules unless a separately reviewed research change explicitly authorizes replacing them.
- Do not tune parameters on the locked fresh holdout or use simulator truth columns as inference features.
- Keep human inspection and recovery authorization separate from an ML signature score.
- Include a scientific validity statement when changing an experiment, metric, threshold, or claim.

## Security and privacy

Never commit private runtime packets, source ZIPs, database URLs, OIDC tokens, guest cookies, reviewer share links, telemetry from a real facility, licensed font files, raw private logs or temporary downloaded PDFs. Redact traces before attaching them to a PR or issue.

For vulnerabilities use [SECURITY.md](SECURITY.md), not a public bug report.

## Documentation style

Write for a reader who doesn't know the project. State prerequisites and branch context. Use relative links for files on the same branch, exact source SHAs for release-specific claims, and consistent terms: **Return meter bias**, **Scenario Review**, **Event Center**, **deficit signature**, **synthetic**. Avoid promotional adjectives and undocumented claims.

Documentation changes do not require retraining, UI redesign, cloud provisioning or alterations to guest ownership.

Maintainer review is required before merge. A PR or its successful CI does not by itself authorize a production promotion.

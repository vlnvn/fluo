# Security policy

Fluo is an educational prototype with a **protected preview**. There is no production security-support SLA or independently certified penetration test.

## Reporting a vulnerability

**Do not open a public issue, pull request or discussion containing exploit steps, a usable share capability, credentials or personal data.**

Use GitHub's **private vulnerability reporting** feature on this repository if it is enabled. If GitHub does not offer that option, contact the repository owner via a private channel already established with the project team and request a secure reporting method **without sending exploit details publicly**. The maintainers have not advertised a public security mailbox; do not guess one.

A useful private report contains the affected commit, minimal reproduction, expected/observed impact, and whether any credentials or guest data were accessed. Remove secrets from logs and screenshots.

## Supported scope

The code is under active research review. The tested preview is tied to commit `ab3ebc9650cabdc9e90f46b3e27df0959a904f50`; the default `main` branch is research-only. Neither branch carries a guarantee of ongoing security support. Review the [release record](docs/RELEASE_STATUS.md) for the tested scope and remaining limits.

## Security boundaries

- Vercel provider access control and app-level guest isolation are separate checks.
- Guest authorization establishes a temporary capability, **not a verified human identity**.
- Reviews, preferences, reports and events must remain subject to server-side ownership.
- Offline model and dataset artifacts are checksum-verified before being loaded.
- No online SQLite fallback is supported in Vercel serverless functions.
- Fluo must not issue equipment-control or condensate-recovery authorization.

No security scan proves an absence of vulnerabilities. Provider sharing links can be revoked; report suspected credential exposure promptly. Do not post reviewer or developer bypass tokens in any public tracker.

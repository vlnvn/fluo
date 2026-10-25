# Reviewer access during judging — 25 October 2026

P0 COMPLETE. The protected immutable preview remains `https://fluo-o3h0wtwma-vlnvns-projects.vercel.app/`, deployed SHA `ab3ebc9650cabdc9e90f46b3e27df0959a904f50`. No production deployment, database, guest isolation, rate limit, paid plan or global protection setting was changed.

The previous 23-hour capability was revoked and regenerated through the authenticated Vercel `PATCH /aliases/{id}/protection-bypass` endpoint on deployment `dpl_AtmJuJn8gAH4po1h1mbwiWYe7XHa`, team `team_zwZnclCELlEBLoZg5s1LX6HA`. Request: `revoke.regenerate=true`, **ttl omitted**. The official API defines omitted TTL as no expiry. Returned scope: `shareable-link`, createdAt 1792902407353. This removes the26 October automatic expiration; it does not guarantee provider uptime or that nobody will manually revoke/delete the deployment.

Capability and provider response are stored only in ignored `.local/reviewer-link.json` and `.local/reviewer-access-provider.json`. Do not commit these, paste them into the proposal, or use the convenience get-access tool to generate a replacement 23-hour link. Anyone holding the capability can enter the provider gate, but Fluo still requires a separate guest sandbox; guest TTL remains two hours.

`qa/vercel/reviewer-access-judging.json` records six successful fresh Chromium steps without OIDC: entry gate, guest entry, Overview, Scenario Review/Overview navigation, reload and logout. This is a targeted access regression, not a repeat of the earlier full audit.

After judging, the owner can revoke the link from the deployment's Share dialog. Equivalent authenticated API operation: same team/deployment, `revoke.secret` read from the private capability's `_vercel_share` query parameter, `regenerate=false`, no override or project-wide automation bypass. Never place the literal secret in shell history or Git. Revocation stops future link use; do not assume it immediately removes every already-issued provider cookie. Fluo guest expiry/logout remain independent controls. No automatic revocation is scheduled because the judging end date was not provided.

Official references: [sharing deployments](https://vercel.com/docs/deployments/sharing-deployments), [shareable links and revocation](https://vercel.com/docs/deployment-protection/methods-to-bypass-deployment-protection/sharable-links), [official SDK alias operations](https://github.com/vercel/sdk/blob/main/docs/sdks/aliases/README.md). The authenticated API tool's contract explicitly states that shareable links never expire unless TTL is supplied.

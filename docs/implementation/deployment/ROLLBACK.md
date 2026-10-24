# Rollback and incident notes

No external deployment exists to roll back. Inspect git status first; do not reset/discard working changes, delete state/volumes or overwrite audited research.

1. Stop the owned launcher with Ctrl+C. Preserve code revision and local logs without exporting sensitive notes/secrets.
2. Back up SQLite using its backup API, not a live copy of only the main WAL file. Store.backup/reopen/integrity are tested. Keep backups private.
3. Investigate an older commit in a separate checkout/worktree after protecting changes; reinstall its lockfile/build there. Never retrain to repair UI or replace the ZIP/model/source datasets.
4. Inspect user_version and integrity_check on an offline copy. Current Store accepts0/1 and refuses newer versions. Verify notes/revisions before an explicit state-restoration procedure.
5. Restart loopback and rerun readiness/API/report/replay/browser checks. Retain failed state for diagnosis instead of deleting it.

Future staging requires immutable image/commit digests, compatible private backup, migration plan and rollback owner before deployment. On auth/ownership incident, restrict ingress, invalidate actual identity sessions/credentials, then examine safe logs. Negative auth/persistence tests must pass before restoring traffic. DNS/proxy changes must not expose the origin.

Provider restore commands, backup encryption/location/retention, RPO/RTO and cloud rollback test are UNCONFIGURED until a real host/account/operator is supplied. No successful disaster recovery is claimed.

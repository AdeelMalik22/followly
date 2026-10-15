# Staging and production release runbook

## Before release

1. Take a PostgreSQL custom-format backup and record its SHA-256 checksum.
2. Validate the backup by restoring it into an isolated PostgreSQL database.
3. Record the current migration revision, tenant count, and row counts from
   `scripts/verify_tenant_migration.py`.
4. Run `scripts/staging_tenant_smoke_test.sh` for every enabled tenant.
5. Keep the previous application image and the previous migration revision
   available for rollback.

The existing backup validation command performs steps 1 and 2:

```bash
BACKUP_SOURCE_DATABASE_URL='postgresql://...' \
BACKUP_RESTORE_DATABASE_URL='postgresql://...' \
BACKUP_FILE=/secure/backups/followly-$(date +%Y%m%d-%H%M%S).dump \
./scripts/backup_restore_check.sh
sha256sum /secure/backups/followly-*.dump
```

Backups must be encrypted at rest, access controlled, and retained according
to the deployment retention policy. Never put a database URL or backup file in
the repository.

## Rollback triggers

Start rollback when any of these conditions persists for five minutes or
affects a critical tenant:

- `/health/ready` is degraded or database/Redis readiness fails.
- HTTP 5xx exceeds 2% of requests or any critical route returns repeated 5xx.
- p95 latency exceeds 2 seconds for five minutes, or p99 exceeds 5 seconds.
- Webhook failures exceed 5% or event processing remains stale beyond the
  configured retry window.
- Tenant smoke tests report cross-tenant data, authorization, or integration
  failures.
- Usage records, billing state, or webhook delivery counts diverge from the
  release baseline.

## Rollback procedure

1. Stop new rollout traffic and record the correlation IDs and release image.
2. Roll the API image back to the last known good image.
3. Do not automatically downgrade database migrations. Restore the database
   only when data corruption or an incompatible schema change is confirmed,
   using the validated backup and a maintenance window.
4. Re-run readiness and every tenant smoke test.
5. Compare tenant row counts and ownership with the pre-release report.
6. Preserve logs, webhook events, metrics, and the backup checksum for review.

Rollback completion requires healthy readiness, passing tenant smoke tests, and
matching tenant ownership counts. Any irreversible data repair needs a separate
review before execution.

# PostgreSQL backup and restore

Create encrypted, compressed PostgreSQL backups with `pg_dump` and validate restores against a separate empty database before release or migration.

```bash
BACKUP_SOURCE_DATABASE_URL="$DATABASE_URL" \
BACKUP_RESTORE_DATABASE_URL="postgresql://user:password@restore-host:5432/followly_restore" \
./scripts/backup_restore_check.sh
```

The restore target must be disposable or dedicated to validation. The script uses `--clean --if-exists` on that target and never writes to the source database. Store the resulting dump in encrypted backup storage with restricted access and retain enough generations to cover the recovery policy.

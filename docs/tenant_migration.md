# Tenant migration verification

Create the target PostgreSQL database with the staging compose stack, apply its
Alembic migrations, and restore a trusted source dump into it. Then compare
source and target totals and per-business counts:

```bash
./scripts/verify_tenant_migration.py \
  --source-url 'postgresql://source-user:source-password@source-host/followly' \
  --target-url 'postgresql://followly:staging-password@target-host/followly' \
  --business-id 123
```

The verifier checks every table for equal row totals, compares rows grouped by
`business_id`, detects business foreign-key orphans, and checks message and tool
audit conversation ownership. A nonzero exit status means the migration must be
reviewed before staging is used.

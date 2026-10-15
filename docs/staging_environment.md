# Staging environment

The staging stack runs the API against PostgreSQL 16 and Redis 7 with persistent
volumes. It uses the same Alembic migrations and application image as a
production deployment. Integration credentials remain outside the repository.

```bash
cp .env.staging.example .env.staging
# Replace staging secrets and add the provider credentials you want to test.
docker compose --env-file .env.staging -f docker-compose.staging.yml up --build -d
docker compose --env-file .env.staging -f docker-compose.staging.yml ps
```

The API entrypoint applies migrations before starting Uvicorn. PostgreSQL and
Redis must pass their health checks before the API container starts.

```bash
docker compose --env-file .env.staging -f docker-compose.staging.yml down
docker compose --env-file .env.staging -f docker-compose.staging.yml down -v
```

The second command removes staging data volumes. Provider checks are run by
`scripts/staging_smoke_test.sh` after a business and test credentials exist.
Use test Stripe keys and test provider accounts; the smoke test does not create
a charge.

```bash
export STAGING_API_URL=http://localhost:8000
export STAGING_AUTH_TOKEN='business-user-access-token'
./scripts/staging_smoke_test.sh
```

The smoke test covers application readiness (PostgreSQL, Redis, queue, and LLM
configuration), billing status, WhatsApp and Google Calendar health, and an
optional real LLM request. Set `STAGING_RUN_LLM=1` only when the configured
provider should be called.

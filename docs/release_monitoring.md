# Post-release monitoring

Run the monitor with the same local tenant token file used for smoke tests:

```bash
export STAGING_API_URL=http://localhost:8000
export STAGING_TENANTS_FILE=/secure/path/staging-tenants.txt
STAGING_MONITOR_ITERATIONS=30 \
STAGING_MONITOR_INTERVAL_SECONDS=60 \
STAGING_MONITOR_OUTPUT=/secure/path/followly-release.tsv \
./scripts/staging_release_monitor.sh
```

Each sample records UTC time, tenant, endpoint, HTTP status, request latency,
usage report, and webhook delivery metrics. Review the file every five minutes
for 5xx responses, readiness degradation, rising latency, usage-limit changes,
webhook failure/retry growth, and stale processing. Correlate incidents with
the `X-Correlation-ID` returned by a focused request and preserve the sample
file with the release record.

The monitor reads existing reporting endpoints and does not create messages,
appointments, charges, or provider events.

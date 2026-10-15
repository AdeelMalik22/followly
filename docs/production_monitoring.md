# Production monitoring and alerting

The API exposes `/health/ready` for dependency readiness and
`/health/metrics` for process-level request metrics. Protect the metrics route
at the network or gateway layer and provide a monitoring bearer token through
the deployment secret store.

Metrics include request volume, 5xx error rate, status counts, p50/p95/p99
latency, and the most frequently used routes. The sample is bounded in memory;
export it to an external monitoring system for durable history and alerting.

Run the alert check from cron, a systemd timer, or the release monitor host:

```bash
export PRODUCTION_API_URL=https://api.example.com
export PRODUCTION_METRICS_TOKEN='monitoring-token'
./scripts/check_production_alerts.sh
```

Defaults alert at 2% 5xx errors, 2 seconds p95 latency, or 5 seconds p99
latency. Override `ALERT_ERROR_RATE`, `ALERT_P95_MS`, and `ALERT_P99_MS` for
the deployment. Combine this check with `/health/ready`, billing usage reports,
and per-tenant webhook metrics so dependency failures and delivery failures are
visible alongside request health.

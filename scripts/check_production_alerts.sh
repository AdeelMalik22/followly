#!/usr/bin/env bash
set -euo pipefail

: "${PRODUCTION_API_URL:?PRODUCTION_API_URL must be set}"
: "${PRODUCTION_METRICS_TOKEN:?PRODUCTION_METRICS_TOKEN must be set}"

payload=$(curl --fail --silent --show-error \
  -H "Authorization: Bearer ${PRODUCTION_METRICS_TOKEN}" \
  "${PRODUCTION_API_URL%/}/health/metrics")

PAYLOAD="$payload" python - <<'PY'
import json
import os
import sys

data = json.loads(os.environ["PAYLOAD"])
error_rate = data.get("error_rate", 0)
p95 = data.get("latency_ms", {}).get("p95", 0)
p99 = data.get("latency_ms", {}).get("p99", 0)
error_limit = float(os.environ.get("ALERT_ERROR_RATE", "0.02"))
p95_limit = float(os.environ.get("ALERT_P95_MS", "2000"))
p99_limit = float(os.environ.get("ALERT_P99_MS", "5000"))
alerts = []
if error_rate > error_limit:
    alerts.append(f"5xx error rate {error_rate:.2%} exceeds {error_limit:.2%}")
if p95 > p95_limit:
    alerts.append(f"p95 latency {p95:.0f}ms exceeds {p95_limit:.0f}ms")
if p99 > p99_limit:
    alerts.append(f"p99 latency {p99:.0f}ms exceeds {p99_limit:.0f}ms")
if alerts:
    for alert in alerts:
        print(f"ALERT {alert}", file=sys.stderr)
    raise SystemExit(1)
print(f"OK requests={data.get('requests', 0)} error_rate={error_rate:.2%} p95_ms={p95:.0f} p99_ms={p99:.0f}")
PY

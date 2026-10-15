#!/usr/bin/env bash
set -euo pipefail

: "${STAGING_API_URL:?STAGING_API_URL must be set}"
: "${STAGING_TENANTS_FILE:?STAGING_TENANTS_FILE must contain tenant_id|bearer_token rows}"
interval="${STAGING_MONITOR_INTERVAL_SECONDS:-60}"
iterations="${STAGING_MONITOR_ITERATIONS:-1}"
output="${STAGING_MONITOR_OUTPUT:-staging-monitor.tsv}"

printf 'timestamp\ttenant_id\tendpoint\thttp_status\tlatency_seconds\tpayload\n' > "$output"

sample() {
  local tenant_id="$1" token="$2" path="$3" timestamp status timing body
  timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  body=$(mktemp)
  timing=$(curl --silent --show-error --output "$body" --write-out '%{http_code}\t%{time_total}' \
    -H "Authorization: Bearer ${token}" -H 'Accept: application/json' \
    "${STAGING_API_URL%/}${path}" || printf '000\t-1')
  status=${timing%%$'\t'*}
  timing=${timing#*$'\t'}
  payload=$(tr '\n\t' '  ' < "$body" | cut -c1-500)
  rm -f "$body"
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$timestamp" "$tenant_id" "$path" "$status" "$timing" "$payload" | tee -a "$output"
}

for ((iteration = 1; iteration <= iterations; iteration++)); do
  while IFS='|' read -r tenant_id token; do
    [[ -z "${tenant_id}" || "${tenant_id}" == \#* ]] && continue
    sample "$tenant_id" "$token" /health/ready
    sample "$tenant_id" "$token" /api/v1/billing/usage-report
    sample "$tenant_id" "$token" /api/v1/business/webhook-metrics
  done < "$STAGING_TENANTS_FILE"
  (( iteration < iterations )) && sleep "$interval"
done

printf 'Monitoring samples written to %s\n' "$output"

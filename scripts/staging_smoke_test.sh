#!/usr/bin/env bash
set -euo pipefail

base_url="${STAGING_API_URL:-http://localhost:8000}"
auth_token="${STAGING_AUTH_TOKEN:?STAGING_AUTH_TOKEN must contain a business-user bearer token}"

check() {
  local path="$1"
  local response
  response=$(curl --fail --silent --show-error -H "Authorization: Bearer ${auth_token}" -H 'Accept: application/json' "${base_url}${path}")
  printf 'PASS %s %s\n' "$path" "$(printf '%s' "$response" | tr '\n' ' ' | cut -c1-240)"
}

check_public() {
  local path="$1"
  curl --fail --silent --show-error -H 'Accept: application/json' "${base_url}${path}" >/dev/null
  printf 'PASS %s\n' "$path"
}

check_public /health
check_public /health/ready
check /api/v1/billing/status
check /api/v1/business/integration-status
check /api/v1/business/integration-health

if [[ "${STAGING_RUN_LLM:-0}" == "1" ]]; then
  message="${STAGING_LLM_MESSAGE:-Staging integration smoke test. Reply with one short sentence.}"
  payload=$(printf '%s' "$message" | python -c 'import json,sys; print(json.dumps({"message": sys.stdin.read()}))')
  curl --fail --silent --show-error -H "Authorization: Bearer ${auth_token}" -H 'Content-Type: application/json' -d "$payload" "${base_url}/api/v1/business/test-chat" >/dev/null
  printf 'PASS /api/v1/business/test-chat (LLM call)\n'
else
  printf 'SKIP /api/v1/business/test-chat (set STAGING_RUN_LLM=1 to make a real LLM request)\n'
fi

printf 'Staging smoke test completed.\n'

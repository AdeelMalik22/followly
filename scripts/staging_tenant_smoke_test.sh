#!/usr/bin/env bash
set -euo pipefail

: "${STAGING_API_URL:?STAGING_API_URL must be set}"
: "${STAGING_TENANTS_FILE:?STAGING_TENANTS_FILE must contain tenant_id|bearer_token rows}"

failed=0
while IFS='|' read -r tenant_id token; do
  [[ -z "${tenant_id}" || "${tenant_id}" == \#* ]] && continue
  if [[ -z "${token}" ]]; then
    printf 'FAIL tenant=%s missing bearer token\n' "$tenant_id" >&2
    failed=1
    continue
  fi
  printf 'Tenant %s\n' "$tenant_id"
  for path in /health/ready /api/v1/billing/status /api/v1/business/integration-status /api/v1/business/integration-health; do
    if curl --fail --silent --show-error \
      -H "Authorization: Bearer ${token}" \
      -H 'Accept: application/json' \
      "${STAGING_API_URL%/}${path}" >/dev/null; then
      printf '  PASS %s\n' "$path"
    else
      printf '  FAIL %s\n' "$path" >&2
      failed=1
    fi
  done
done < "$STAGING_TENANTS_FILE"

if (( failed )); then
  printf 'Tenant smoke tests failed.\n' >&2
  exit 1
fi
printf 'All tenant smoke tests passed.\n'

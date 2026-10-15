#!/usr/bin/env bash
set -euo pipefail

: "${BACKUP_SOURCE_DATABASE_URL:?Set BACKUP_SOURCE_DATABASE_URL}"
: "${BACKUP_RESTORE_DATABASE_URL:?Set BACKUP_RESTORE_DATABASE_URL}"

backup_file="${BACKUP_FILE:-$(mktemp --suffix=.dump)}"
cleanup() {
  if [[ -z "${BACKUP_FILE:-}" || "${BACKUP_FILE}" == /tmp/* ]]; then
    rm -f "$backup_file"
  fi
}
trap cleanup EXIT

pg_dump --format=custom --no-owner --file="$backup_file" "$BACKUP_SOURCE_DATABASE_URL"
pg_restore --exit-on-error --no-owner --clean --if-exists --dbname="$BACKUP_RESTORE_DATABASE_URL" "$backup_file"
echo "Backup and restore validation completed: $backup_file"

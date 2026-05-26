#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "Missing DATABASE_URL."
  echo "Example:"
  echo '  DATABASE_URL="postgresql://USER:PASSWORD@HOST:PORT/DB_NAME" scripts/import_to_postgres.sh'
  exit 1
fi

psql "$DATABASE_URL" -f db/import_all.sql

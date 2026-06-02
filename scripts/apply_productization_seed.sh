#!/usr/bin/env bash
set -euo pipefail

DB_NAME="${DB_NAME:-robo_reception}"
DB_USER="${DB_USER:-minhmh}"
DB_HOST="${DB_HOST:-}"

PSQL_ARGS=(-v ON_ERROR_STOP=1 -U "${DB_USER}" -d "${DB_NAME}")
if [[ -n "${DB_HOST}" ]]; then
  PSQL_ARGS+=(-h "${DB_HOST}")
fi

psql "${PSQL_ARGS[@]}" -f db/app/seed_productization_demo.sql

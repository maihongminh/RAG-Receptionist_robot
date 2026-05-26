#!/usr/bin/env bash
set -euo pipefail

DB_NAME="${DB_NAME:-robo_reception}"
DB_USER="${DB_USER:-minhmh}"
DB_HOST="${DB_HOST:-localhost}"

psql -v ON_ERROR_STOP=1 -U "${DB_USER}" -d "${DB_NAME}" -h "${DB_HOST}" -f db/app_views.sql

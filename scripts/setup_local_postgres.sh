#!/usr/bin/env bash
set -euo pipefail

DB_USER="${DB_USER:-minhmh}"
DB_NAME="${DB_NAME:-robo_reception}"

echo "Setting up local Postgres database:"
echo "  user:     ${DB_USER}"
echo "  database: ${DB_NAME}"
echo

if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}'" | grep -q 1; then
  sudo -u postgres createuser -P "${DB_USER}"
else
  echo "Role ${DB_USER} already exists."
fi

if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1; then
  sudo -u postgres createdb -O "${DB_USER}" "${DB_NAME}"
else
  echo "Database ${DB_NAME} already exists."
  sudo -u postgres psql -c "ALTER DATABASE \"${DB_NAME}\" OWNER TO \"${DB_USER}\";"
fi

echo
echo "Done. You can import with:"
echo "  psql ${DB_NAME} -f db/import_all.sql"

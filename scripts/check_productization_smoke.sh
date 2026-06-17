#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-backend/.venv/bin/python}"

echo "[1/6] Checking app contract"
"${PYTHON_BIN}" scripts/check_app_contract.py

echo "[2/6] Checking tool map"
"${PYTHON_BIN}" scripts/check_tool_map.py

echo "[3/6] Checking raw table inventory"
"${PYTHON_BIN}" scripts/check_raw_table_inventory.py

echo "[4/6] Checking RAG registry"
"${PYTHON_BIN}" scripts/check_rag_registry.py

echo "[5/6] Running MVP chatbot scenario"
"${PYTHON_BIN}" scripts/test_mvp_chatbot.py --llm-provider none

if [[ "${SKIP_PYTEST:-0}" == "1" ]]; then
  echo "[6/6] Skipping pytest because SKIP_PYTEST=1"
else
  echo "[6/6] Running backend test suite"
  (cd backend && ./.venv/bin/pytest)
fi

echo "Productization smoke check passed."

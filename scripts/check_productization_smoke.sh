#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-backend/.venv/bin/python}"

echo "[1/5] Checking app contract"
"${PYTHON_BIN}" scripts/check_app_contract.py

echo "[2/5] Checking tool map"
"${PYTHON_BIN}" scripts/check_tool_map.py

echo "[3/5] Checking RAG registry"
"${PYTHON_BIN}" scripts/check_rag_registry.py

echo "[4/5] Running MVP chatbot scenario"
"${PYTHON_BIN}" scripts/test_mvp_chatbot.py --llm-provider none

if [[ "${SKIP_PYTEST:-0}" == "1" ]]; then
  echo "[5/5] Skipping pytest because SKIP_PYTEST=1"
else
  echo "[5/5] Running backend test suite"
  (cd backend && ./.venv/bin/pytest)
fi

echo "Productization smoke check passed."

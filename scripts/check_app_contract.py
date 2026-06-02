#!/usr/bin/env python3
"""Validate that the live robo_app schema matches db/app/contract.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.db import fetch_all  # noqa: E402


def load_contract(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def fetch_schema_columns(schema: str) -> dict[str, dict[str, str]]:
    rows = fetch_all(
        """
        SELECT
          table_name,
          column_name,
          data_type
        FROM information_schema.columns
        WHERE table_schema = %(schema)s
        ORDER BY table_name, ordinal_position
        """,
        {"schema": schema},
    )
    columns: dict[str, dict[str, str]] = {}
    for row in rows:
        table_name = row["table_name"]
        columns.setdefault(table_name, {})[row["column_name"]] = row["data_type"]
    return columns


def validate_contract(contract: dict[str, Any], live_columns: dict[str, dict[str, str]]) -> list[str]:
    errors: list[str] = []
    for view in contract.get("views", []):
        view_name = view["name"]
        if view_name not in live_columns:
            errors.append(f"Missing view/table: {contract['schema']}.{view_name}")
            continue

        actual_columns = live_columns[view_name]
        for column in view.get("columns", []):
            column_name = column["name"]
            if column_name not in actual_columns:
                errors.append(f"Missing column: {contract['schema']}.{view_name}.{column_name}")
                continue
            expected_type = column.get("data_type")
            actual_type = actual_columns[column_name]
            if expected_type and actual_type != expected_type:
                errors.append(
                    f"Type mismatch: {contract['schema']}.{view_name}.{column_name} "
                    f"expected {expected_type}, got {actual_type}"
                )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--contract",
        type=Path,
        default=PROJECT_ROOT / "db" / "app" / "contract.json",
        help="Path to app contract JSON.",
    )
    args = parser.parse_args()

    contract = load_contract(args.contract)
    errors = validate_contract(contract, fetch_schema_columns(contract["schema"]))
    if errors:
        print("App contract check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    view_count = len(contract.get("views", []))
    print(f"App contract check passed: {contract['schema']} has {view_count} contracted views.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

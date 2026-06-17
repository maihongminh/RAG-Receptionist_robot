#!/usr/bin/env python3
"""Validate db/app/raw_table_inventory.json against db/raw/schema.sql."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_TABLE_PATTERN = re.compile(r'CREATE TABLE "robo_raw"\."([^"]+)"')
VALID_STATUSES = {"current", "planned", "later", "hold"}
VALID_ACCESS_LEVELS = {"public", "operational", "private", "sensitive", "platform"}


def load_raw_table_names(raw_schema_path: Path) -> list[str]:
    return RAW_TABLE_PATTERN.findall(raw_schema_path.read_text(encoding="utf-8"))


def load_inventory(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_inventory(raw_tables: list[str], inventory: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    raw_table_set = set(raw_tables)
    entries = inventory.get("tables", [])
    inventory_tables = [entry.get("raw_table") for entry in entries]
    inventory_table_set = set(inventory_tables)

    if inventory.get("source_schema") != "robo_raw":
        errors.append("source_schema must be robo_raw.")

    if inventory.get("raw_table_count") != len(raw_tables):
        errors.append(
            f"raw_table_count expected {len(raw_tables)}, got {inventory.get('raw_table_count')}"
        )

    if len(inventory_tables) != len(inventory_table_set):
        errors.append("raw_table_inventory contains duplicate raw_table entries.")

    missing = sorted(raw_table_set - inventory_table_set)
    extra = sorted(inventory_table_set - raw_table_set)
    if missing:
        errors.append(f"Missing raw tables in inventory: {', '.join(missing)}")
    if extra:
        errors.append(f"Inventory contains unknown raw tables: {', '.join(extra)}")

    for entry in entries:
        raw_table = entry.get("raw_table", "<missing>")
        for key in ["group", "access_level", "status", "batch", "app_views", "tools", "notes"]:
            if key not in entry:
                errors.append(f"{raw_table}: missing key {key}")

        if entry.get("status") not in VALID_STATUSES:
            errors.append(f"{raw_table}: invalid status {entry.get('status')}")
        if entry.get("access_level") not in VALID_ACCESS_LEVELS:
            errors.append(f"{raw_table}: invalid access_level {entry.get('access_level')}")
        if not isinstance(entry.get("app_views"), list):
            errors.append(f"{raw_table}: app_views must be a list")
        if not isinstance(entry.get("tools"), list):
            errors.append(f"{raw_table}: tools must be a list")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--raw-schema",
        type=Path,
        default=PROJECT_ROOT / "db" / "raw" / "schema.sql",
    )
    parser.add_argument(
        "--inventory",
        type=Path,
        default=PROJECT_ROOT / "db" / "app" / "raw_table_inventory.json",
    )
    args = parser.parse_args()

    raw_tables = load_raw_table_names(args.raw_schema)
    inventory = load_inventory(args.inventory)
    errors = validate_inventory(raw_tables, inventory)
    if errors:
        print("Raw table inventory check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Raw table inventory check passed: {len(raw_tables)} raw tables covered.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

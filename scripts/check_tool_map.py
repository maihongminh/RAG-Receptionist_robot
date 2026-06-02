#!/usr/bin/env python3
"""Validate db/app/tool_map.json against the app contract and policy map."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.auth.policy_guard import INTENT_TOOL_MAP  # noqa: E402


IGNORED_CONTRACT_TOOL_PREFIXES = ("auth.", "future.", "scripts.")


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def validate_tool_map(contract: dict[str, Any], tool_map: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    contract_views = {view["name"]: view for view in contract.get("views", [])}
    tools = tool_map.get("tools", [])
    tool_names = [tool["tool_name"] for tool in tools]
    tool_by_name = {tool["tool_name"]: tool for tool in tools}

    if len(tool_names) != len(set(tool_names)):
        errors.append("Duplicate tool_name in tool_map.json")

    for tool in tools:
        tool_name = tool["tool_name"]
        for required_key in [
            "status",
            "intents",
            "data_source",
            "access_level",
            "contract_views",
            "source_tables",
            "allowed_roles",
            "scope_rule",
            "tests",
        ]:
            if required_key not in tool:
                errors.append(f"{tool_name}: missing key {required_key}")

        for view_name in tool.get("contract_views", []):
            if view_name not in contract_views:
                errors.append(f"{tool_name}: unknown contract view {view_name}")
                continue
            contract_tools = contract_views[view_name].get("tools", [])
            if tool_name not in contract_tools:
                errors.append(f"{tool_name}: not listed in contract view {view_name}.tools")

        for intent in tool.get("intents", []):
            expected_tool = INTENT_TOOL_MAP.get(intent)
            if expected_tool and expected_tool != tool_name:
                errors.append(
                    f"{tool_name}: intent {intent} maps to {expected_tool} in PolicyGuard"
                )

    for intent, tool_name in INTENT_TOOL_MAP.items():
        if tool_name == "none":
            continue
        if tool_name not in tool_by_name:
            errors.append(f"PolicyGuard intent {intent} maps to unmapped tool {tool_name}")

    for view in contract.get("views", []):
        for tool_name in view.get("tools", []):
            if tool_name.startswith(IGNORED_CONTRACT_TOOL_PREFIXES):
                continue
            if tool_name not in tool_by_name:
                errors.append(f"Contract view {view['name']} lists unmapped tool {tool_name}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--contract",
        type=Path,
        default=PROJECT_ROOT / "db" / "app" / "contract.json",
        help="Path to app contract JSON.",
    )
    parser.add_argument(
        "--tool-map",
        type=Path,
        default=PROJECT_ROOT / "db" / "app" / "tool_map.json",
        help="Path to tool map JSON.",
    )
    args = parser.parse_args()

    contract = load_json(args.contract)
    tool_map = load_json(args.tool_map)
    errors = validate_tool_map(contract, tool_map)
    if errors:
        print("Tool map check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Tool map check passed: {len(tool_map.get('tools', []))} mapped tools.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

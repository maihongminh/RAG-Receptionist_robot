#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from rag_documents import RAG_DOCUMENT_SOURCES


VALID_ACCESS_LEVELS = {"public", "private", "operational"}
VALID_LANGUAGES = {"vi", "en", "km"}


def validate_rag_registry() -> list[str]:
    errors: list[str] = []
    seen_source_names: set[str] = set()

    for source in RAG_DOCUMENT_SOURCES:
        if not source.source_name:
            errors.append("RAG source has empty source_name.")
            continue

        if source.source_name in seen_source_names:
            errors.append(f"Duplicate RAG source_name: {source.source_name}")
        seen_source_names.add(source.source_name)

        if not source.source_view.startswith("robo_app."):
            errors.append(
                f"{source.source_name}: source_view must point to robo_app.*, got {source.source_view}"
            )

        if not source.source_tables:
            errors.append(f"{source.source_name}: source_tables must not be empty.")

        for table in source.source_tables:
            if not table.startswith(("robo_raw.", "robo_app.")):
                errors.append(
                    f"{source.source_name}: source_table must point to robo_raw.* or robo_app.*, got {table}"
                )

        normalized_query = " ".join(source.query.lower().split())
        if "from robo_app." not in normalized_query:
            errors.append(f"{source.source_name}: query must read from a robo_app view/table.")

        if source.default_access_level not in VALID_ACCESS_LEVELS:
            errors.append(
                f"{source.source_name}: invalid default_access_level {source.default_access_level}"
            )

        if source.default_language not in VALID_LANGUAGES:
            errors.append(f"{source.source_name}: invalid default_language {source.default_language}")

    return errors


def main() -> None:
    errors = validate_rag_registry()
    if errors:
        print("RAG registry validation failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print(f"RAG registry validation passed: {len(RAG_DOCUMENT_SOURCES)} source(s).")


if __name__ == "__main__":
    main()

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.db import get_connection  # noqa: E402


def build_manifest_row(chunk: dict[str, Any]) -> dict[str, Any]:
    payload = dict(chunk.get("payload") or {})
    collection = str(payload.get("qdrant_collection") or "")
    source = str(payload.get("source") or "")
    source_id = str(payload.get("source_id") or "")
    chunk_index = int(payload.get("chunk_index") or 0)
    point_id = str(chunk["point_id"])

    return {
        "id": f"{collection}:{source}:{source_id}:{chunk_index}",
        "qdrant_collection": collection,
        "source": source,
        "source_table": payload.get("source_table"),
        "source_view": payload.get("source_view"),
        "source_id": source_id,
        "chunk_index": chunk_index,
        "point_id": point_id,
        "content_hash": str(payload.get("content_hash") or ""),
        "domain": payload.get("domain"),
        "clinic_id": payload.get("clinic_id"),
        "access_level": payload.get("access_level"),
        "visibility": payload.get("visibility"),
        "language": payload.get("language"),
        "document_type": payload.get("document_type"),
        "source_updated_at": payload.get("updated_at"),
    }


def build_manifest_rows(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [build_manifest_row(chunk) for chunk in chunks]


def replace_index_manifest(qdrant_collection: str, rows: list[dict[str, Any]]) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM robo_rag.index_manifest WHERE qdrant_collection = %(collection)s",
                {"collection": qdrant_collection},
            )
            if rows:
                cur.executemany(
                    """
                    INSERT INTO robo_rag.index_manifest (
                      id,
                      qdrant_collection,
                      source,
                      source_table,
                      source_view,
                      source_id,
                      chunk_index,
                      point_id,
                      content_hash,
                      domain,
                      clinic_id,
                      access_level,
                      visibility,
                      language,
                      document_type,
                      source_updated_at,
                      indexed_at,
                      updated_at
                    ) VALUES (
                      %(id)s,
                      %(qdrant_collection)s,
                      %(source)s,
                      %(source_table)s,
                      %(source_view)s,
                      %(source_id)s,
                      %(chunk_index)s,
                      %(point_id)s,
                      %(content_hash)s,
                      %(domain)s,
                      %(clinic_id)s,
                      %(access_level)s,
                      %(visibility)s,
                      %(language)s,
                      %(document_type)s,
                      %(source_updated_at)s,
                      now(),
                      now()
                    )
                    """,
                    rows,
                )

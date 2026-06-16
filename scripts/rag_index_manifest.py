from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.db import get_connection  # noqa: E402


DocumentKey = tuple[str, str]


def document_key_from_row(row: dict[str, Any]) -> DocumentKey:
    return (str(row.get("source") or ""), str(row.get("source_id") or ""))


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


def fetch_index_manifest(qdrant_collection: str) -> dict[DocumentKey, dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                  source,
                  source_id,
                  array_agg(DISTINCT content_hash ORDER BY content_hash) AS content_hashes,
                  array_agg(point_id ORDER BY chunk_index) AS point_ids,
                  count(*) AS chunk_count
                FROM robo_rag.index_manifest
                WHERE qdrant_collection = %(collection)s
                GROUP BY source, source_id
                """,
                {"collection": qdrant_collection},
            )
            rows = [dict(row) for row in cur.fetchall()]

    manifest: dict[DocumentKey, dict[str, Any]] = {}
    for row in rows:
        key = (str(row["source"]), str(row["source_id"]))
        manifest[key] = {
            "content_hashes": list(row.get("content_hashes") or []),
            "point_ids": list(row.get("point_ids") or []),
            "chunk_count": int(row.get("chunk_count") or 0),
        }
    return manifest


def replace_index_manifest(qdrant_collection: str, rows: list[dict[str, Any]]) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM robo_rag.index_manifest WHERE qdrant_collection = %(collection)s",
                {"collection": qdrant_collection},
            )
            if rows:
                _insert_manifest_rows(cur, rows)


def replace_manifest_documents(
    qdrant_collection: str,
    document_keys: set[DocumentKey],
    rows: list[dict[str, Any]],
) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            _delete_manifest_documents(cur, qdrant_collection, document_keys)
            if rows:
                _insert_manifest_rows(cur, rows)


def delete_manifest_documents(qdrant_collection: str, document_keys: set[DocumentKey]) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            _delete_manifest_documents(cur, qdrant_collection, document_keys)


def _delete_manifest_documents(cur: Any, qdrant_collection: str, document_keys: set[DocumentKey]) -> None:
    if not document_keys:
        return
    cur.executemany(
        """
        DELETE FROM robo_rag.index_manifest
        WHERE qdrant_collection = %(collection)s
          AND source = %(source)s
          AND source_id = %(source_id)s
        """,
        [
            {
                "collection": qdrant_collection,
                "source": source,
                "source_id": source_id,
            }
            for source, source_id in sorted(document_keys)
        ],
    )


def _insert_manifest_rows(cur: Any, rows: list[dict[str, Any]]) -> None:
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

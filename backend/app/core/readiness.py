from typing import Any

from app.config import get_settings
from app.db import fetch_one
from app.rag.qdrant_store import QdrantVectorStore


def get_readiness_status() -> tuple[bool, dict[str, Any]]:
    checks: dict[str, Any] = {}

    checks["database"] = _check_database()
    checks["schemas"] = _check_required_relations()
    checks["rag_manifest"] = _check_rag_manifest()
    checks["qdrant"] = _check_qdrant()

    ready = all(check.get("ok") is True for check in checks.values())
    return ready, {
        "status": "ready" if ready else "not_ready",
        "checks": checks,
    }


def _check_database() -> dict[str, Any]:
    try:
        row = fetch_one("SELECT 1 AS ok")
        return {"ok": bool(row and row.get("ok") == 1)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _check_required_relations() -> dict[str, Any]:
    required_relations = [
        ("robo_app", "clinics"),
        ("robo_auth", "accounts"),
        ("robo_rag", "index_manifest"),
    ]
    try:
        rows = fetch_one(
            """
            SELECT count(*)::int AS relation_count
            FROM information_schema.tables
            WHERE (table_schema, table_name) IN (
              ('robo_app', 'clinics'),
              ('robo_auth', 'accounts'),
              ('robo_rag', 'index_manifest')
            )
            """,
        )
        count = int(rows.get("relation_count", 0)) if rows else 0
        return {
            "ok": count == len(required_relations),
            "required": [f"{schema}.{name}" for schema, name in required_relations],
            "found": count,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _check_rag_manifest() -> dict[str, Any]:
    settings = get_settings()
    if not settings.rag_vector_enabled:
        return {"ok": True, "skipped": True, "reason": "RAG vector disabled"}

    try:
        row = fetch_one(
            """
            SELECT count(*)::int AS chunk_count
            FROM robo_rag.index_manifest
            WHERE qdrant_collection = %(collection)s
            """,
            {"collection": settings.qdrant_collection},
        )
        chunk_count = int(row.get("chunk_count", 0)) if row else 0
        return {
            "ok": chunk_count > 0,
            "collection": settings.qdrant_collection,
            "chunk_count": chunk_count,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _check_qdrant() -> dict[str, Any]:
    settings = get_settings()
    if not settings.rag_vector_enabled:
        return {"ok": True, "skipped": True, "reason": "RAG vector disabled"}

    try:
        store = QdrantVectorStore()
        exists = store.collection_exists()
        return {
            "ok": exists,
            "mode": settings.qdrant_mode,
            "collection": store.collection_name,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

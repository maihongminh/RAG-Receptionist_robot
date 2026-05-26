from dataclasses import dataclass
from typing import Any

from app.db import fetch_all


@dataclass(frozen=True)
class RagDocumentSource:
    name: str
    query: str


RAG_DOCUMENT_SOURCES = [
    RagDocumentSource(
        name="admin_help_templates",
        query="""
            SELECT
              'admin_help_templates'::text AS source_table,
              id::text AS source_id,
              topic,
              title,
              title_vi,
              content,
              content_vi,
              'knowledge_article'::text AS document_type,
              'public'::text AS access_level,
              is_active,
              NULL::text AS updated_at
            FROM robo_app.knowledge_articles
            WHERE COALESCE(is_active, true) = true
        """,
    ),
]


def load_rag_documents() -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    for source in RAG_DOCUMENT_SOURCES:
        for row in fetch_all(source.query):
            document = dict(row)
            document.setdefault("source_table", source.name)
            documents.append(document)
    return sorted(
        documents,
        key=lambda item: (
            str(item.get("topic") or ""),
            str(item.get("title_vi") or item.get("title") or ""),
            str(item.get("source_id") or ""),
        ),
    )

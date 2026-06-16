import hashlib
from dataclasses import dataclass, field
from typing import Any

from app.db import fetch_all


@dataclass(frozen=True)
class RagDocumentSource:
    source_name: str
    source_view: str
    query: str
    source_tables: tuple[str, ...] = field(default_factory=tuple)
    domain: str = "clinic"
    default_access_level: str = "public"
    default_language: str = "vi"


RAG_DOCUMENT_SOURCES = [
    RagDocumentSource(
        source_name="knowledge_articles",
        source_view="robo_app.knowledge_articles",
        source_tables=("robo_raw.admin_help_templates",),
        query="""
            SELECT
              'knowledge_articles'::text AS source,
              'robo_app.knowledge_articles'::text AS source_table,
              id::text AS source_id,
              topic,
              title,
              title_vi,
              content,
              content_vi,
              'knowledge_article'::text AS document_type,
              'public'::text AS access_level,
              'vi'::text AS language,
              NULL::text AS clinic_id,
              is_active,
              NULL::text AS updated_at
            FROM robo_app.knowledge_articles
            WHERE COALESCE(is_active, true) = true
        """,
    ),
    RagDocumentSource(
        source_name="patient_question_templates",
        source_view="robo_app.patient_question_templates",
        source_tables=("robo_raw.patient_question_templates",),
        query="""
            SELECT
              'patient_question_templates'::text AS source,
              'robo_app.patient_question_templates'::text AS source_table,
              id::text AS source_id,
              category::text AS topic,
              question_text AS title,
              question_text_vi AS title_vi,
              CONCAT(
                'Suggested patient question. Category: ',
                category,
                '. Question: ',
                question_text
              ) AS content,
              CONCAT(
                'Mẫu câu hỏi gợi ý cho bệnh nhân. Chủ đề: ',
                CASE category
                  WHEN 'general' THEN 'thông tin chung'
                  WHEN 'medication' THEN 'thuốc'
                  WHEN 'test_results' THEN 'kết quả xét nghiệm'
                  WHEN 'lifestyle' THEN 'lối sống'
                  ELSE category
                END,
                '. Câu hỏi: ',
                question_text_vi
              ) AS content_vi,
              'patient_question_template'::text AS document_type,
              'public'::text AS access_level,
              'vi'::text AS language,
              NULL::text AS clinic_id,
              is_active,
              NULL::text AS updated_at
            FROM robo_app.patient_question_templates
            WHERE COALESCE(is_active, true) = true
        """,
    ),
]


def load_rag_documents() -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    for source in RAG_DOCUMENT_SOURCES:
        for row in fetch_all(source.query):
            document = normalize_rag_document(dict(row), source)
            documents.append(document)
    return sorted(
        documents,
        key=lambda item: (
            str(item.get("source") or ""),
            str(item.get("topic") or ""),
            str(item.get("title_vi") or item.get("title") or ""),
            str(item.get("source_id") or ""),
        ),
    )


def normalize_rag_document(row: dict[str, Any], source: RagDocumentSource) -> dict[str, Any]:
    document = dict(row)
    document.setdefault("source", source.source_name)
    document.setdefault("source_table", source.source_view)
    document.setdefault("source_view", source.source_view)
    document.setdefault("source_tables", list(source.source_tables))
    document.setdefault("domain", source.domain)
    document.setdefault("access_level", source.default_access_level)
    document.setdefault("visibility", document.get("access_level", source.default_access_level))
    document.setdefault("language", source.default_language)
    document.setdefault("clinic_id", None)
    document.setdefault("document_type", "knowledge_article")
    document.setdefault("updated_at", None)
    document["content_hash"] = build_content_hash(document)
    return document


def build_content_hash(document: dict[str, Any]) -> str:
    text = "\n".join(
        normalize_text(document.get(key, ""))
        for key in ("title", "title_vi", "content", "content_vi")
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split())

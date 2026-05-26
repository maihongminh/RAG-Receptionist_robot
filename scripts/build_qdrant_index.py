#!/usr/bin/env python3
import sys
import uuid
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.rag.embedding_client import EmbeddingClient  # noqa: E402
from app.rag.qdrant_store import QdrantVectorStore  # noqa: E402
from app.rag.rag_config import get_rag_config  # noqa: E402
from rag_documents import load_rag_documents  # noqa: E402


MAX_CHUNK_CHARS = 900
MIN_CHUNK_CHARS = 80
SOURCE_VIEW = "scripts/rag_documents.py"
SOURCE_DESCRIPTION = (
    "Only public knowledge/FAQ/process documents from the RAG source registry are vectorized. "
    "Structured data such as services, schedules, appointments and patients stays in SQL."
)


def main() -> None:
    rag_config = get_rag_config()
    rows = load_rag_documents()
    rows = [row for row in rows if row.get("access_level") == "public"]
    rows = filter_source_rows(rows, rag_config.excluded_topics)
    if not rows:
        raise RuntimeError("No active public rows found in RAG document sources.")

    print(f"Vector source registry: {SOURCE_VIEW}")
    print(SOURCE_DESCRIPTION)
    if rag_config.excluded_topics:
        print(f"Excluded RAG topics: {', '.join(rag_config.excluded_topics)}")

    embedding_client = EmbeddingClient()
    chunks = []
    for row in rows:
        title = row.get("title_vi") or row.get("title") or row.get("topic") or "Knowledge article"
        for chunk_index, text in enumerate(chunk_article(row)):
            embedding_text = f"{title}\n\n{text}"
            embedding = embedding_client.embed_text(embedding_text)
            if not embedding:
                raise RuntimeError(
                    "Embedding failed. Check Ollama and EMBEDDING_MODEL configuration."
                )
            chunks.append(
                {
                    "point_id": str(
                        uuid.uuid5(
                            uuid.NAMESPACE_URL,
                            f"{row['source_table']}:{row['source_id']}:{chunk_index}",
                        )
                    ),
                    "embedding": embedding,
                    "payload": {
                        "source_table": row.get("source_table"),
                        "source_id": str(row["source_id"]),
                        "chunk_index": chunk_index,
                        "topic": row.get("topic"),
                        "title": row.get("title"),
                        "title_vi": row.get("title_vi"),
                        "document_type": row.get("document_type"),
                        "access_level": row.get("access_level"),
                        "updated_at": str(row["updated_at"]) if row.get("updated_at") else None,
                        "content": text,
                        "content_vi": text,
                        "source": "qdrant:clinic_knowledge",
                    },
                }
            )

    if not chunks:
        raise RuntimeError("No chunks were generated from knowledge articles.")

    vector_store = QdrantVectorStore()
    vector_store.recreate_collection(vector_size=len(chunks[0]["embedding"]))
    vector_store.upsert_chunks(chunks)

    print(
        f"Indexed {len(chunks)} chunks from {len(rows)} rows in {SOURCE_VIEW} "
        f"into Qdrant collection '{vector_store.collection_name}'."
    )


def chunk_article(row: dict[str, Any]) -> list[str]:
    content = row.get("content_vi") or row.get("content") or ""
    text = normalize_text(content)
    if len(text) <= MAX_CHUNK_CHARS:
        return [text] if text else []

    paragraphs = [part.strip() for part in text.split("\n") if part.strip()]
    chunks = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= MAX_CHUNK_CHARS:
            current = candidate
            continue
        if current:
            chunks.append(current)
        current = paragraph

    if current:
        chunks.append(current)

    merged = []
    for chunk in chunks:
        if merged and len(chunk) < MIN_CHUNK_CHARS:
            merged[-1] = f"{merged[-1]}\n{chunk}"
        else:
            merged.append(chunk)
    return merged


def filter_source_rows(rows: list[dict[str, Any]], excluded_topics: tuple[str, ...]) -> list[dict[str, Any]]:
    excluded = {topic.strip().lower() for topic in excluded_topics if topic.strip()}
    if not excluded:
        return rows
    return [
        row
        for row in rows
        if str(row.get("topic") or "").strip().lower() not in excluded
    ]


def normalize_text(value: str) -> str:
    lines = [" ".join(line.split()) for line in str(value or "").splitlines()]
    return "\n".join(line for line in lines if line).strip()


if __name__ == "__main__":
    main()

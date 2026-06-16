#!/usr/bin/env python3
import argparse
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.rag.embedding_client import EmbeddingClient  # noqa: E402
from app.rag.qdrant_store import QdrantVectorStore  # noqa: E402
from app.rag.rag_config import get_rag_config  # noqa: E402
from rag_index_manifest import (  # noqa: E402
    DocumentKey,
    build_manifest_rows,
    delete_manifest_documents,
    document_key_from_row,
    fetch_index_manifest,
    replace_index_manifest,
    replace_manifest_documents,
)
from rag_documents import load_rag_documents  # noqa: E402


MAX_CHUNK_CHARS = 900
MIN_CHUNK_CHARS = 80
SOURCE_VIEW = "scripts/rag_documents.py"
SOURCE_DESCRIPTION = (
    "Only public knowledge/FAQ/process documents from the RAG source registry are vectorized. "
    "Structured data such as services, schedules, appointments and patients stays in SQL."
)


@dataclass(frozen=True)
class IncrementalPlan:
    unchanged: list[dict[str, Any]]
    changed_or_new: list[dict[str, Any]]
    stale_keys: set[DocumentKey]
    stale_point_ids: list[str]


def main() -> None:
    args = parse_args()
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
    vector_store = QdrantVectorStore()

    if args.mode == "incremental":
        sync_incremental(rows, embedding_client, vector_store)
        return

    sync_full(rows, embedding_client, vector_store)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build or sync the Qdrant RAG index.")
    parser.add_argument(
        "--mode",
        choices=("full", "incremental"),
        default="full",
        help="full recreates the collection; incremental only re-indexes changed documents.",
    )
    return parser.parse_args()


def sync_full(
    rows: list[dict[str, Any]],
    embedding_client: EmbeddingClient,
    vector_store: QdrantVectorStore,
) -> None:
    chunks = build_chunks(rows, embedding_client, vector_store)
    if not chunks:
        raise RuntimeError("No chunks were generated from knowledge articles.")

    vector_store.recreate_collection(vector_size=len(chunks[0]["embedding"]))
    vector_store.upsert_chunks(chunks)
    manifest_rows = build_manifest_rows(chunks)
    replace_index_manifest(vector_store.collection_name, manifest_rows)

    print(
        f"Indexed {len(chunks)} chunks from {len(rows)} rows in {SOURCE_VIEW} "
        f"into Qdrant collection '{vector_store.collection_name}'. "
        f"Manifest rows: {len(manifest_rows)}."
    )


def sync_incremental(
    rows: list[dict[str, Any]],
    embedding_client: EmbeddingClient,
    vector_store: QdrantVectorStore,
) -> None:
    manifest = fetch_index_manifest(vector_store.collection_name)
    if not manifest or not vector_store.collection_exists():
        print(
            "Incremental sync needs an existing collection and manifest; "
            "falling back to full rebuild."
        )
        sync_full(rows, embedding_client, vector_store)
        return

    plan = plan_incremental_sync(rows, manifest)
    chunks = build_chunks(plan.changed_or_new, embedding_client, vector_store)
    manifest_rows = build_manifest_rows(chunks)

    vector_store.delete_points(plan.stale_point_ids)
    if chunks:
        vector_store.upsert_chunks(chunks)

    changed_keys = {document_key_from_row(row) for row in plan.changed_or_new}
    if changed_keys:
        old_point_ids = [
            point_id
            for key in changed_keys
            for point_id in manifest.get(key, {}).get("point_ids", [])
        ]
        vector_store.delete_points(old_point_ids)
        replace_manifest_documents(vector_store.collection_name, changed_keys, manifest_rows)

    if plan.stale_keys:
        delete_manifest_documents(vector_store.collection_name, plan.stale_keys)

    print(
        f"Incremental sync complete for '{vector_store.collection_name}': "
        f"{len(plan.unchanged)} unchanged, "
        f"{len(plan.changed_or_new)} changed/new docs, "
        f"{len(plan.stale_keys)} stale docs, "
        f"{len(chunks)} upserted chunks."
    )


def plan_incremental_sync(
    rows: list[dict[str, Any]],
    manifest: dict[DocumentKey, dict[str, Any]],
) -> IncrementalPlan:
    current_keys = {document_key_from_row(row) for row in rows}
    unchanged: list[dict[str, Any]] = []
    changed_or_new: list[dict[str, Any]] = []

    for row in rows:
        key = document_key_from_row(row)
        current_hash = str(row.get("content_hash") or "")
        hashes = set(manifest.get(key, {}).get("content_hashes", []))
        if hashes == {current_hash}:
            unchanged.append(row)
        else:
            changed_or_new.append(row)

    stale_keys = set(manifest) - current_keys
    stale_point_ids = [
        point_id
        for key in stale_keys
        for point_id in manifest.get(key, {}).get("point_ids", [])
    ]

    return IncrementalPlan(
        unchanged=unchanged,
        changed_or_new=changed_or_new,
        stale_keys=stale_keys,
        stale_point_ids=stale_point_ids,
    )


def build_chunks(
    rows: list[dict[str, Any]],
    embedding_client: EmbeddingClient,
    vector_store: QdrantVectorStore,
) -> list[dict[str, Any]]:
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
                            f"{row['source']}:{row['source_id']}:{chunk_index}:{row.get('content_hash')}",
                        )
                    ),
                    "embedding": embedding,
                    "payload": {
                        "source": row.get("source"),
                        "source_table": row.get("source_table"),
                        "source_view": row.get("source_view"),
                        "source_tables": row.get("source_tables", []),
                        "source_id": str(row["source_id"]),
                        "chunk_index": chunk_index,
                        "domain": row.get("domain"),
                        "clinic_id": row.get("clinic_id"),
                        "topic": row.get("topic"),
                        "title": row.get("title"),
                        "title_vi": row.get("title_vi"),
                        "document_type": row.get("document_type"),
                        "access_level": row.get("access_level"),
                        "visibility": row.get("visibility") or row.get("access_level"),
                        "language": row.get("language"),
                        "updated_at": str(row["updated_at"]) if row.get("updated_at") else None,
                        "content_hash": row.get("content_hash"),
                        "content": text,
                        "content_vi": text,
                        "qdrant_collection": vector_store.collection_name,
                    },
                }
            )
    return chunks


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

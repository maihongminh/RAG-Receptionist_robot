from pathlib import Path
from typing import Any

from qdrant_client import QdrantClient, models

from app.config import get_settings


class QdrantVectorStore:
    """Qdrant-backed vector index for RAG chunks.

    Postgres remains the source of truth. Qdrant stores rebuildable semantic
    search chunks and payloads only.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.collection_name = self.settings.qdrant_collection
        self.client = self._build_client()

    def _build_client(self) -> QdrantClient:
        if self.settings.qdrant_mode.lower() == "local":
            path = Path(self.settings.qdrant_path)
            path.mkdir(parents=True, exist_ok=True)
            return QdrantClient(path=str(path))
        return QdrantClient(url=self.settings.qdrant_url)

    def recreate_collection(self, vector_size: int) -> None:
        if self.client.collection_exists(self.collection_name):
            self.client.delete_collection(self.collection_name)
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE,
            ),
        )

    def upsert_chunks(self, chunks: list[dict[str, Any]]) -> None:
        points = [
            models.PointStruct(
                id=chunk["point_id"],
                vector=chunk["embedding"],
                payload=chunk["payload"],
            )
            for chunk in chunks
        ]
        if points:
            self.client.upsert(collection_name=self.collection_name, points=points)

    def search(
        self,
        query_vector: list[float],
        limit: int = 3,
        score_threshold: float | None = None,
        payload_filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if not self.client.collection_exists(self.collection_name):
            return []

        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=self._build_filter(payload_filter),
            with_payload=True,
            with_vectors=False,
        )

        rows = []
        for point in response.points:
            payload = dict(point.payload or {})
            payload["_score"] = round(float(point.score), 3)
            rows.append(payload)
        return rows

    def _build_filter(self, payload_filter: dict[str, Any] | None) -> models.Filter | None:
        if not payload_filter:
            return None
        conditions = [
            models.FieldCondition(
                key=key,
                match=models.MatchValue(value=value),
            )
            for key, value in payload_filter.items()
            if value is not None
        ]
        if not conditions:
            return None
        return models.Filter(must=conditions)

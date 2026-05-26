import json
import logging
import urllib.error
import urllib.request

from app.config import get_settings


logger = logging.getLogger(__name__)


class EmbeddingClient:
    """Embedding provider abstraction for local RAG retrieval."""

    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def enabled(self) -> bool:
        return self.settings.embedding_provider.lower() == "ollama"

    def embed_text(self, text: str) -> list[float] | None:
        value = " ".join(str(text or "").split())
        if not value or not self.enabled:
            return None

        embedding = self._embed_with_ollama_embed(value)
        if embedding is not None:
            return embedding
        return self._embed_with_ollama_embeddings(value)

    def _embed_with_ollama_embed(self, text: str) -> list[float] | None:
        payload = {
            "model": self.settings.embedding_model,
            "input": text,
        }
        try:
            body = self._post_json(self._ollama_embed_url(), payload)
            embeddings = body.get("embeddings")
            if isinstance(embeddings, list) and embeddings:
                return [float(value) for value in embeddings[0]]
        except (TypeError, ValueError, urllib.error.URLError) as exc:
            logger.warning("Ollama /api/embed failed: %s", exc)
        return None

    def _embed_with_ollama_embeddings(self, text: str) -> list[float] | None:
        payload = {
            "model": self.settings.embedding_model,
            "prompt": text,
        }
        try:
            body = self._post_json(self._ollama_embeddings_url(), payload)
            embedding = body.get("embedding")
            if isinstance(embedding, list) and embedding:
                return [float(value) for value in embedding]
        except (TypeError, ValueError, urllib.error.URLError) as exc:
            logger.warning("Ollama /api/embeddings failed: %s", exc)
        return None

    def _post_json(self, url: str, payload: dict) -> dict:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(
            request,
            timeout=self.settings.embedding_timeout_seconds,
        ) as response:
            raw = response.read().decode("utf-8")
        return json.loads(raw)

    def _ollama_embed_url(self) -> str:
        base_url = self.settings.embedding_base_url.rstrip("/")
        if base_url.endswith("/api/embed"):
            return base_url
        return f"{base_url}/api/embed"

    def _ollama_embeddings_url(self) -> str:
        base_url = self.settings.embedding_base_url.rstrip("/")
        if base_url.endswith("/api/embeddings"):
            return base_url
        return f"{base_url}/api/embeddings"

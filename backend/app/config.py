import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")


class Settings(BaseModel):
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql:///robo_reception",
    )
    default_domain: str = os.getenv("DEFAULT_DOMAIN", "clinic")
    llm_provider: str = os.getenv("LLM_PROVIDER", "none")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    llm_timeout_seconds: int = int(os.getenv("LLM_TIMEOUT_SECONDS", "20"))
    llm_intent_timeout_seconds: int = int(os.getenv("LLM_INTENT_TIMEOUT_SECONDS", "10"))
    llm_answer_timeout_seconds: int = int(os.getenv("LLM_ANSWER_TIMEOUT_SECONDS", "20"))
    llm_context_char_limit: int = int(os.getenv("LLM_CONTEXT_CHAR_LIMIT", "3500"))
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    embedding_provider: str = os.getenv("EMBEDDING_PROVIDER", "ollama")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
    embedding_base_url: str = os.getenv("EMBEDDING_BASE_URL", "http://localhost:11434")
    embedding_timeout_seconds: int = int(os.getenv("EMBEDDING_TIMEOUT_SECONDS", "60"))
    qdrant_mode: str = os.getenv("QDRANT_MODE", "local")
    qdrant_path: str = os.getenv("QDRANT_PATH", str(ROOT_DIR.parent / "qdrant_data"))
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_collection: str = os.getenv("QDRANT_COLLECTION", "clinic_knowledge")
    rag_vector_enabled: bool = os.getenv("RAG_VECTOR_ENABLED", "true").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()

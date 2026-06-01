import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")


def _bool_env(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.lower() in {"1", "true", "yes", "on"}


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
    auth_token_secret: str = os.getenv("AUTH_TOKEN_SECRET", "dev-local-auth-secret")
    auth_token_ttl_seconds: int = int(os.getenv("AUTH_TOKEN_TTL_SECONDS", "86400"))
    auth_allow_request_context: bool = _bool_env("AUTH_ALLOW_REQUEST_CONTEXT", False)
    auth_allow_legacy_role_login: bool = _bool_env("AUTH_ALLOW_LEGACY_ROLE_LOGIN", False)
    auth_max_failed_login_attempts: int = int(os.getenv("AUTH_MAX_FAILED_LOGIN_ATTEMPTS", "5"))
    auth_lock_seconds: int = int(os.getenv("AUTH_LOCK_SECONDS", "900"))
    rag_vector_enabled: bool = _bool_env("RAG_VECTOR_ENABLED", True)


@lru_cache
def get_settings() -> Settings:
    return Settings()

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class RagConfig:
    """Tunable RAG retrieval parameters.

    These values control retrieval behavior only. They do not replace
    PolicyGuard or SQL source-of-truth rules.
    """

    vector_top_k: int = 5
    vector_min_score: float = 0.60
    keyword_source_limit: int = 500
    keyword_top_k: int = 3
    keyword_min_score: float = 0.18
    context_max_rows: int = 5
    api_preview_max_rows: int = 50
    sql_result_limit: int = 1000
    empty_confidence: float = 0.0
    excluded_topics: tuple[str, ...] = ("overview", "roles")


@lru_cache
def get_rag_config() -> RagConfig:
    return RagConfig(
        vector_top_k=_int_env("RAG_TOP_K", 5),
        vector_min_score=_float_env("RAG_MIN_SCORE", 0.60),
        keyword_source_limit=_int_env("RAG_KEYWORD_SOURCE_LIMIT", 500),
        keyword_top_k=_int_env("RAG_KEYWORD_TOP_K", 3),
        keyword_min_score=_float_env("RAG_KEYWORD_MIN_SCORE", 0.18),
        context_max_rows=_int_env("RAG_CONTEXT_MAX_ROWS", 5),
        api_preview_max_rows=_int_env("RAG_API_PREVIEW_MAX_ROWS", 50),
        sql_result_limit=_int_env("RAG_SQL_RESULT_LIMIT", 1000),
        empty_confidence=_float_env("RAG_EMPTY_CONFIDENCE", 0.0),
        excluded_topics=_tuple_env("RAG_EXCLUDED_TOPICS", ("overview", "roles")),
    )


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


def _float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return float(value)


def _tuple_env(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return tuple(item.strip().lower() for item in value.split(",") if item.strip())

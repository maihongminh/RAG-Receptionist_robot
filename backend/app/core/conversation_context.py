from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any

from app.core.schemas import Intent, ToolResult


@dataclass
class ConversationTurn:
    intent: str
    entities: dict[str, Any] = field(default_factory=dict)
    rows: list[dict[str, Any]] = field(default_factory=list)
    source: str = "none"
    updated_at: float = field(default_factory=time)


class ConversationContextStore:
    """Small in-memory context store for MVP follow-up questions.

    This is intentionally process-local. It is enough for local MVP testing;
    production should replace it with Redis/PostgreSQL session storage.
    """

    def __init__(self, ttl_seconds: int = 3600) -> None:
        self.ttl_seconds = ttl_seconds
        self._turns: dict[str, ConversationTurn] = {}

    def get(self, session_id: str | None) -> ConversationTurn | None:
        if not session_id:
            return None
        turn = self._turns.get(session_id)
        if not turn:
            return None
        if time() - turn.updated_at > self.ttl_seconds:
            self._turns.pop(session_id, None)
            return None
        return turn

    def remember(self, session_id: str | None, intent: Intent, result: ToolResult) -> None:
        if not session_id or not result.rows:
            return
        if intent.intent not in {
            "service_category_list",
            "service_catalog_summary",
            "service_category_detail",
            "service_price",
        }:
            return
        entities = dict(intent.entities or {})
        first_row = result.rows[0]
        for key in ("category_offset", "display_limit", "total_categories"):
            if key in first_row and key not in entities:
                entities[key.removeprefix("category_") if key == "category_offset" else key] = first_row[key]

        self._turns[session_id] = ConversationTurn(
            intent=intent.intent,
            entities=entities,
            rows=[dict(row) for row in result.rows],
            source=result.source,
        )


_STORE = ConversationContextStore()


def get_conversation_context_store() -> ConversationContextStore:
    return _STORE

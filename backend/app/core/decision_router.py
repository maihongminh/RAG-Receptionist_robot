from app.core.schemas import Intent


class DecisionRouter:
    def route(self, intent: Intent) -> str:
        if intent.requires_auth:
            return "auth"
        if intent.data_source in {"sql", "rag"}:
            return intent.data_source
        return "none"

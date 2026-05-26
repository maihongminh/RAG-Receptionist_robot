from app.auth.audit_logger import AuditLogger
from app.auth.auth_context import AuthContextResolver
from app.core.decision_router import DecisionRouter
from app.rag.grounded_response_generator import GroundedResponseGenerator
from app.rag.rag_config import get_rag_config
from app.llm.llm_client import LLMClient
from app.auth.policy_guard import PolicyGuard
from app.core.response_generator import ResponseGenerator
from app.core.rule_intent_parser import RuleIntentParser
from app.core.schemas import AskRequest, AskResponse, Intent, ToolResult
from app.core.tool_registry import ToolRegistry
from app.domains.base import DomainAdapter


class Orchestrator:
    def __init__(self, adapters: dict[str, DomainAdapter], default_domain: str = "clinic") -> None:
        self.default_domain = default_domain
        self.llm_client = LLMClient()
        self.rule_parser = RuleIntentParser()
        self.auth_resolver = AuthContextResolver()
        self.decision_router = DecisionRouter()
        self.policy_guard = PolicyGuard()
        self.tool_registry = ToolRegistry(adapters)
        self.response_generator = ResponseGenerator()
        self.grounded_response_generator = GroundedResponseGenerator()
        self.audit_logger = AuditLogger()

    def handle(self, payload: AskRequest) -> AskResponse:
        domain = payload.domain or self.default_domain
        question = payload.question.strip()
        if not question:
            raise ValueError("Question is required.")

        auth = self.auth_resolver.resolve(payload)
        rule_intent = self.rule_parser.parse(question, domain)
        if self._should_use_rule_before_llm(rule_intent):
            intent = rule_intent
            parser_source = "rule"
        else:
            intent = self.llm_client.parse_intent(question, domain)
            parser_source = "llm"
            if intent is None:
                intent = rule_intent
                parser_source = "rule"
            else:
                intent = self._normalize_llm_intent(intent, rule_intent, question)

        policy_decision = self.policy_guard.authorize(intent, auth)
        self.audit_logger.log_policy_decision(
            auth=auth,
            intent=intent,
            decision=policy_decision,
        )

        if not policy_decision.allowed:
            result = ToolResult(
                tool_name="policy_guard",
                source="policy",
                message=policy_decision.reason,
                confidence=intent.confidence,
            )
            answer = self.response_generator.generate(question, intent, result, auth)
            return AskResponse(
                question=question,
                answer=answer,
                domain=intent.domain,
                intent=intent.intent,
                confidence=intent.confidence,
                parser_source=parser_source,
                answer_source="template",
                sources=["policy"],
                data=[],
                requires_auth=intent.requires_auth,
            )

        route = self.decision_router.route(intent)
        if route == "auth":
            result = self.tool_registry.run(intent, auth)
        elif intent.intent in {"greeting", "appointment_booking"}:
            result = self.tool_registry.run(intent)
        elif route in {"sql", "rag"}:
            result = self.tool_registry.run(intent)
        else:
            result = ToolResult(
                tool_name="none",
                source="none",
                message="Câu hỏi này hiện nằm ngoài phạm vi hỗ trợ của robot lễ tân.",
                confidence=intent.confidence,
            )

        answer_source = "template"
        answer = self.response_generator.generate(question, intent, result, auth)
        grounded_answer = self.grounded_response_generator.generate(question, intent, result, auth)
        if grounded_answer:
            answer = grounded_answer
            answer_source = "llm_grounded" if intent.intent == "knowledge_search" else "llm_formatted"

        self.audit_logger.log_tool_result(auth=auth, intent=intent, result=result)

        max_rows = get_rag_config().api_preview_max_rows
        return AskResponse(
            question=question,
            answer=answer,
            domain=intent.domain,
            intent=intent.intent,
            confidence=max(intent.confidence, result.confidence),
            parser_source=parser_source,
            answer_source=answer_source,
            sources=[result.source] if result.source != "none" else [],
            data=result.rows[:max_rows],
            requires_auth=intent.requires_auth,
        )

    def _should_use_rule_before_llm(self, rule_intent: Intent) -> bool:
        if rule_intent.intent == "knowledge_search" and rule_intent.confidence >= 0.65:
            return True
        return rule_intent.intent == "service_category_list" and "offset" in rule_intent.entities

    def _normalize_llm_intent(
        self,
        intent: Intent,
        rule_intent: Intent,
        question: str,
    ) -> Intent:
        """Make local LLM output obey backend routing contracts.

        Small local models can classify the intent correctly while returning a
        wrong data_source. Routing must stay deterministic because SQL/RAG/Auth
        tools are owned by backend policy, not by the model.
        """

        source_by_intent = {
            "greeting": "none",
            "general_info": "sql",
            "service_price": "sql",
            "service_category_list": "sql",
            "service_catalog_summary": "sql",
            "service_category_detail": "sql",
            "doctor_schedule": "sql",
            "knowledge_search": "rag",
            "appointment_booking": "none",
            "appointment_lookup": "auth",
            "lab_result_lookup": "auth",
            "personal_data": "auth",
            "medical_advice": "none",
            "out_of_scope": "none",
        }
        auth_required_by_intent = {
            "appointment_lookup": True,
            "lab_result_lookup": True,
            "personal_data": True,
        }

        if rule_intent.intent == "service_category_detail" and intent.intent in {
            "service_category_list",
            "service_catalog_summary",
            "service_price",
        }:
            intent = rule_intent.model_copy(
                update={"confidence": max(intent.confidence, rule_intent.confidence)}
            )
        elif rule_intent.intent == "service_catalog_summary" and intent.intent in {
            "service_category_list",
            "service_price",
        }:
            intent = rule_intent.model_copy(
                update={"confidence": max(intent.confidence, rule_intent.confidence)}
            )

        entities = dict(intent.entities or {})
        if intent.intent == rule_intent.intent:
            for key, value in rule_intent.entities.items():
                if entities.get(key) in {None, ""}:
                    entities[key] = value
            if (
                intent.intent == "service_category_list"
                and rule_intent.entities.get("service_type") == "lab"
            ):
                entities["service_type"] = "lab"
            if (
                intent.intent == "general_info"
                and rule_intent.entities.get("profile_query") == ""
            ):
                entities["profile_query"] = ""

        if intent.intent == "service_price" and not entities.get("service_query"):
            entities["service_query"] = question.strip()
        elif intent.intent == "service_category_list" and not entities.get("service_type"):
            entities["service_type"] = rule_intent.entities.get("service_type", "all")
        elif intent.intent == "service_catalog_summary" and not entities.get("service_type"):
            entities["service_type"] = rule_intent.entities.get("service_type", "all")
        elif intent.intent == "service_category_detail":
            if not entities.get("category_query"):
                entities["category_query"] = rule_intent.entities.get("category_query", question.strip())
            if not entities.get("service_type"):
                entities["service_type"] = rule_intent.entities.get("service_type", "all")
        elif intent.intent == "general_info" and not entities.get("profile_query"):
            entities["profile_query"] = rule_intent.entities.get("profile_query", "")
        elif intent.intent == "doctor_schedule":
            if not entities.get("doctor_query"):
                entities["doctor_query"] = rule_intent.entities.get("doctor_query", question.strip())
            if entities.get("weekday") is None and rule_intent.entities.get("weekday") is not None:
                entities["weekday"] = rule_intent.entities["weekday"]
        elif intent.intent == "knowledge_search" and not entities.get("knowledge_query"):
            entities["knowledge_query"] = question.strip()
        elif intent.intent == "appointment_booking" and not entities.get("booking_query"):
            entities["booking_query"] = question.strip()
        elif intent.intent == "lab_result_lookup" and not entities.get("result_query"):
            entities["result_query"] = question.strip()

        return intent.model_copy(
            update={
                "entities": entities,
                "data_source": source_by_intent[intent.intent],
                "requires_auth": auth_required_by_intent.get(
                    intent.intent,
                    intent.requires_auth,
                ),
            }
        )

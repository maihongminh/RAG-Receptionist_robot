from app.core.schemas import AuthContext, Intent, ToolResult
from app.domains.base import DomainAdapter


class ToolRegistry:
    def __init__(self, adapters: dict[str, DomainAdapter]) -> None:
        self.adapters = adapters

    def run(self, intent: Intent, auth: AuthContext | None = None) -> ToolResult:
        adapter = self.adapters.get(intent.domain)
        if adapter is None:
            raise ValueError(f"Unsupported domain: {intent.domain}")

        if intent.intent == "greeting":
            return ToolResult(
                tool_name="core.greeting",
                source="system_capabilities",
                message="Greeting and capability introduction.",
                confidence=0.9,
            )
        if intent.intent == "general_info":
            return adapter.get_public_profile(intent.entities)
        if intent.intent == "service_price":
            return adapter.list_services(intent.entities)
        if intent.intent == "service_category_list":
            return adapter.list_service_categories(intent.entities)
        if intent.intent == "service_catalog_summary":
            return adapter.summarize_service_catalog(intent.entities)
        if intent.intent == "service_category_detail":
            return adapter.list_services_by_category(intent.entities)
        if intent.intent == "service_package_detail":
            return adapter.lookup_service_package_detail(intent.entities)
        if intent.intent == "lab_indicator_detail":
            return adapter.lookup_lab_indicator_detail(intent.entities)
        if intent.intent == "icd10_lookup":
            return adapter.lookup_icd10_codes(intent.entities)
        if intent.intent == "security_check_summary":
            return adapter.lookup_security_checks(intent.entities, auth or AuthContext(role="guest"))
        if intent.intent == "doctor_schedule":
            return adapter.check_availability(intent.entities)
        if intent.intent == "knowledge_search":
            return adapter.search_knowledge(intent.entities)
        if intent.intent == "appointment_booking":
            return adapter.create_request(intent.entities)
        if intent.intent == "lab_result_lookup":
            return adapter.lookup_lab_results(intent.entities, auth or AuthContext(role="guest"))
        if intent.intent == "partner_lab_request_lookup":
            return adapter.lookup_partner_lab_requests(intent.entities, auth or AuthContext(role="guest"))
        if intent.intent == "patient_timeline_summary":
            return adapter.lookup_patient_timeline(intent.entities, auth or AuthContext(role="guest"))
        if intent.intent == "visit_summary_lookup":
            return adapter.lookup_visit_summary(intent.entities, auth or AuthContext(role="guest"))
        if intent.intent == "billing_summary_lookup":
            return adapter.lookup_billing_summary(intent.entities, auth or AuthContext(role="guest"))
        if intent.intent == "patient_profile_summary":
            return adapter.lookup_patient_profile(intent.entities, auth or AuthContext(role="guest"))
        if intent.intent in {"appointment_lookup", "personal_data"}:
            return adapter.lookup_private_data(intent.entities, auth or AuthContext(role="guest"))

        return ToolResult(
            tool_name="none",
            source="none",
            message="Không tìm thấy công cụ phù hợp cho câu hỏi này.",
            confidence=0.0,
        )

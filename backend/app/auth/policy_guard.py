from app.auth.permissions import PermissionDecision, is_tool_allowed
from app.core.schemas import AuthContext, Intent


INTENT_TOOL_MAP = {
    "greeting": "core.greeting",
    "general_info": "clinic.get_public_profile",
    "service_price": "clinic.search_services",
    "service_category_list": "clinic.list_service_categories",
    "service_catalog_summary": "clinic.summarize_service_catalog",
    "service_category_detail": "clinic.list_services_by_category",
    "doctor_schedule": "clinic.search_doctor_schedules",
    "knowledge_search": "clinic.search_knowledge",
    "appointment_booking": "clinic.create_appointment_request",
    "appointment_lookup": "clinic.lookup_private_data",
    "lab_result_lookup": "clinic.lookup_lab_results",
    "patient_timeline_summary": "clinic.lookup_patient_timeline",
    "patient_profile_summary": "clinic.lookup_patient_profile",
    "personal_data": "clinic.lookup_private_data",
    "medical_advice": "none",
    "out_of_scope": "none",
}


class PolicyGuard:
    """Authorize intent/tool access before a tool runs."""

    def authorize(self, intent: Intent, auth: AuthContext) -> PermissionDecision:
        if intent.requires_auth and auth.role == "guest":
            return PermissionDecision(
                allowed=False,
                reason="Authentication is required for this request.",
            )

        tool_name = INTENT_TOOL_MAP.get(intent.intent, "none")
        if tool_name == "none":
            return PermissionDecision(allowed=True, reason="No protected tool needed.")

        decision = is_tool_allowed(auth.role, tool_name)
        if not decision.allowed:
            return decision

        return self._authorize_scope(intent, auth)

    def _authorize_scope(self, intent: Intent, auth: AuthContext) -> PermissionDecision:
        if intent.intent not in {
            "personal_data",
            "appointment_lookup",
            "lab_result_lookup",
            "patient_timeline_summary",
            "patient_profile_summary",
        }:
            return PermissionDecision(allowed=True, reason="Public or non-private scope.")

        if auth.role == "patient" and not auth.patient_id:
            return PermissionDecision(
                allowed=False,
                reason="Patient requests require patient_id in auth context.",
            )

        if auth.role == "doctor" and not auth.doctor_id:
            return PermissionDecision(
                allowed=False,
                reason="Doctor private data requests require doctor_id in auth context.",
            )

        if auth.role in {"receptionist", "clinic_admin"} and not auth.clinic_id:
            return PermissionDecision(
                allowed=False,
                reason=f"{auth.role} requests require clinic_id in auth context.",
            )

        return PermissionDecision(allowed=True, reason="Scope allowed.")

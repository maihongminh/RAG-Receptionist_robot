from dataclasses import dataclass


PUBLIC_TOOLS = {
    "core.greeting",
    "clinic.get_public_profile",
    "clinic.search_services",
    "clinic.list_service_categories",
    "clinic.summarize_service_catalog",
    "clinic.list_services_by_category",
    "clinic.lookup_service_package_detail",
    "clinic.lookup_lab_indicator_detail",
    "clinic.lookup_icd10_codes",
    "clinic.search_doctor_schedules",
    "clinic.search_knowledge",
    "clinic.create_appointment_request",
}


ROLE_TOOL_PERMISSIONS: dict[str, set[str]] = {
    "guest": PUBLIC_TOOLS,
    "patient": PUBLIC_TOOLS
    | {
        "clinic.lookup_private_data",
        "clinic.lookup_lab_results",
        "clinic.lookup_partner_lab_requests",
        "clinic.lookup_patient_profile",
        "clinic.lookup_patient_timeline",
        "clinic.lookup_visit_summary",
        "clinic.lookup_billing_summary",
    },
    "doctor": PUBLIC_TOOLS
    | {
        "clinic.lookup_private_data",
        "clinic.lookup_lab_results",
        "clinic.lookup_visit_summary",
    },
    "receptionist": PUBLIC_TOOLS
    | {
        "clinic.lookup_private_data",
        "clinic.lookup_lab_results",
        "clinic.lookup_partner_lab_requests",
        "clinic.lookup_patient_profile",
        "clinic.lookup_patient_timeline",
        "clinic.lookup_visit_summary",
        "clinic.lookup_billing_summary",
    },
    "clinic_admin": PUBLIC_TOOLS
    | {
        "clinic.lookup_private_data",
        "clinic.lookup_lab_results",
        "clinic.lookup_partner_lab_requests",
        "clinic.lookup_patient_profile",
        "clinic.lookup_patient_timeline",
        "clinic.lookup_visit_summary",
        "clinic.lookup_billing_summary",
        "clinic.manage_services",
    },
    "system_admin": {"*"},
}


@dataclass(frozen=True)
class PermissionDecision:
    allowed: bool
    reason: str


def is_tool_allowed(role: str, tool_name: str) -> PermissionDecision:
    permissions = ROLE_TOOL_PERMISSIONS.get(role, ROLE_TOOL_PERMISSIONS["guest"])
    if "*" in permissions or tool_name in permissions:
        return PermissionDecision(allowed=True, reason="allowed")
    return PermissionDecision(
        allowed=False,
        reason=f"Role '{role}' is not allowed to use tool '{tool_name}'.",
    )

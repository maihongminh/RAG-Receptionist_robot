from app.core.schemas import AuthContext, ToolResult
from app.domains.base import DomainAdapter
from app.domains.clinic.sql_tools import ClinicSqlTools


class ClinicAdapter(DomainAdapter):
    def __init__(self) -> None:
        self.sql_tools = ClinicSqlTools()

    def get_public_profile(self, entities: dict) -> ToolResult:
        return self.sql_tools.get_public_profile(entities.get("profile_query", ""))

    def list_services(self, entities: dict) -> ToolResult:
        return self.sql_tools.search_services(entities.get("service_query", ""))

    def list_service_categories(self, entities: dict) -> ToolResult:
        return self.sql_tools.list_service_categories(
            service_type=entities.get("service_type", "all"),
            offset=entities.get("offset", 0),
            display_limit=entities.get("display_limit"),
        )

    def summarize_service_catalog(self, entities: dict) -> ToolResult:
        return self.sql_tools.summarize_service_catalog(
            service_type=entities.get("service_type", "all"),
            offset=entities.get("offset", 0),
            display_limit=entities.get("display_limit"),
        )

    def list_services_by_category(self, entities: dict) -> ToolResult:
        return self.sql_tools.list_services_by_category(
            category_query=entities.get("category_query", ""),
            service_type=entities.get("service_type", "all"),
        )

    def check_availability(self, entities: dict) -> ToolResult:
        return self.sql_tools.search_doctor_schedules(
            doctor_query=entities.get("doctor_query", ""),
            weekday=entities.get("weekday"),
        )

    def search_knowledge(self, entities: dict) -> ToolResult:
        return self.sql_tools.search_knowledge(entities.get("knowledge_query", ""))

    def lookup_private_data(self, entities: dict, auth: AuthContext) -> ToolResult:
        return self.sql_tools.lookup_private_data(entities, auth)

    def lookup_lab_results(self, entities: dict, auth: AuthContext) -> ToolResult:
        return self.sql_tools.lookup_lab_results(entities, auth)

    def create_request(self, entities: dict) -> ToolResult:
        return ToolResult(
            tool_name="clinic.create_appointment_request",
            source="appointment_requests",
            message="Appointment booking is not enabled yet.",
            confidence=0.8,
        )

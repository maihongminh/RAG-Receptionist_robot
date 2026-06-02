from abc import ABC, abstractmethod

from app.core.schemas import AuthContext, ToolResult


class DomainAdapter(ABC):
    @abstractmethod
    def get_public_profile(self, entities: dict) -> ToolResult:
        raise NotImplementedError

    @abstractmethod
    def list_services(self, entities: dict) -> ToolResult:
        raise NotImplementedError

    @abstractmethod
    def list_service_categories(self, entities: dict) -> ToolResult:
        raise NotImplementedError

    @abstractmethod
    def summarize_service_catalog(self, entities: dict) -> ToolResult:
        raise NotImplementedError

    @abstractmethod
    def list_services_by_category(self, entities: dict) -> ToolResult:
        raise NotImplementedError

    @abstractmethod
    def check_availability(self, entities: dict) -> ToolResult:
        raise NotImplementedError

    @abstractmethod
    def search_knowledge(self, entities: dict) -> ToolResult:
        raise NotImplementedError

    @abstractmethod
    def lookup_private_data(self, entities: dict, auth: AuthContext) -> ToolResult:
        raise NotImplementedError

    @abstractmethod
    def lookup_lab_results(self, entities: dict, auth: AuthContext) -> ToolResult:
        raise NotImplementedError

    @abstractmethod
    def lookup_patient_profile(self, entities: dict, auth: AuthContext) -> ToolResult:
        raise NotImplementedError

    @abstractmethod
    def lookup_patient_timeline(self, entities: dict, auth: AuthContext) -> ToolResult:
        raise NotImplementedError

    @abstractmethod
    def create_request(self, entities: dict) -> ToolResult:
        raise NotImplementedError

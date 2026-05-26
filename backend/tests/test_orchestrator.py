from app.config import Settings
from app.core.orchestrator import Orchestrator
from app.core.schemas import AskRequest, AuthContext, Intent, ToolResult
from app.domains.base import DomainAdapter


class FakeClinicAdapter(DomainAdapter):
    def get_public_profile(self, entities: dict) -> ToolResult:
        return ToolResult(
            tool_name="clinic.get_public_profile",
            source="fake.clinics",
            rows=[
                {
                    "name": "Demo Clinic",
                    "address": "123 Demo",
                    "phone": "0123",
                    "email": "demo@example.com",
                    "working_hours_start": "08:00:00",
                    "working_hours_end": "17:00:00",
                }
            ],
            confidence=0.9,
        )

    def list_services(self, entities: dict) -> ToolResult:
        return ToolResult(
            tool_name="clinic.search_services",
            source="fake.services",
            rows=[
                {
                    "name": "CT Brain without contrast",
                    "price_amount": 120000,
                    "currency_code": "USD",
                }
            ],
            confidence=0.95,
        )

    def list_service_categories(self, entities: dict) -> ToolResult:
        return ToolResult(
            tool_name="clinic.list_service_categories",
            source="fake.services",
            rows=[
                {
                    "service_type": "lab",
                    "category_name": "Check Liver Function",
                    "service_count": 12,
                    "min_price": 1.0,
                    "max_price": 6.25,
                    "currency_code": "USD",
                }
            ],
            confidence=0.85,
        )

    def summarize_service_catalog(self, entities: dict) -> ToolResult:
        return ToolResult(
            tool_name="clinic.summarize_service_catalog",
            source="fake.services",
            rows=[
                {
                    "service_type": "lab",
                    "category_name": "Blood test",
                    "service_count": 12,
                    "min_price": 2.0,
                    "max_price": 5.0,
                    "currency_code": "USD",
                    "total_services": 20,
                    "total_categories": 2,
                },
                {
                    "service_type": "imaging",
                    "category_name": "CT Scan",
                    "service_count": 8,
                    "min_price": 120000,
                    "max_price": 350000,
                    "currency_code": "USD",
                    "total_services": 20,
                    "total_categories": 2,
                },
            ],
            confidence=0.88,
        )

    def list_services_by_category(self, entities: dict) -> ToolResult:
        return ToolResult(
            tool_name="clinic.list_services_by_category",
            source="fake.services",
            rows=[
                {
                    "code": "CT001",
                    "name": "CT Brain without contrast",
                    "category_name": "CT Scan",
                    "price_amount": 120000,
                    "currency_code": "USD",
                    "duration_minutes": 30,
                    "service_type": "imaging",
                    "total_services_in_category": 2,
                    "matched_category_name": "CT Scan",
                },
                {
                    "code": "CT002",
                    "name": "CT Brain with contrast",
                    "category_name": "CT Scan",
                    "price_amount": 180000,
                    "currency_code": "USD",
                    "duration_minutes": 30,
                    "service_type": "imaging",
                    "total_services_in_category": 2,
                    "matched_category_name": "CT Scan",
                },
            ],
            confidence=0.9,
        )

    def check_availability(self, entities: dict) -> ToolResult:
        return ToolResult(
            tool_name="clinic.search_doctor_schedules",
            source="fake.doctor_schedules",
            rows=[
                {
                    "doctor_name": "SUON SAVUTH",
                    "day_of_week": 4,
                    "start_time": "08:00:00",
                    "end_time": "17:00:00",
                    "room_name": "P101",
                }
            ],
            confidence=0.9,
        )

    def search_knowledge(self, entities: dict) -> ToolResult:
        return ToolResult(
            tool_name="clinic.search_knowledge",
            source="fake.knowledge_articles",
            rows=[
                {
                    "title_vi": "Quy trình khám",
                    "content_vi": "Bệnh nhân đến quầy tiếp nhận, xác nhận thông tin, thanh toán và vào phòng khám.",
                }
            ],
            confidence=0.88,
        )

    def lookup_private_data(self, entities: dict, auth: AuthContext) -> ToolResult:
        return ToolResult(
            tool_name="clinic.lookup_private_data",
            source="fake.appointments",
            rows=[
                {
                    "appointment_date": "2026-04-24",
                    "start_time": "08:00:00",
                    "patient_name": "Nguyễn Văn A",
                    "doctor_name": "SUON SAVUTH",
                    "service_name": "Khám tổng quát",
                    "status": "scheduled",
                }
            ]
            if auth.patient_id == "patient-1"
            else [],
            confidence=0.8 if auth.patient_id == "patient-1" else 0.0,
        )

    def lookup_lab_results(self, entities: dict, auth: AuthContext) -> ToolResult:
        return ToolResult(
            tool_name="clinic.lookup_lab_results",
            source="fake.paraclinical_orders",
            rows=[
                {
                    "service_code": "CBC",
                    "service_name": "CBC",
                    "status": "collected",
                    "has_result": False,
                }
            ]
            if auth.patient_id == "patient-1"
            else [],
            confidence=0.8 if auth.patient_id == "patient-1" else 0.0,
        )

    def create_request(self, entities: dict) -> ToolResult:
        return ToolResult(
            tool_name="clinic.create_appointment_request",
            source="fake.appointment_requests",
            message="Appointment booking is not enabled yet.",
            confidence=0.8,
        )


def build_orchestrator() -> Orchestrator:
    orchestrator = Orchestrator(adapters={"clinic": FakeClinicAdapter()})
    orchestrator.llm_client.settings = Settings(llm_provider="none")
    orchestrator.grounded_response_generator = StaticGroundedResponseGenerator()
    return orchestrator


class StaticLLMClient:
    def __init__(self, intent: Intent) -> None:
        self.intent = intent

    def parse_intent(self, question: str, domain: str) -> Intent:
        return self.intent


class StaticGroundedResponseGenerator:
    def __init__(self, answer: str | None = None) -> None:
        self.answer = answer

    def generate(
        self,
        question: str,
        intent: Intent,
        result: ToolResult,
        auth: AuthContext | None = None,
    ) -> str | None:
        return self.answer


def test_orchestrator_greeting():
    response = build_orchestrator().handle(AskRequest(question="xin chào"))

    assert response.intent == "greeting"
    assert response.parser_source == "rule"
    assert response.requires_auth is False
    assert "robot lễ tân" in response.answer


def test_orchestrator_service_price():
    response = build_orchestrator().handle(
        AskRequest(question="CT Brain without contrast giá bao nhiêu?")
    )

    assert response.intent == "service_price"
    assert response.sources == ["fake.services"]
    assert "120000" in response.answer


def test_orchestrator_normalizes_llm_general_info_data_source():
    orchestrator = build_orchestrator()
    orchestrator.llm_client = StaticLLMClient(
        Intent(
            domain="clinic",
            intent="general_info",
            entities={},
            confidence=0.8,
            data_source="none",
        )
    )

    response = orchestrator.handle(AskRequest(question="Địa chỉ phòng khám ở đâu?"))

    assert response.intent == "general_info"
    assert response.parser_source == "llm"
    assert response.sources == ["fake.clinics"]
    assert "Demo Clinic" in response.answer


def test_orchestrator_normalizes_llm_service_price_data_source():
    orchestrator = build_orchestrator()
    orchestrator.llm_client = StaticLLMClient(
        Intent(
            domain="clinic",
            intent="service_price",
            entities={},
            confidence=0.8,
            data_source="none",
        )
    )

    response = orchestrator.handle(AskRequest(question="CT Brain without contrast giá bao nhiêu?"))

    assert response.intent == "service_price"
    assert response.parser_source == "llm"
    assert response.sources == ["fake.services"]
    assert "120000" in response.answer


def test_orchestrator_prefers_rule_for_service_category_detail_when_llm_is_broad():
    orchestrator = build_orchestrator()
    orchestrator.llm_client = StaticLLMClient(
        Intent(
            domain="clinic",
            intent="service_category_list",
            entities={"service_type": "imaging"},
            confidence=0.8,
            data_source="sql",
        )
    )

    response = orchestrator.handle(AskRequest(question="xem chi tiết nhóm CT Scan"))

    assert response.intent == "service_category_detail"
    assert response.parser_source == "llm"
    assert response.sources == ["fake.services"]
    assert "CT001" in response.answer


def test_orchestrator_prefers_lab_service_type_when_llm_uses_all():
    orchestrator = build_orchestrator()
    orchestrator.llm_client = StaticLLMClient(
        Intent(
            domain="clinic",
            intent="service_category_list",
            entities={"service_type": "all"},
            confidence=0.8,
            data_source="sql",
        )
    )

    response = orchestrator.handle(AskRequest(question="có các loại xét nghiệm nào"))

    assert response.intent == "service_category_list"
    assert response.parser_source == "llm"
    assert response.sources == ["fake.services"]
    assert "Check Liver Function" in response.answer


def test_orchestrator_prefers_empty_profile_query_for_generic_general_info():
    orchestrator = build_orchestrator()
    orchestrator.llm_client = StaticLLMClient(
        Intent(
            domain="clinic",
            intent="general_info",
            entities={"profile_query": "Địa chỉ phòng khám ở đâu"},
            confidence=0.8,
            data_source="sql",
        )
    )

    response = orchestrator.handle(AskRequest(question="Địa chỉ phòng khám ở đâu?"))

    assert response.intent == "general_info"
    assert response.parser_source == "llm"
    assert response.sources == ["fake.clinics"]
    assert "Demo Clinic" in response.answer


def test_orchestrator_prefers_service_catalog_summary_for_current_services():
    orchestrator = build_orchestrator()
    orchestrator.llm_client = StaticLLMClient(
        Intent(
            domain="clinic",
            intent="service_category_list",
            entities={"service_type": "all"},
            confidence=0.8,
            data_source="sql",
        )
    )

    response = orchestrator.handle(AskRequest(question="các dịch vụ hiện có"))

    assert response.intent == "service_catalog_summary"
    assert response.parser_source == "llm"
    assert response.sources == ["fake.services"]
    assert "20 dịch vụ" in response.answer


def test_orchestrator_guest_personal_data_is_blocked_by_policy():
    response = build_orchestrator().handle(AskRequest(question="Tôi có lịch hẹn nào không?"))

    assert response.intent == "personal_data"
    assert response.requires_auth is True
    assert response.sources == ["policy"]
    assert "xác thực" in response.answer


def test_orchestrator_authenticated_patient_reaches_auth_branch():
    response = build_orchestrator().handle(
        AskRequest(
            question="Tôi có lịch hẹn nào không?",
            auth=AuthContext(role="patient", patient_id="patient-1"),
        )
    )

    assert response.intent == "personal_data"
    assert response.requires_auth is True
    assert response.sources == ["fake.appointments"]
    assert "2026-04-24" in response.answer
    assert "SUON SAVUTH" in response.answer


def test_orchestrator_authenticated_patient_uses_formatted_answer_when_available():
    orchestrator = build_orchestrator()
    orchestrator.grounded_response_generator = StaticGroundedResponseGenerator(
        "Bạn có lịch hẹn ngày 2026-04-24 lúc 08:00 với bác sĩ SUON SAVUTH."
    )

    response = orchestrator.handle(
        AskRequest(
            question="Tôi có lịch hẹn nào không?",
            auth=AuthContext(role="patient", patient_id="patient-1"),
        )
    )

    assert response.intent == "personal_data"
    assert response.answer_source == "llm_formatted"
    assert response.answer == "Bạn có lịch hẹn ngày 2026-04-24 lúc 08:00 với bác sĩ SUON SAVUTH."


def test_orchestrator_knowledge_search():
    response = build_orchestrator().handle(AskRequest(question="Quy trình khám như thế nào?"))

    assert response.intent == "knowledge_search"
    assert response.answer_source == "template"
    assert response.sources == ["fake.knowledge_articles"]
    assert "Quy trình khám" in response.answer


def test_orchestrator_knowledge_search_uses_grounded_answer_when_available():
    orchestrator = build_orchestrator()
    orchestrator.grounded_response_generator = StaticGroundedResponseGenerator(
        "Bệnh nhân đến quầy tiếp nhận, xác nhận thông tin rồi vào phòng khám."
    )

    response = orchestrator.handle(AskRequest(question="Quy trình khám như thế nào?"))

    assert response.intent == "knowledge_search"
    assert response.answer_source == "llm_grounded"
    assert response.answer == "Bệnh nhân đến quầy tiếp nhận, xác nhận thông tin rồi vào phòng khám."


def test_orchestrator_appointment_booking_placeholder():
    response = build_orchestrator().handle(AskRequest(question="đặt lịch"))

    assert response.intent == "appointment_booking"
    assert response.sources == ["fake.appointment_requests"]
    assert "chưa được bật" in response.answer

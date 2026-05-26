from app.rag.grounded_response_generator import GroundedResponseGenerator
from app.core.schemas import AuthContext, Intent, ToolResult


class StaticLLMClient:
    def __init__(self, answer: str) -> None:
        self.answer = answer

    def generate_formatted_answer(self, **kwargs) -> str:
        return self.answer

    def generate_grounded_answer(self, **kwargs) -> None:
        return None


def test_appointment_context_marks_missing_doctor_as_missing_data():
    generator = GroundedResponseGenerator()
    result = ToolResult(
        tool_name="clinic.lookup_private_data",
        source="fake.appointments",
        rows=[
            {
                "id": "appointment-1",
                "appointment_date": "2026-04-24",
                "start_time": "08:00:00",
                "patient_name": "Trần Thị Bình",
                "doctor_name": None,
                "visit_type": "walk_in",
                "status": "scheduled",
            }
        ],
    )

    context = generator._build_context(result, AuthContext(role="patient"))

    assert "role: patient" in context
    assert "patient_name: Trần Thị Bình" in context
    assert "doctor_name: không có dữ liệu" in context
    assert "không được dùng patient_name làm tên bác sĩ" in context


def test_appointment_formatter_rejects_patient_name_as_doctor_name():
    generator = GroundedResponseGenerator()

    assert (
        generator._has_appointment_role_confusion(
            "Bạn có lịch hẹn với bác sĩ Trần Thị Bình lúc 08:00.",
            [
                {
                    "appointment_date": "2026-04-24",
                    "patient_name": "Trần Thị Bình",
                    "doctor_name": None,
                }
            ],
        )
        is True
    )


def test_appointment_formatter_allows_real_doctor_name():
    generator = GroundedResponseGenerator()

    assert (
        generator._has_appointment_role_confusion(
            "Bạn có lịch hẹn với bác sĩ SUON SAVUTH lúc 08:00.",
            [
                {
                    "appointment_date": "2026-04-24",
                    "patient_name": "Trần Thị Bình",
                    "doctor_name": "SUON SAVUTH",
                }
            ],
        )
        is False
    )


def test_doctor_context_uses_patient_schedule_perspective():
    generator = GroundedResponseGenerator()
    result = ToolResult(
        tool_name="clinic.lookup_private_data",
        source="fake.appointments",
        rows=[
            {
                "id": "appointment-1",
                "appointment_date": "2026-04-24",
                "start_time": "08:00:00",
                "patient_name": "Trần Thị Bình",
                "doctor_name": None,
                "visit_type": "walk_in",
                "status": "scheduled",
            }
        ],
    )

    context = generator._build_context(result, AuthContext(role="doctor"))

    assert "role: doctor" in context
    assert "Người đang hỏi là bác sĩ" in context
    assert "không viết 'với bác sĩ <patient_name>'" in context


def test_doctor_formatter_rejects_patient_name_as_doctor_name():
    generator = GroundedResponseGenerator()

    assert (
        generator._has_appointment_role_confusion(
            "Bạn có lịch với bác sĩ Trần Thị Bình lúc 08:00.",
            [
                {
                    "appointment_date": "2026-04-24",
                    "patient_name": "Trần Thị Bình",
                    "doctor_name": None,
                }
            ],
            AuthContext(role="doctor"),
        )
        is True
    )


def test_formatter_rejects_no_appointments_answer_when_rows_exist():
    generator = GroundedResponseGenerator()
    result = ToolResult(
        tool_name="clinic.lookup_private_data",
        source="fake.appointments",
        rows=[
            {
                "appointment_date": "2026-04-24",
                "start_time": "08:00:00",
                "patient_name": "Chea Reaksmey",
                "doctor_name": None,
            }
        ],
    )

    assert generator._contradicts_non_empty_result("Bạn chưa có lịch hẹn nào.", result) is True


def test_formatter_allows_no_appointments_answer_when_rows_are_empty():
    generator = GroundedResponseGenerator()
    result = ToolResult(
        tool_name="clinic.lookup_private_data",
        source="fake.appointments",
        rows=[],
    )

    assert generator._contradicts_non_empty_result("Bạn chưa có lịch hẹn nào.", result) is False


def test_service_context_preserves_service_names():
    generator = GroundedResponseGenerator()
    result = ToolResult(
        tool_name="clinic.search_services",
        source="robo_app.services",
        rows=[
            {
                "code": "CT001",
                "name": "CT Brain without contrast",
                "category_name": "CT Scan",
                "price_amount": 120000,
                "currency_code": "USD",
            }
        ],
    )

    context = generator._build_context(result, AuthContext(role="guest"))

    assert "Giữ nguyên văn name, code, category_name và currency_code" in context
    assert "name: CT Brain without contrast" in context


def test_service_formatter_rejects_translated_service_name():
    generator = GroundedResponseGenerator()
    generator.llm_client = StaticLLMClient("CT não không contrast có giá 120.000 USD.")
    intent = Intent(
        intent="service_price",
        entities={"service_query": "CT Brain without contrast giá bao nhiêu?"},
        data_source="sql",
    )
    result = ToolResult(
        tool_name="clinic.search_services",
        source="robo_app.services",
        rows=[
            {
                "code": "CT001",
                "name": "CT Brain without contrast",
                "category_name": "CT Scan",
                "price_amount": 120000,
                "currency_code": "USD",
            }
        ],
    )

    assert generator.generate("CT Brain without contrast giá bao nhiêu?", intent, result) is None


def test_service_formatter_allows_exact_service_name():
    generator = GroundedResponseGenerator()
    generator.llm_client = StaticLLMClient("CT Brain without contrast có giá 120.000 USD.")
    intent = Intent(
        intent="service_price",
        entities={"service_query": "CT Brain without contrast giá bao nhiêu?"},
        data_source="sql",
    )
    result = ToolResult(
        tool_name="clinic.search_services",
        source="robo_app.services",
        rows=[
            {
                "code": "CT001",
                "name": "CT Brain without contrast",
                "category_name": "CT Scan",
                "price_amount": 120000,
                "currency_code": "USD",
            }
        ],
    )

    assert (
        generator.generate("CT Brain without contrast giá bao nhiêu?", intent, result)
        == "CT Brain without contrast có giá 120.000 USD."
    )


def test_service_formatter_rejects_answer_that_drops_service_rows():
    generator = GroundedResponseGenerator()
    generator.llm_client = StaticLLMClient("MRI Abdomen with contrast có giá 380000 USD.")
    intent = Intent(
        intent="service_price",
        entities={"service_query": "ct"},
        data_source="sql",
    )
    result = ToolResult(
        tool_name="clinic.search_services",
        source="robo_app.services",
        rows=[
            {
                "code": "CT001",
                "name": "CT Brain without contrast",
                "category_name": "CT Scan",
                "price_amount": 120000,
                "currency_code": "USD",
            },
            {
                "code": "CT002",
                "name": "CT Brain with contrast",
                "category_name": "CT Scan",
                "price_amount": 180000,
                "currency_code": "USD",
            },
        ],
    )

    assert generator.generate("tôi muốn chụp ct", intent, result) is None


def test_general_info_formatter_rejects_answer_that_drops_clinic_rows():
    generator = GroundedResponseGenerator()
    generator.llm_client = StaticLLMClient(
        "Địa chỉ phòng khám là No.55, St,566, Boeung Kok, Toul Kork, PNP, Phnom Penh."
    )
    intent = Intent(
        intent="general_info",
        entities={"profile_query": ""},
        data_source="sql",
    )
    result = ToolResult(
        tool_name="clinic.get_public_profile",
        source="robo_app.clinics, robo_app.clinic_settings",
        rows=[
            {
                "name": "BIOMEDIC DIAGNOSTIC CENTER",
                "address": "No.55, St,566, Boeung Kok, Toul Kork, PNP",
                "city": "Phnom Penh",
            },
            {
                "name": "Phòng Khám Đa Khoa Mẫu",
                "address": "123 Nguyễn Huệ, Q1",
                "city": "Hồ Chí Minh",
            },
        ],
    )

    assert generator.generate("Địa chỉ phòng khám ở đâu?", intent, result) is None


def test_general_info_formatter_allows_answer_with_all_clinic_rows():
    answer = (
        "Tôi tìm thấy các cơ sở đang hoạt động: "
        "BIOMEDIC DIAGNOSTIC CENTER ở No.55; "
        "Phòng Khám Đa Khoa Mẫu ở 123 Nguyễn Huệ, Q1."
    )
    generator = GroundedResponseGenerator()
    generator.llm_client = StaticLLMClient(answer)
    intent = Intent(
        intent="general_info",
        entities={"profile_query": ""},
        data_source="sql",
    )
    result = ToolResult(
        tool_name="clinic.get_public_profile",
        source="robo_app.clinics, robo_app.clinic_settings",
        rows=[
            {
                "name": "BIOMEDIC DIAGNOSTIC CENTER",
                "address": "No.55, St,566, Boeung Kok, Toul Kork, PNP",
                "city": "Phnom Penh",
            },
            {
                "name": "Phòng Khám Đa Khoa Mẫu",
                "address": "123 Nguyễn Huệ, Q1",
                "city": "Hồ Chí Minh",
            },
        ],
    )

    assert generator.generate("Địa chỉ phòng khám ở đâu?", intent, result) == answer


def test_medical_advice_uses_template_instead_of_llm_formatter():
    generator = GroundedResponseGenerator()
    generator.llm_client = StaticLLMClient("Tôi không tìm thấy dữ liệu phù hợp.")
    intent = Intent(
        intent="medical_advice",
        entities={},
        data_source="none",
    )
    result = ToolResult(
        tool_name="clinic.medical_advice",
        source="none",
        message="Robot không thể tư vấn chọn xét nghiệm.",
        rows=[{"message": "Robot không thể tư vấn chọn xét nghiệm."}],
    )

    assert generator.generate("nên sử dụng loại nào?", intent, result) is None


def test_knowledge_context_uses_only_relevant_content_fields():
    generator = GroundedResponseGenerator()
    result = ToolResult(
        tool_name="clinic.search_knowledge",
        source="scripts/rag_documents.py",
        rows=[
            {
                "source_table": "admin_help_templates",
                "source_id": "article-1",
                "title": "Reception",
                "title_vi": "Tiếp nhận & Check-in",
                "content": "English content should not be preferred.",
                "content_vi": "## Tiếp nhận\n1. Tìm bệnh nhân.\n2. Xác nhận lịch hẹn.",
                "_score": 0.91,
            }
        ],
    )

    context = generator._build_knowledge_context(result)

    assert "Tiếp nhận & Check-in" in context
    assert "Tìm bệnh nhân" in context
    assert "source_table" not in context
    assert "English content should not be preferred" not in context

from app.core.response_generator import ResponseGenerator
from app.core.schemas import Intent, ToolResult


def test_doctor_schedule_lists_available_rows_without_hidden_count():
    intent = Intent(intent="doctor_schedule", data_source="sql")
    result = ToolResult(
        tool_name="clinic.search_doctor_schedules",
        source="fake.doctor_schedules",
        rows=[
            {
                "doctor_name": "Dr. Nguyen Van A",
                "day_of_week": 5,
                "start_time": "08:00:00",
                "end_time": "17:00:00",
                "room_name": None,
            },
            {
                "doctor_name": "LEANG THY",
                "day_of_week": 5,
                "start_time": "00:00:00",
                "end_time": "12:00:00",
                "room_name": "Phòng khám ngoại 1",
            },
            {
                "doctor_name": "SUON SAVUTH",
                "day_of_week": 5,
                "start_time": "08:00:00",
                "end_time": "12:00:00",
                "room_name": "P101",
            },
            {
                "doctor_name": "Nuth Sodara",
                "day_of_week": 5,
                "start_time": "13:00:00",
                "end_time": "17:00:00",
                "room_name": "P102",
            },
        ],
    )

    answer = ResponseGenerator().generate("Hôm nay bác sĩ có khám không?", intent, result)

    assert "và còn" not in answer
    assert "Dr. Nguyen Van A" in answer
    assert "Nuth Sodara" in answer
    assert "1. " in answer
    assert "4. " in answer


def test_service_catalog_summary_answers_with_group_totals():
    intent = Intent(intent="service_catalog_summary", data_source="sql")
    result = ToolResult(
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
    )

    answer = ResponseGenerator().generate("phòng khám có những dịch vụ nào?", intent, result)

    assert "20 dịch vụ" in answer
    assert "2 nhóm" in answer
    assert "Blood test" in answer
    assert "CT Scan" in answer
    assert "Bạn muốn xem chi tiết nhóm nào?" in answer


def test_service_catalog_summary_can_continue_remaining_groups():
    intent = Intent(intent="service_catalog_summary", data_source="sql")
    result = ToolResult(
        tool_name="clinic.summarize_service_catalog",
        source="fake.services",
        rows=[
            {
                "service_type": "lab",
                "category_name": "Group 11",
                "service_count": 5,
                "min_price": 1.0,
                "max_price": 2.0,
                "currency_code": "USD",
                "total_services": 50,
                "total_categories": 12,
                "category_offset": 10,
                "display_limit": 10,
                "category_display_index": 11,
            },
            {
                "service_type": "imaging",
                "category_name": "Group 12",
                "service_count": 4,
                "min_price": 3.0,
                "max_price": 4.0,
                "currency_code": "USD",
                "total_services": 50,
                "total_categories": 12,
                "category_offset": 10,
                "display_limit": 10,
                "category_display_index": 12,
            },
        ],
    )

    answer = ResponseGenerator().generate("xem thêm", intent, result)

    assert answer.startswith("Các nhóm dịch vụ còn lại phù hợp:")
    assert "11. Group 11" in answer
    assert "12. Group 12" in answer
    assert "Còn" not in answer


def test_service_category_list_can_continue_remaining_groups():
    intent = Intent(intent="service_category_list", data_source="sql")
    result = ToolResult(
        tool_name="clinic.list_service_categories",
        source="fake.services",
        rows=[
            {
                "service_type": "lab",
                "category_name": "General Health Check Up",
                "service_count": 17,
                "min_price": 1.0,
                "max_price": 7.0,
                "currency_code": "USD",
                "total_categories": 14,
                "category_offset": 12,
                "display_limit": 24,
            },
            {
                "service_type": "lab",
                "category_name": "Laboratories",
                "service_count": 504,
                "min_price": 1.0,
                "max_price": 500.0,
                "currency_code": "USD",
                "total_categories": 14,
                "category_offset": 12,
                "display_limit": 24,
            },
        ],
    )

    answer = ResponseGenerator().generate("24 nhóm khác là nhóm nào", intent, result)

    assert answer.startswith("Các nhóm dịch vụ còn lại phù hợp:")
    assert "13. General Health Check Up" in answer
    assert "14. Laboratories" in answer
    assert "Còn" not in answer


def test_service_category_detail_lists_services_in_group():
    intent = Intent(intent="service_category_detail", data_source="sql")
    result = ToolResult(
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
                "total_services_in_category": 2,
                "matched_category_name": "CT Scan",
            },
        ],
    )

    answer = ResponseGenerator().generate("xem chi tiết nhóm CT Scan", intent, result)

    assert "Nhóm CT Scan có 2 dịch vụ" in answer
    assert "CT001 - CT Brain without contrast" in answer
    assert "CT002 - CT Brain with contrast" in answer


def test_service_package_detail_lists_package_items():
    intent = Intent(intent="service_package_detail", data_source="sql")
    result = ToolResult(
        tool_name="clinic.lookup_service_package_detail",
        source="fake.service_packages",
        rows=[
            {
                "package_code": "PKG-0001",
                "package_name": "General Health Check Up",
                "package_price_amount": 0,
                "currency_code": "USD",
                "service_code": "GHC001",
                "service_name": "CBC",
                "service_category_name": "General Health Check Up",
                "quantity": 1,
                "service_price_amount": 2.0,
                "service_currency_code": "USD",
                "total_items_in_package": 2,
            },
            {
                "package_code": "PKG-0001",
                "package_name": "General Health Check Up",
                "package_price_amount": 0,
                "currency_code": "USD",
                "service_code": "GHC002",
                "service_name": "Glucose",
                "service_category_name": "General Health Check Up",
                "quantity": 1,
                "service_price_amount": 1.0,
                "service_currency_code": "USD",
                "total_items_in_package": 2,
            },
        ],
    )

    answer = ResponseGenerator().generate("gói khám General Health Check Up gồm gì?", intent, result)

    assert "PKG-0001 - General Health Check Up có 2 dịch vụ" in answer
    assert "GHC001 - CBC" in answer
    assert "GHC002 - Glucose" in answer


def test_lab_indicator_detail_lists_indicator_metadata():
    intent = Intent(intent="lab_indicator_detail", data_source="sql")
    result = ToolResult(
        tool_name="clinic.lookup_lab_indicator_detail",
        source="fake.service_lab_indicators",
        rows=[
            {
                "service_id": "svc-cbc",
                "service_code": "GHC001",
                "service_name": "CBC",
                "code": "WBC",
                "name": "Bạch cầu",
                "unit": "x10^9/L",
                "reference_range_text": "4.0 - 10.0",
                "specimen_type": "Whole Blood (EDTA)",
                "method": "Automated Hematology Analyzer",
                "total_indicators": 1,
            }
        ],
    )

    answer = ResponseGenerator().generate("CBC gồm những chỉ số nào?", intent, result)

    assert "Dịch vụ CBC có 1 chỉ số xét nghiệm" in answer
    assert "WBC - Bạch cầu" in answer
    assert "x10^9/L" in answer
    assert "4.0 - 10.0" in answer


def test_partner_lab_request_lookup_lists_request_and_onsite_rows():
    intent = Intent(intent="partner_lab_request_lookup", data_source="auth", requires_auth=True)
    result = ToolResult(
        tool_name="clinic.lookup_partner_lab_requests",
        source="fake.partner_lab_requests",
        rows=[
            {
                "record_type": "partner_lab_request",
                "accession_number": "PLR-PROD-0003",
                "patient_name": "Trần Thị Bình",
                "status": "sample_collected",
                "sample_type": "Máu",
                "collection_method": "onsite_collection",
                "requested_at": "2026-06-12 15:00:00+07",
                "sample_collected_at": "2026-06-12 16:15:00+07",
            },
            {
                "record_type": "partner_onsite_collection",
                "accession_number": "PLR-PROD-0003",
                "patient_name": "Trần Thị Bình",
                "onsite_status": "collected",
                "preferred_date": "2026-06-12",
                "collection_address": "123 Demo Street",
                "collected_at": "2026-06-12 16:15:00+07",
                "returned_to_lab_at": "2026-06-12 16:45:00+07",
            },
        ],
    )

    answer = ResponseGenerator().generate("Mẫu xét nghiệm của tôi đã lấy chưa?", intent, result)

    assert "PLR-PROD-0003" in answer
    assert "sample_collected" in answer
    assert "Lấy mẫu tận nơi" in answer
    assert "đã chuyển về lab" in answer


def test_knowledge_search_template_formats_markdown_as_readable_lines():
    intent = Intent(intent="knowledge_search", data_source="rag")
    result = ToolResult(
        tool_name="clinic.search_knowledge",
        source="fake.knowledge",
        rows=[
            {
                "title_vi": "Tiếp nhận & Check-in",
                "content_vi": "## Tiếp nhận & Check-in\n\n### Check-in bệnh nhân\n1. Tìm bệnh nhân.\n2. Xác nhận lịch hẹn.\n- Bệnh nhân vào hàng đợi.",
            }
        ],
    )

    answer = ResponseGenerator().generate("Quy trình check-in bệnh nhân như thế nào?", intent, result)

    assert "##" not in answer
    assert "**" not in answer
    assert "Tiếp nhận & Check-in:" in answer
    assert "1. Tìm bệnh nhân." in answer
    assert "Bệnh nhân vào hàng đợi." in answer


def test_knowledge_search_template_formats_patient_question_templates_as_suggestions():
    intent = Intent(intent="knowledge_search", data_source="rag")
    result = ToolResult(
        tool_name="clinic.search_knowledge",
        source="qdrant:clinic_knowledge",
        rows=[
            {
                "document_type": "patient_question_template",
                "title_vi": "Tôi nên uống thuốc này như thế nào?",
                "topic": "medication",
                "content_vi": "Mẫu câu hỏi gợi ý cho bệnh nhân. Chủ đề: thuốc.",
            },
            {
                "document_type": "patient_question_template",
                "title_vi": "Tôi có thể uống thuốc này cùng với các thuốc khác không?",
                "topic": "medication",
                "content_vi": "Mẫu câu hỏi gợi ý cho bệnh nhân. Chủ đề: thuốc.",
            },
            {
                "document_type": "patient_question_template",
                "title_vi": "Kết quả xét nghiệm của tôi có ý nghĩa gì?",
                "topic": "test_results",
                "content_vi": "Mẫu câu hỏi gợi ý cho bệnh nhân. Chủ đề: kết quả xét nghiệm.",
            },
        ],
    )

    answer = ResponseGenerator().generate("Tôi nên hỏi bác sĩ câu gì về thuốc?", intent, result)

    assert "Bạn có thể tham khảo các câu hỏi sau" in answer
    assert "1. Tôi nên uống thuốc này như thế nào?" in answer
    assert "2. Tôi có thể uống thuốc này cùng với các thuốc khác không?" in answer
    assert "Kết quả xét nghiệm" not in answer


def test_medical_advice_mentions_symptom_without_recommending_specific_test():
    intent = Intent(intent="medical_advice", data_source="none")
    result = ToolResult(tool_name="none", source="none")

    answer = ResponseGenerator().generate("tôi đau bụng nên khám gì?", intent, result)

    assert "đau bụng" in answer
    assert "chẩn đoán" in answer
    assert "cấp cứu" in answer
    assert "xét nghiệm hoặc sử dụng dịch vụ nào" not in answer


def test_medical_advice_keeps_multiple_symptoms_from_question():
    intent = Intent(intent="medical_advice", data_source="none")
    result = ToolResult(tool_name="none", source="none")

    answer = ResponseGenerator().generate("tôi đau đầu đau mắt thì sao?", intent, result)

    assert "đau đầu đau mắt" in answer
    assert "chẩn đoán" in answer


def test_medical_advice_strips_trailing_symptom_punctuation():
    intent = Intent(intent="medical_advice", data_source="none")
    result = ToolResult(tool_name="none", source="none")

    answer = ResponseGenerator().generate("tôi đau ngực, nên khám gì", intent, result)

    assert "đau ngực." in answer
    assert "đau ngực,." not in answer

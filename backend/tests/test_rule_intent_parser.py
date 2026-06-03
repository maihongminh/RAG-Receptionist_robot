from app.core.rule_intent_parser import RuleIntentParser


def test_greeting_intent():
    intent = RuleIntentParser().parse("xin chào", "clinic")

    assert intent.intent == "greeting"
    assert intent.data_source == "none"
    assert intent.requires_auth is False


def test_service_price_intent_does_not_match_hi_inside_vietnamese_word():
    intent = RuleIntentParser().parse("CT Brain without contrast giá bao nhiêu?", "clinic")

    assert intent.intent == "service_price"
    assert intent.entities["service_query"] == "CT Brain without contrast"
    assert intent.data_source == "sql"


def test_service_price_cleans_generic_ct_request():
    intent = RuleIntentParser().parse("tôi muốn chụp ct", "clinic")

    assert intent.intent == "service_price"
    assert intent.entities["service_query"] == "ct"


def test_service_price_cleans_lab_test_name():
    intent = RuleIntentParser().parse("xét nghiệm TIBC có giá bao nhiêu", "clinic")

    assert intent.intent == "service_price"
    assert intent.entities["service_query"] == "TIBC"


def test_lab_result_lookup_requires_auth():
    intent = RuleIntentParser().parse("tôi muốn nhận kết quả xét nghiệm", "clinic")

    assert intent.intent == "lab_result_lookup"
    assert intent.requires_auth is True
    assert intent.data_source == "auth"


def test_result_process_stays_knowledge_search():
    intent = RuleIntentParser().parse("Quy trình nhận kết quả xét nghiệm như thế nào?", "clinic")

    assert intent.intent == "knowledge_search"
    assert intent.data_source == "rag"


def test_lab_category_list_intent():
    intent = RuleIntentParser().parse("tôi muốn xét nghiệm, có các loại xét nghiệm nào", "clinic")

    assert intent.intent == "service_category_list"
    assert intent.entities["service_type"] == "lab"


def test_lab_category_list_from_short_question():
    intent = RuleIntentParser().parse("danh sách xét nghiệm", "clinic")

    assert intent.intent == "service_category_list"
    assert intent.entities["service_type"] == "lab"


def test_service_category_remaining_followup_intent():
    intent = RuleIntentParser().parse("24 nhóm khác là nhóm nào", "clinic")

    assert intent.intent == "service_category_list"
    assert intent.data_source == "sql"
    assert intent.entities["service_type"] == "lab"
    assert intent.entities["offset"] == 12
    assert intent.entities["display_limit"] == 24


def test_service_catalog_summary_intent():
    intent = RuleIntentParser().parse("phòng khám có những dịch vụ nào?", "clinic")

    assert intent.intent == "service_catalog_summary"
    assert intent.data_source == "sql"
    assert intent.entities["service_type"] == "all"


def test_service_catalog_summary_current_services_intent():
    intent = RuleIntentParser().parse("các dịch vụ hiện có", "clinic")

    assert intent.intent == "service_catalog_summary"
    assert intent.data_source == "sql"
    assert intent.entities["service_type"] == "all"


def test_service_category_detail_intent():
    intent = RuleIntentParser().parse("xem chi tiết nhóm CT Scan", "clinic")

    assert intent.intent == "service_category_detail"
    assert intent.data_source == "sql"
    assert intent.entities["category_query"] == "CT Scan"
    assert intent.entities["service_type"] == "imaging"


def test_service_category_detail_does_not_treat_insects_as_ct_imaging():
    intent = RuleIntentParser().parse("xem chi tiết nhóm check for insects in the blood", "clinic")

    assert intent.intent == "service_category_detail"
    assert intent.entities["category_query"] == "check for insects in the blood"
    assert intent.entities["service_type"] == "all"


def test_numeric_service_category_detail_defaults_to_lab_without_session_context():
    intent = RuleIntentParser().parse("xem chi tiết nhóm 35", "clinic")

    assert intent.intent == "service_category_detail"
    assert intent.entities["category_query"] == "35"
    assert intent.entities["service_type"] == "lab"


def test_medical_advice_intent():
    intent = RuleIntentParser().parse("nên sử dụng loại nào?", "clinic")

    assert intent.intent == "medical_advice"
    assert intent.data_source == "none"


def test_symptom_triage_question_is_medical_advice():
    intent = RuleIntentParser().parse("tôi đau bụng nên khám gì?", "clinic")

    assert intent.intent == "medical_advice"
    assert intent.data_source == "none"


def test_symptom_triage_question_is_not_hardcoded_to_one_symptom():
    intent = RuleIntentParser().parse("tôi đau đầu đau mắt thì sao?", "clinic")

    assert intent.intent == "medical_advice"
    assert intent.data_source == "none"


def test_doctor_schedule_today_extracts_doctor_query_and_weekday():
    intent = RuleIntentParser().parse("Hôm nay bác sĩ SUON SAVUTH có khám không?", "clinic")

    assert intent.intent == "doctor_schedule"
    assert intent.entities["doctor_query"] == "SUON SAVUTH"
    assert intent.entities["date"] == "today"
    assert isinstance(intent.entities["weekday"], int)


def test_personal_data_requires_auth():
    intent = RuleIntentParser().parse("Tôi có lịch hẹn nào không?", "clinic")

    assert intent.intent == "personal_data"
    assert intent.requires_auth is True
    assert intent.data_source == "auth"


def test_patient_profile_summary_requires_auth():
    intent = RuleIntentParser().parse("Thông tin hồ sơ của tôi là gì?", "clinic")

    assert intent.intent == "patient_profile_summary"
    assert intent.requires_auth is True
    assert intent.data_source == "auth"


def test_patient_timeline_summary_requires_auth():
    intent = RuleIntentParser().parse("Tóm tắt lịch sử khám của tôi", "clinic")

    assert intent.intent == "patient_timeline_summary"
    assert intent.requires_auth is True
    assert intent.data_source == "auth"


def test_visit_summary_lookup_requires_auth():
    intent = RuleIntentParser().parse("Tóm tắt lần khám gần đây của tôi", "clinic")

    assert intent.intent == "visit_summary_lookup"
    assert intent.requires_auth is True
    assert intent.data_source == "auth"


def test_billing_summary_lookup_requires_auth():
    intent = RuleIntentParser().parse("Tôi đã thanh toán chưa?", "clinic")

    assert intent.intent == "billing_summary_lookup"
    assert intent.requires_auth is True
    assert intent.data_source == "auth"


def test_general_info_intent():
    intent = RuleIntentParser().parse("Địa chỉ phòng khám ở đâu?", "clinic")

    assert intent.intent == "general_info"
    assert intent.data_source == "sql"
    assert intent.entities["profile_query"] == ""


def test_general_info_opening_hours_keeps_generic_profile_query_empty():
    intent = RuleIntentParser().parse("Phòng khám mở cửa lúc mấy giờ", "clinic")

    assert intent.intent == "general_info"
    assert intent.data_source == "sql"
    assert intent.entities["profile_query"] == ""


def test_general_info_extracts_specific_clinic_query():
    intent = RuleIntentParser().parse("Địa chỉ Phòng Khám Đa Khoa Mẫu ở đâu?", "clinic")

    assert intent.intent == "general_info"
    assert intent.entities["profile_query"] == "Đa Khoa Mẫu"


def test_knowledge_search_intent():
    intent = RuleIntentParser().parse("Quy trình khám như thế nào?", "clinic")

    assert intent.intent == "knowledge_search"
    assert intent.data_source == "rag"
    assert intent.entities["knowledge_query"] == "Quy trình khám như thế nào?"


def test_appointment_booking_intent():
    intent = RuleIntentParser().parse("đặt lịch", "clinic")

    assert intent.intent == "appointment_booking"
    assert intent.data_source == "none"
    assert intent.entities["booking_query"] == "đặt lịch"

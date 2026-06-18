import re
from datetime import date

from app.core.schemas import Intent


SERVICE_KEYWORDS = ("giá", "bao nhiêu", "cost", "price", "dịch vụ", "xét nghiệm", "chụp", "chụp phim")
SERVICE_CATEGORY_KEYWORDS = (
    "danh sách xét nghiệm",
    "các loại xét nghiệm",
    "loại xét nghiệm",
    "nhóm xét nghiệm",
    "các nhóm xét nghiệm",
    "có loại xét nghiệm nào",
    "có các loại xét nghiệm nào",
    "có những loại xét nghiệm nào",
)
SERVICE_CATEGORY_REMAINING_KEYWORDS = (
    "nhóm khác",
    "nhóm còn lại",
    "các nhóm còn lại",
    "phần còn lại",
)
SERVICE_CATALOG_KEYWORDS = (
    "các dịch vụ hiện có",
    "dịch vụ hiện có",
    "các dịch vụ hiện tại",
    "dịch vụ hiện tại",
    "danh sách dịch vụ",
    "các dịch vụ của phòng khám",
    "phòng khám có những dịch vụ nào",
    "phòng khám có các dịch vụ nào",
    "có những dịch vụ nào",
    "có các dịch vụ nào",
    "tất cả dịch vụ",
)
SERVICE_CATEGORY_DETAIL_PATTERNS = (
    r"(?:xem|cho tôi xem)\s+(?:chi tiết\s+)?(?:các\s+dịch vụ\s+)?(?:trong\s+)?nhóm\s+(.+)",
    r"(?:xem|cho tôi xem|chi tiết|dịch vụ|các dịch vụ)\s+(?:trong\s+)?nhóm\s+(.+)",
    r"nhóm\s+(.+?)\s+(?:gồm|có)\s+(?:những\s+)?(?:gì|dịch vụ nào)",
    r"(.+?)\s+(?:gồm|có)\s+(?:những\s+)?dịch vụ nào",
)
SERVICE_PACKAGE_KEYWORDS = (
    "gói khám",
    "gói dịch vụ",
    "service package",
    "package",
)
LAB_INDICATOR_KEYWORDS = (
    "chỉ số xét nghiệm",
    "chỉ số",
    "analyte",
    "indicator",
    "khoảng tham chiếu",
    "reference range",
    "đơn vị",
)
LAB_RESULT_KEYWORDS = (
    "kết quả xét nghiệm",
    "nhận kết quả",
    "lấy kết quả",
    "xem kết quả",
    "tra kết quả",
)
PARTNER_LAB_REQUEST_KEYWORDS = (
    "yêu cầu xét nghiệm",
    "request xét nghiệm",
    "trạng thái xét nghiệm",
    "trạng thái mẫu",
    "mẫu đã lấy",
    "đã lấy mẫu",
    "đã lấy chưa",
    "lấy mẫu tận nơi",
    "lịch lấy mẫu",
    "mã accession",
    "accession",
    "barcode",
)
PATIENT_TIMELINE_KEYWORDS = (
    "timeline của tôi",
    "dòng thời gian của tôi",
    "lịch sử khám của tôi",
    "quá trình khám của tôi",
    "quá trình điều trị của tôi",
    "tóm tắt quá trình khám",
    "tóm tắt lịch sử khám",
    "tổng quan lịch sử khám",
    "tổng quan bệnh nhân",
    "tóm tắt bệnh nhân",
    "patient timeline",
)
VISIT_SUMMARY_KEYWORDS = (
    "tóm tắt lần khám",
    "tóm tắt lượt khám",
    "tóm tắt hồ sơ khám",
    "hồ sơ khám của tôi",
    "bệnh án của tôi",
    "lần khám gần đây",
    "lần khám mới nhất",
    "lịch sử bệnh án",
    "medical record",
    "visit summary",
)
BILLING_SUMMARY_KEYWORDS = (
    "hóa đơn của tôi",
    "hoá đơn của tôi",
    "thanh toán của tôi",
    "tôi đã thanh toán chưa",
    "còn nợ bao nhiêu",
    "công nợ của tôi",
    "invoice của tôi",
    "payment của tôi",
    "billing của tôi",
)
PATIENT_PROFILE_KEYWORDS = (
    "hồ sơ của tôi",
    "thông tin hồ sơ của tôi",
    "thông tin cá nhân của tôi",
    "thông tin bệnh nhân của tôi",
    "hồ sơ bệnh nhân của tôi",
    "số điện thoại của tôi",
    "email của tôi",
    "ngày sinh của tôi",
    "mã bệnh nhân của tôi",
    "patient profile",
    "profile của tôi",
)
MEDICAL_ADVICE_KEYWORDS = (
    "nên sử dụng",
    "nên dùng",
    "nên chọn",
    "nên khám",
    "cần khám",
    "khám gì",
    "nên xét nghiệm",
    "nên làm xét nghiệm",
    "loại nào",
)
SYMPTOM_CUES = (
    "đau",
    "sốt",
    "ho",
    "khó thở",
    "buồn nôn",
    "nôn",
    "chóng mặt",
    "tiêu chảy",
    "mệt",
    "ngứa",
    "sưng",
    "chảy máu",
)
TRIAGE_CONTEXT_CUES = (
    "tôi",
    "em",
    "mình",
    "bị",
    "nên",
    "cần",
    "khám",
    "làm gì",
    "thì sao",
)
GUIDANCE_KEYWORDS = ("quy trình", "hướng dẫn", "làm thế nào", "như thế nào", "cách")
DOCTOR_KEYWORDS = ("bác sĩ", "doctor", "lịch khám", "có khám")
PERSONAL_KEYWORDS = (
    "của tôi",
    "tôi có lịch hẹn",
    "lịch hẹn của tôi",
    "kết quả của tôi",
    "hồ sơ của tôi",
    "lịch khám của tôi",
)
BOOKING_KEYWORDS = (
    "đặt lịch",
    "đăng ký khám",
    "book lịch",
    "hẹn khám",
    "tạo lịch hẹn",
    "muốn khám",
    "đặt khám",
)
GENERAL_KEYWORDS = ("địa chỉ", "ở đâu", "số điện thoại", "phone", "email", "mở cửa", "giờ làm")
KNOWLEDGE_KEYWORDS = (
    "quy trình",
    "hướng dẫn",
    "làm thế nào",
    "như thế nào",
    "mẫu câu hỏi",
    "câu hỏi gợi ý",
    "gợi ý câu hỏi",
    "hỏi bác sĩ câu gì",
    "nên hỏi bác sĩ",
    "nhận kết quả",
    "trả kết quả",
    "lấy mẫu",
    "check-in",
    "tiếp nhận",
    "đặt lịch",
    "khám sức khỏe",
)
GREETING_PHRASES = (
    "xin chào",
    "chào",
    "hello",
    "bạn là ai",
    "bạn làm được gì",
    "bạn có thể làm gì",
    "chức năng",
    "giới thiệu",
)


class RuleIntentParser:
    def parse(self, question: str, domain: str) -> Intent:
        normalized = question.strip().lower()

        if self._is_greeting(normalized):
            return Intent(
                domain=domain,
                intent="greeting",
                entities={},
                confidence=0.9,
                data_source="none",
                reasoning="Question appears to greet or ask bot capabilities.",
            )

        if any(keyword in normalized for keyword in MEDICAL_ADVICE_KEYWORDS) or self._is_symptom_triage_question(
            normalized
        ):
            return Intent(
                domain=domain,
                intent="medical_advice",
                entities={},
                confidence=0.76,
                data_source="none",
                reasoning="Question asks for medical advice or service recommendation.",
            )

        category_query = self._clean_category_detail_query(question)
        if category_query:
            service_type = self._service_type_from_question(normalized)
            if category_query.isdigit() and service_type == "all":
                service_type = "lab"
            return Intent(
                domain=domain,
                intent="service_category_detail",
                entities={
                    "category_query": category_query,
                    "service_type": service_type,
                },
                confidence=0.78,
                data_source="sql",
                reasoning="Question asks for services inside a specific service category.",
            )

        remaining_category_entities = self._remaining_category_entities(normalized)
        if remaining_category_entities:
            return Intent(
                domain=domain,
                intent="service_category_list",
                entities=remaining_category_entities,
                confidence=0.74,
                data_source="sql",
                reasoning="Question asks to continue the previously truncated service category list.",
            )

        if any(keyword in normalized for keyword in SERVICE_CATEGORY_KEYWORDS):
            return Intent(
                domain=domain,
                intent="service_category_list",
                entities={"service_type": "lab" if "xét nghiệm" in normalized else "all"},
                confidence=0.75,
                data_source="sql",
                reasoning="Question asks for service/test categories.",
            )

        if any(keyword in normalized for keyword in SERVICE_CATALOG_KEYWORDS):
            return Intent(
                domain=domain,
                intent="service_catalog_summary",
                entities={"service_type": self._service_type_from_question(normalized)},
                confidence=0.78,
                data_source="sql",
                reasoning="Question asks for a broad service catalog summary.",
            )

        if any(keyword in normalized for keyword in SERVICE_PACKAGE_KEYWORDS):
            return Intent(
                domain=domain,
                intent="service_package_detail",
                entities={"package_query": self._clean_package_query(question)},
                confidence=0.78,
                data_source="sql",
                reasoning="Question asks about a service package and its items.",
            )

        if self._is_lab_indicator_question(normalized):
            return Intent(
                domain=domain,
                intent="lab_indicator_detail",
                entities={"indicator_query": self._clean_lab_indicator_query(question)},
                confidence=0.78,
                data_source="sql",
                reasoning="Question asks about lab indicators/analytes for a service.",
            )

        if any(keyword in normalized for keyword in LAB_RESULT_KEYWORDS) and not any(
            keyword in normalized for keyword in GUIDANCE_KEYWORDS
        ):
            return Intent(
                domain=domain,
                intent="lab_result_lookup",
                entities={"result_query": question.strip()},
                confidence=0.82,
                requires_auth=True,
                data_source="auth",
                reasoning="Question asks to look up lab/diagnostic results.",
            )

        if any(keyword in normalized for keyword in PARTNER_LAB_REQUEST_KEYWORDS) and not any(
            keyword in normalized for keyword in GUIDANCE_KEYWORDS
        ):
            return Intent(
                domain=domain,
                intent="partner_lab_request_lookup",
                entities={"request_query": self._clean_partner_lab_request_query(question)},
                confidence=0.82,
                requires_auth=True,
                data_source="auth",
                reasoning="Question asks to look up partner lab request or onsite collection status.",
            )

        if any(keyword in normalized for keyword in PATIENT_TIMELINE_KEYWORDS):
            return Intent(
                domain=domain,
                intent="patient_timeline_summary",
                entities={"patient_query": self._clean_patient_timeline_query(question)},
                confidence=0.84,
                requires_auth=True,
                data_source="auth",
                reasoning="Question asks to summarize authenticated patient timeline data.",
            )

        if any(keyword in normalized for keyword in VISIT_SUMMARY_KEYWORDS):
            return Intent(
                domain=domain,
                intent="visit_summary_lookup",
                entities={"patient_query": self._clean_visit_summary_query(question)},
                confidence=0.84,
                requires_auth=True,
                data_source="auth",
                reasoning="Question asks to look up authenticated visit or medical record summaries.",
            )

        if any(keyword in normalized for keyword in BILLING_SUMMARY_KEYWORDS):
            return Intent(
                domain=domain,
                intent="billing_summary_lookup",
                entities={"patient_query": self._clean_billing_summary_query(question)},
                confidence=0.84,
                requires_auth=True,
                data_source="auth",
                reasoning="Question asks to look up authenticated billing or payment summaries.",
            )

        if any(keyword in normalized for keyword in PATIENT_PROFILE_KEYWORDS):
            return Intent(
                domain=domain,
                intent="patient_profile_summary",
                entities={"patient_query": self._clean_patient_profile_query(question)},
                confidence=0.84,
                requires_auth=True,
                data_source="auth",
                reasoning="Question asks to look up authenticated patient profile data.",
            )

        if any(keyword in normalized for keyword in PERSONAL_KEYWORDS):
            return Intent(
                domain=domain,
                intent="personal_data",
                entities={},
                confidence=0.85,
                requires_auth=True,
                data_source="auth",
                reasoning="Question appears to request personal data.",
            )

        if any(keyword in normalized for keyword in BOOKING_KEYWORDS):
            return Intent(
                domain=domain,
                intent="appointment_booking",
                entities={"booking_query": question.strip()},
                confidence=0.82,
                data_source="none",
                reasoning="Question appears to request appointment booking.",
            )

        if any(keyword in normalized for keyword in KNOWLEDGE_KEYWORDS):
            return Intent(
                domain=domain,
                intent="knowledge_search",
                entities={"knowledge_query": question.strip()},
                confidence=0.68,
                data_source="rag",
                reasoning="Question appears to ask about guidance, process, or FAQ.",
            )

        if any(keyword in normalized for keyword in GENERAL_KEYWORDS):
            return Intent(
                domain=domain,
                intent="general_info",
                entities={"profile_query": self._clean_profile_query(question)},
                confidence=0.65,
                data_source="sql",
                reasoning="Question appears to ask public clinic information.",
            )

        if any(keyword in normalized for keyword in SERVICE_KEYWORDS):
            return Intent(
                domain=domain,
                intent="service_price",
                entities={"service_query": self._clean_service_query(question)},
                confidence=0.72,
                data_source="sql",
                reasoning="Question appears to ask about service or price.",
            )

        if any(keyword in normalized for keyword in DOCTOR_KEYWORDS):
            return Intent(
                domain=domain,
                intent="doctor_schedule",
                entities={
                    "doctor_query": self._clean_doctor_query(question),
                    "date": "today" if "hôm nay" in normalized else None,
                    "weekday": date.today().isoweekday() if "hôm nay" in normalized else None,
                },
                confidence=0.7,
                data_source="sql",
                reasoning="Question appears to ask about doctor schedule.",
            )

        return Intent(
            domain=domain,
            intent="out_of_scope",
            entities={},
            confidence=0.4,
            data_source="none",
            reasoning="No confident rule match.",
        )

    def _is_greeting(self, normalized_question: str) -> bool:
        if any(phrase in normalized_question for phrase in GREETING_PHRASES):
            return True
        return bool(re.search(r"\bhi\b", normalized_question))

    def _is_symptom_triage_question(self, normalized_question: str) -> bool:
        has_symptom = any(self._contains_phrase(normalized_question, cue) for cue in SYMPTOM_CUES)
        has_context = any(cue in normalized_question for cue in TRIAGE_CONTEXT_CUES)
        return has_symptom and has_context

    def _contains_phrase(self, normalized_question: str, phrase: str) -> bool:
        if " " in phrase:
            return phrase in normalized_question
        return bool(re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", normalized_question))

    def _clean_service_query(self, question: str) -> str:
        text = question
        replacements = [
            "giá bao nhiêu",
            "bao nhiêu",
            "giá",
            "dịch vụ",
            "xét nghiệm",
            "chụp phim",
            "chụp",
            "tôi muốn",
            "muốn",
            "cho tôi",
            "có",
            "không",
            "?",
        ]
        for value in replacements:
            text = re.sub(re.escape(value), " ", text, flags=re.IGNORECASE)
        return re.sub(r"\s+", " ", text).strip()

    def _clean_package_query(self, question: str) -> str:
        text = question
        replacements = [
            "gói khám",
            "gói dịch vụ",
            "service package",
            "package",
            "gồm những dịch vụ nào",
            "gồm dịch vụ nào",
            "gồm những gì",
            "gồm những",
            "gồm gì",
            "có những gì",
            "có những",
            "có gì",
            "giá bao nhiêu",
            "bao nhiêu",
            "giá",
            "xem",
            "chi tiết",
            "cho tôi",
            "?",
        ]
        for value in replacements:
            text = re.sub(re.escape(value), " ", text, flags=re.IGNORECASE)
        return re.sub(r"\s+", " ", text).strip()

    def _is_lab_indicator_question(self, normalized_question: str) -> bool:
        if any(keyword in normalized_question for keyword in LAB_INDICATOR_KEYWORDS):
            return "xét nghiệm" in normalized_question or any(
                keyword in normalized_question
                for keyword in ("cbc", "wbc", "rbc", "hgb", "plt", "aptt", "tibc")
            )
        return bool(
            re.search(
                r"\b(cbc|wbc|rbc|hgb|plt|aptt|tibc)\b.*(?:gồm|có).*(?:chỉ số|indicator|analyte)",
                normalized_question,
            )
        )

    def _clean_lab_indicator_query(self, question: str) -> str:
        text = question
        replacements = [
            "chỉ số xét nghiệm",
            "chỉ số",
            "xét nghiệm",
            "analyte",
            "indicator",
            "khoảng tham chiếu",
            "reference range",
            "đơn vị",
            "gồm những gì",
            "gồm những",
            "gồm gì",
            "có những gì",
            "có những",
            "có gì",
            "có",
            "là gì",
            "nào",
            "xem",
            "chi tiết",
            "cho tôi",
            "?",
        ]
        for value in replacements:
            text = re.sub(re.escape(value), " ", text, flags=re.IGNORECASE)
        return re.sub(r"\s+", " ", text).strip()

    def _service_type_from_question(self, normalized_question: str) -> str:
        if "xét nghiệm" in normalized_question or "lab" in normalized_question:
            return "lab"
        if "chụp" in normalized_question or re.search(
            r"\b(ct|mri|mr|x-ray|xray|x quang|x-quang|imaging|ultrasound|endoscopy)\b",
            normalized_question,
        ):
            return "imaging"
        return "all"

    def _clean_category_detail_query(self, question: str) -> str:
        normalized = question.strip().lower()
        if not any(value in normalized for value in ("nhóm", "group", "category")):
            return ""
        if any(value in normalized for value in SERVICE_CATEGORY_REMAINING_KEYWORDS):
            return ""
        for pattern in SERVICE_CATEGORY_DETAIL_PATTERNS:
            match = re.search(pattern, question, flags=re.IGNORECASE)
            if not match:
                continue
            text = match.group(1)
            text = re.sub(r"\b(gồm|có|những|gì|dịch vụ nào|dịch vụ|chi tiết)\b", " ", text, flags=re.IGNORECASE)
            text = re.sub(r"[?.!]+", " ", text)
            return re.sub(r"\s+", " ", text).strip()
        return ""

    def _remaining_category_entities(self, normalized_question: str) -> dict:
        if not any(keyword in normalized_question for keyword in SERVICE_CATEGORY_REMAINING_KEYWORDS):
            return {}

        count_match = re.search(r"(\d+)\s+nhóm", normalized_question)
        display_limit = int(count_match.group(1)) if count_match else 12

        return {
            "service_type": self._service_type_from_question(normalized_question)
            if self._service_type_from_question(normalized_question) != "all"
            else "lab",
            "offset": 12,
            "display_limit": min(max(display_limit, 1), 50),
        }

    def _clean_profile_query(self, question: str) -> str:
        text = question
        replacements = [
            "địa chỉ",
            "ở đâu",
            "số điện thoại",
            "phone",
            "email",
            "lúc mấy giờ",
            "mấy giờ",
            "lúc mấy",
            "mở cửa",
            "giờ làm việc",
            "giờ làm",
            "phòng khám",
            "trung tâm",
            "cơ sở",
            "clinic",
            "hospital",
            "cho tôi biết",
            "cho tôi",
            "thông tin",
            "của",
            "về",
            "?",
        ]
        for value in replacements:
            text = re.sub(re.escape(value), " ", text, flags=re.IGNORECASE)
        return re.sub(r"\s+", " ", text).strip()

    def _clean_patient_profile_query(self, question: str) -> str:
        text = question
        replacements = [
            "hồ sơ bệnh nhân",
            "hồ sơ của tôi",
            "thông tin hồ sơ",
            "thông tin cá nhân",
            "thông tin bệnh nhân",
            "số điện thoại của tôi",
            "email của tôi",
            "ngày sinh của tôi",
            "mã bệnh nhân của tôi",
            "profile của tôi",
            "patient profile",
            "của tôi",
            "cho tôi xem",
            "xem",
            "là gì",
            "?",
        ]
        for value in replacements:
            text = re.sub(re.escape(value), " ", text, flags=re.IGNORECASE)
        return re.sub(r"\s+", " ", text).strip()

    def _clean_partner_lab_request_query(self, question: str) -> str:
        text = question
        replacements = [
            "mẫu xét nghiệm",
            "yêu cầu xét nghiệm",
            "request xét nghiệm",
            "trạng thái xét nghiệm",
            "trạng thái mẫu",
            "mẫu đã lấy chưa",
            "mẫu đã lấy",
            "đã lấy mẫu chưa",
            "đã lấy mẫu",
            "đã lấy chưa",
            "lấy mẫu tận nơi",
            "lịch lấy mẫu",
            "mã accession",
            "accession",
            "barcode",
            "của tôi",
            "cho tôi xem",
            "xem",
            "tra",
            "là gì",
            "?",
        ]
        for value in replacements:
            text = re.sub(re.escape(value), " ", text, flags=re.IGNORECASE)
        return re.sub(r"\s+", " ", text).strip()

    def _clean_patient_timeline_query(self, question: str) -> str:
        text = question
        replacements = [
            "timeline của tôi",
            "dòng thời gian của tôi",
            "lịch sử khám của tôi",
            "quá trình khám của tôi",
            "quá trình điều trị của tôi",
            "tóm tắt quá trình khám",
            "tóm tắt lịch sử khám",
            "tổng quan lịch sử khám",
            "tổng quan bệnh nhân",
            "tóm tắt bệnh nhân",
            "patient timeline",
            "của tôi",
            "cho tôi xem",
            "xem",
            "là gì",
            "?",
        ]
        for value in replacements:
            text = re.sub(re.escape(value), " ", text, flags=re.IGNORECASE)
        return re.sub(r"\s+", " ", text).strip()

    def _clean_visit_summary_query(self, question: str) -> str:
        text = question
        replacements = [
            "tóm tắt lần khám",
            "tóm tắt lượt khám",
            "tóm tắt hồ sơ khám",
            "hồ sơ khám của tôi",
            "bệnh án của tôi",
            "lần khám gần đây",
            "lần khám mới nhất",
            "lịch sử bệnh án",
            "medical record",
            "visit summary",
            "của tôi",
            "cho tôi xem",
            "xem",
            "là gì",
            "?",
        ]
        for value in replacements:
            text = re.sub(re.escape(value), " ", text, flags=re.IGNORECASE)
        return re.sub(r"\s+", " ", text).strip()

    def _clean_billing_summary_query(self, question: str) -> str:
        text = question
        replacements = [
            "hóa đơn của tôi",
            "hoá đơn của tôi",
            "thanh toán của tôi",
            "tôi đã thanh toán chưa",
            "còn nợ bao nhiêu",
            "công nợ của tôi",
            "invoice của tôi",
            "payment của tôi",
            "billing của tôi",
            "của tôi",
            "cho tôi xem",
            "xem",
            "là gì",
            "?",
        ]
        for value in replacements:
            text = re.sub(re.escape(value), " ", text, flags=re.IGNORECASE)
        return re.sub(r"\s+", " ", text).strip()

    def _clean_doctor_query(self, question: str) -> str:
        text = question
        replacements = [
            "hôm nay",
            "bác sĩ",
            "doctor",
            "có khám không",
            "có khám",
            "lịch",
            "?",
        ]
        for value in replacements:
            text = re.sub(re.escape(value), " ", text, flags=re.IGNORECASE)
        return re.sub(r"\s+", " ", text).strip()

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
LAB_RESULT_KEYWORDS = (
    "kết quả xét nghiệm",
    "nhận kết quả",
    "lấy kết quả",
    "xem kết quả",
    "tra kết quả",
)
MEDICAL_ADVICE_KEYWORDS = (
    "nên sử dụng",
    "nên dùng",
    "nên chọn",
    "nên xét nghiệm",
    "nên làm xét nghiệm",
    "loại nào",
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

        if any(keyword in normalized for keyword in MEDICAL_ADVICE_KEYWORDS):
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
            return Intent(
                domain=domain,
                intent="service_category_detail",
                entities={
                    "category_query": category_query,
                    "service_type": self._service_type_from_question(normalized),
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

    def _service_type_from_question(self, normalized_question: str) -> str:
        if "xét nghiệm" in normalized_question or "lab" in normalized_question:
            return "lab"
        if any(value in normalized_question for value in ("chụp", "ct", "mri", "x-quang", "x quang", "imaging")):
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

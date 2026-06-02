import http.client
import json
import logging
import urllib.error
import urllib.request
from typing import Any

from app.config import get_settings
from app.core.schemas import Intent
from app.domains.clinic.prompts import INTENT_SYSTEM_PROMPT


logger = logging.getLogger(__name__)


SOURCE_BY_INTENT = {
    "greeting": "none",
    "general_info": "sql",
    "service_price": "sql",
    "service_category_list": "sql",
    "service_catalog_summary": "sql",
    "service_category_detail": "sql",
    "doctor_schedule": "sql",
    "knowledge_search": "rag",
    "appointment_booking": "none",
    "appointment_lookup": "auth",
    "lab_result_lookup": "auth",
    "patient_timeline_summary": "auth",
    "visit_summary_lookup": "auth",
    "patient_profile_summary": "auth",
    "personal_data": "auth",
    "medical_advice": "none",
    "out_of_scope": "none",
}

AUTH_REQUIRED_BY_INTENT = {
    "appointment_lookup": True,
    "lab_result_lookup": True,
    "patient_timeline_summary": True,
    "visit_summary_lookup": True,
    "patient_profile_summary": True,
    "personal_data": True,
}

ENTITY_KEYS_BY_INTENT = {
    "general_info": ("profile_query",),
    "service_price": ("service_query",),
    "service_category_list": ("service_type",),
    "service_catalog_summary": ("service_type",),
    "service_category_detail": ("category_query", "service_type"),
    "doctor_schedule": ("doctor_query", "date", "weekday"),
    "knowledge_search": ("knowledge_query",),
    "appointment_booking": ("booking_query",),
    "lab_result_lookup": ("result_query",),
    "patient_timeline_summary": ("patient_query",),
    "visit_summary_lookup": ("patient_query",),
    "patient_profile_summary": ("patient_query",),
}


LLM_CALL_EXCEPTIONS = (
    KeyError,
    TypeError,
    ValueError,
    TimeoutError,
    ConnectionError,
    http.client.HTTPException,
    urllib.error.URLError,
)


INTENT_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "domain",
        "intent",
        "entities",
        "confidence",
        "requires_auth",
        "data_source",
        "reasoning",
    ],
    "properties": {
        "domain": {"type": "string"},
        "intent": {
            "type": "string",
            "enum": [
                "greeting",
                "general_info",
                "service_price",
                "service_category_list",
                "service_catalog_summary",
                "service_category_detail",
                "doctor_schedule",
                "knowledge_search",
                "appointment_booking",
                "appointment_lookup",
                "lab_result_lookup",
                "patient_timeline_summary",
                "visit_summary_lookup",
                "patient_profile_summary",
                "personal_data",
                "medical_advice",
                "out_of_scope",
            ],
        },
        "entities": {"type": "object", "additionalProperties": True},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "requires_auth": {"type": "boolean"},
        "data_source": {"type": "string", "enum": ["sql", "rag", "auth", "none"]},
        "reasoning": {"type": "string"},
    },
}


class LLMClient:
    """Provider abstraction for LLM intent parsing.

    The current MVP intentionally falls back to rules when no provider is
    configured. Provider calls must return the same Intent schema.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def enabled(self) -> bool:
        return self.settings.llm_provider.lower() not in {"", "none", "disabled"}

    @property
    def is_ollama(self) -> bool:
        return self.settings.llm_provider.lower() == "ollama"

    def parse_intent(self, question: str, domain: str) -> Intent | None:
        if not self.enabled:
            return None

        provider = self.settings.llm_provider.lower()
        if provider in {"openai", "openai_compatible"}:
            return self._parse_intent_openai_compatible(question=question, domain=domain)
        if provider == "ollama":
            return self._parse_intent_ollama(question=question, domain=domain)

        logger.warning("Unsupported LLM provider: %s", self.settings.llm_provider)
        return None

    def generate_grounded_answer(self, question: str, context: str) -> str | None:
        if not self.enabled or not context.strip():
            return None

        provider = self.settings.llm_provider.lower()
        if provider in {"openai", "openai_compatible"}:
            return self._generate_grounded_answer_openai_compatible(question, context)
        if provider == "ollama":
            return self._generate_grounded_answer_ollama(question, context)

        logger.warning("Unsupported LLM provider for grounded answer: %s", self.settings.llm_provider)
        return None

    def generate_formatted_answer(
        self,
        question: str,
        intent_name: str,
        context: str,
        is_private: bool,
        audience_role: str = "guest",
    ) -> str | None:
        """Format retrieved SQL/Auth data with local Ollama only.

        This is intentionally local-only because it may receive patient data.
        """

        if not self.enabled or not self.is_ollama or not context.strip():
            return None
        return self._generate_formatted_answer_ollama(
            question=question,
            intent_name=intent_name,
            context=context,
            is_private=is_private,
            audience_role=audience_role,
        )

    def _parse_intent_openai_compatible(self, question: str, domain: str) -> Intent | None:
        api_key = self.settings.openai_api_key.strip()
        if not api_key:
            logger.warning("LLM_PROVIDER is enabled but OPENAI_API_KEY is empty.")
            return None

        payload = {
            "model": self.settings.llm_model,
            "messages": [
                {
                    "role": "system",
                    "content": self._system_prompt(domain),
                },
                {
                    "role": "user",
                    "content": question,
                },
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "intent_parser",
                    "strict": True,
                    "schema": INTENT_JSON_SCHEMA,
                },
            },
            "temperature": 0,
        }

        request = urllib.request.Request(
            self._chat_completions_url(),
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.settings.llm_timeout_seconds) as response:
                raw = response.read().decode("utf-8")
            body = json.loads(raw)
            content = body["choices"][0]["message"]["content"]
            parsed = self._parse_json_content(content)
            return self._intent_from_payload(parsed, domain)
        except LLM_CALL_EXCEPTIONS as exc:
            logger.warning("LLM intent parsing failed; falling back to rules: %s", exc)
            return None

    def _parse_intent_ollama(self, question: str, domain: str) -> Intent | None:
        try:
            content = self._post_ollama_chat(
                messages=[
                    {
                        "role": "system",
                        "content": self._system_prompt(domain),
                    },
                    {
                        "role": "user",
                        "content": question,
                    },
                ],
                expect_json=True,
                timeout_seconds=self.settings.llm_intent_timeout_seconds,
            )
            parsed = self._parse_json_content(content)
            return self._intent_from_payload(parsed, domain)
        except LLM_CALL_EXCEPTIONS as exc:
            logger.warning("Ollama intent parsing failed; falling back to rules: %s", exc)
            return None

    def _generate_grounded_answer_openai_compatible(
        self,
        question: str,
        context: str,
    ) -> str | None:
        api_key = self.settings.openai_api_key.strip()
        if not api_key:
            logger.warning("LLM grounded answer is enabled but OPENAI_API_KEY is empty.")
            return None

        payload = {
            "model": self.settings.llm_model,
            "messages": self._grounded_answer_messages(question, context),
            "temperature": 0,
        }

        request = urllib.request.Request(
            self._chat_completions_url(),
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.settings.llm_timeout_seconds) as response:
                raw = response.read().decode("utf-8")
            body = json.loads(raw)
            return self._clean_answer(body["choices"][0]["message"]["content"])
        except LLM_CALL_EXCEPTIONS as exc:
            logger.warning("LLM grounded answer failed; using template fallback: %s", exc)
            return None

    def _generate_grounded_answer_ollama(self, question: str, context: str) -> str | None:
        try:
            content = self._post_ollama_chat(
                messages=self._grounded_answer_messages(question, context),
                timeout_seconds=self.settings.llm_answer_timeout_seconds,
            )
            return self._clean_answer(content)
        except LLM_CALL_EXCEPTIONS as exc:
            logger.warning("Ollama grounded answer failed; using template fallback: %s", exc)
            return None

    def _generate_formatted_answer_ollama(
        self,
        question: str,
        intent_name: str,
        context: str,
        is_private: bool,
        audience_role: str,
    ) -> str | None:
        try:
            content = self._post_ollama_chat(
                messages=self._formatted_answer_messages(
                    question=question,
                    intent_name=intent_name,
                    context=context,
                    is_private=is_private,
                    audience_role=audience_role,
                ),
                timeout_seconds=self.settings.llm_answer_timeout_seconds,
            )
            return self._clean_answer(content)
        except LLM_CALL_EXCEPTIONS as exc:
            logger.warning("Ollama formatted answer failed; using template fallback: %s", exc)
            return None

    def _post_ollama_chat(
        self,
        messages: list[dict[str, str]],
        *,
        expect_json: bool = False,
        timeout_seconds: int | None = None,
    ) -> str:
        payload = {
            "model": self.settings.llm_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0,
                "num_predict": 512,
            },
        }
        if expect_json:
            payload["format"] = "json"

        request = urllib.request.Request(
            self._ollama_chat_url(),
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        timeout = timeout_seconds or self.settings.llm_timeout_seconds
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
        body = json.loads(raw)
        return str(body["message"]["content"])

    def _grounded_answer_messages(self, question: str, context: str) -> list[dict[str, str]]:
        return [
            {
                "role": "system",
                "content": (
                    "Bạn là trợ lý robot lễ tân phòng khám. Hãy trả lời bằng tiếng Việt một cách "
                    "ngắn gọn, rõ ràng và thân thiện.\n\n"
                    "TUYỆT ĐỐI TUÂN THỦ CÁC QUY TẮC SAU:\n"
                    "1. Chỉ dùng thông tin từ CONTEXT: Không tự suy luận, bịa đặt thêm giá cả, "
                    "lịch trình, địa chỉ, dữ liệu cá nhân hoặc bất kỳ chi tiết nào không có trong CONTEXT.\n"
                    "2. Không tự ý thêm thắt: Không thêm các câu cảnh báo, điều kiện, khuyến nghị "
                    "hoặc biến thể quy trình nếu chúng không xuất hiện trong CONTEXT.\n"
                    "3. Xử lý khi thiếu thông tin: Nếu CONTEXT không đủ dữ liệu để trả lời, BẮT BUỘC "
                    "phải nói đúng nguyên văn: 'Tôi chưa tìm thấy thông tin phù hợp trong dữ liệu hiện có.' "
                    "và không nói thêm gì khác."
                ),
            },
            {
                "role": "user",
                "content": f"QUESTION:\n{question}\n\nCONTEXT:\n{context}",
            },
        ]

    def _formatted_answer_messages(
        self,
        question: str,
        intent_name: str,
        context: str,
        is_private: bool,
        audience_role: str = "guest",
    ) -> list[dict[str, str]]:
        privacy_note = (
            "Dữ liệu riêng tư đã được backend xác thực và lọc quyền. Không nhắc lại về xác thực.\n"
            if is_private
            else ""
        )
        intent_rules = self._formatted_answer_rules(intent_name)
        return [
            {
                "role": "system",
                "content": (
                    "Bạn là formatter cho robot lễ tân phòng khám. Chỉ viết lại CONTEXT thành "
                    "câu trả lời tiếng Việt dễ đọc. Không tự thêm dữ liệu.\n\n"
                    f"{privacy_note}"
                    "Luật chung:\n"
                    "- Chỉ dùng CONTEXT, không suy luận thêm.\n"
                    "- Giữ nguyên văn tên dịch vụ, mã dịch vụ, tên cơ sở, tên bệnh nhân, tên bác sĩ.\n"
                    "- Nếu nhiều dòng trong CONTEXT, liệt kê đủ các dòng được cung cấp.\n"
                    "- Không dùng bảng markdown.\n\n"
                    f"Luật riêng cho intent {intent_name}:\n{intent_rules}"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"INTENT: {intent_name}\n"
                    f"AUDIENCE_ROLE: {audience_role}\n"
                    f"QUESTION:\n{question}\n\n"
                    f"CONTEXT:\n{context}"
                ),
            },
        ]

    def _formatted_answer_rules(self, intent_name: str) -> str:
        if intent_name in {"appointment_lookup", "personal_data"}:
            return (
                "- Trả lời dạng danh sách đánh số.\n"
                "- Mỗi mục gồm ngày giờ, bệnh nhân nếu người hỏi là bác sĩ/lễ tân/admin, nội dung/dịch vụ, trạng thái.\n"
                "- patient_name luôn là bệnh nhân; doctor_name luôn là bác sĩ.\n"
                "- Nếu doctor_name thiếu hoặc là 'không có dữ liệu', không dùng patient_name làm tên bác sĩ.\n"
                "- Nếu AUDIENCE_ROLE là doctor, không viết 'bạn có lịch với bác sĩ ...'."
            )
        if intent_name == "lab_result_lookup":
            return (
                "- Trả lời các kết quả/chỉ định xét nghiệm theo danh sách.\n"
                "- Nói rõ service_name, status, has_result và result_summary nếu có.\n"
                "- Không kết luận y khoa và không diễn giải chỉ số xét nghiệm ngoài result_summary."
            )
        if intent_name == "patient_profile_summary":
            return (
                "- Trả lời ngắn gọn các thông tin hành chính của hồ sơ bệnh nhân.\n"
                "- Giữ nguyên patient_code, full_name, phone_primary, email, date_of_birth nếu có.\n"
                "- Không suy luận bệnh sử, chẩn đoán hoặc thông tin y khoa không có trong CONTEXT."
            )
        if intent_name == "patient_timeline_summary":
            return (
                "- Trả lời dạng timeline ngắn gọn theo ngày giờ giảm dần như CONTEXT.\n"
                "- Mỗi mục nói rõ loại mốc: lịch hẹn hoặc xét nghiệm/cận lâm sàng.\n"
                "- Không chẩn đoán, không suy luận kết quả ngoài result_summary hoặc status có trong CONTEXT."
            )
        if intent_name == "visit_summary_lookup":
            return (
                "- Trả lời dạng danh sách các lần khám/lượt khám.\n"
                "- Chỉ nêu chief_complaint, examination_findings, confirmed_diagnosis, treatment_plan, follow_up và vital signs có trong CONTEXT.\n"
                "- Không diễn giải chỉ số sinh hiệu, không chẩn đoán thêm, không khuyến nghị ngoài treatment_plan trong CONTEXT."
            )
        if intent_name == "service_price":
            return (
                "- Giữ nguyên code, name, category_name, price_amount và currency_code.\n"
                "- Nếu có nhiều dịch vụ, liệt kê đủ các dịch vụ trong CONTEXT.\n"
                "- Không dịch tên dịch vụ."
            )
        if intent_name == "general_info":
            return (
                "- Nếu có nhiều cơ sở, liệt kê đủ từng cơ sở trong CONTEXT.\n"
                "- Với mỗi cơ sở, nêu địa chỉ, thành phố, số điện thoại, email, giờ làm việc nếu có.\n"
                "- Nếu một trường thiếu, có thể bỏ qua hoặc nói 'chưa có dữ liệu'."
            )
        return "- Viết ngắn gọn, bám sát từng dòng dữ liệu trong CONTEXT."

    def _clean_answer(self, value: str) -> str | None:
        lines = [" ".join(line.split()) for line in str(value or "").strip().splitlines()]
        text = "\n".join(line for line in lines if line)
        if not text:
            return None
        return text

    def _intent_from_payload(self, payload: dict[str, Any], domain: str) -> Intent:
        normalized = self._normalize_intent_payload(payload, domain)
        return Intent(**normalized)

    def _normalize_intent_payload(self, payload: dict[str, Any], domain: str) -> dict[str, Any]:
        normalized = dict(payload or {})
        normalized["domain"] = normalized.get("domain") or domain

        data_source = str(normalized.get("data_source") or "").strip()
        intent = str(normalized.get("intent") or "").strip()
        if not intent:
            nested_intent = self._find_nested_intent_payload(normalized)
            if nested_intent:
                intent, nested_payload = nested_intent
                for key, value in nested_payload.items():
                    normalized.setdefault(key, value)

        if not intent and data_source in SOURCE_BY_INTENT:
            intent = data_source
        if intent not in SOURCE_BY_INTENT:
            intent = self._infer_intent_from_entity_keys(normalized)
        if intent:
            normalized["intent"] = intent

        entities = normalized.get("entities")
        if not isinstance(entities, dict):
            entities = {}
        if intent in ENTITY_KEYS_BY_INTENT:
            for key in ENTITY_KEYS_BY_INTENT[intent]:
                if normalized.get(key) not in {None, ""} and entities.get(key) in {None, ""}:
                    entities[key] = normalized[key]
        normalized["entities"] = entities

        if intent in SOURCE_BY_INTENT:
            normalized["data_source"] = SOURCE_BY_INTENT[intent]
            normalized["requires_auth"] = AUTH_REQUIRED_BY_INTENT.get(
                intent,
                bool(normalized.get("requires_auth", False)),
            )
        elif data_source not in {"sql", "rag", "auth", "none"}:
            normalized["data_source"] = "none"

        if normalized.get("confidence") is None:
            normalized["confidence"] = 0.5
        if normalized.get("requires_auth") is None:
            normalized["requires_auth"] = False
        if not normalized.get("reasoning"):
            normalized["reasoning"] = "Normalized from LLM JSON payload."

        return normalized

    def _infer_intent_from_entity_keys(self, payload: dict[str, Any]) -> str:
        entities = payload.get("entities") if isinstance(payload.get("entities"), dict) else {}
        keys = set(payload) | set(entities)
        for intent, entity_keys in ENTITY_KEYS_BY_INTENT.items():
            if keys.intersection(entity_keys):
                return intent
        return ""

    def _find_nested_intent_payload(self, payload: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
        for key, value in payload.items():
            if key in SOURCE_BY_INTENT and isinstance(value, dict):
                return key, value
        return None

    def _system_prompt(self, domain: str) -> str:
        if domain == "clinic":
            return INTENT_SYSTEM_PROMPT
        return (
            "You are an intent parser for an AI receptionist. Return only JSON matching "
            "the Intent schema. Do not answer business data directly."
        )

    def _chat_completions_url(self) -> str:
        base_url = self.settings.llm_base_url.rstrip("/")
        if base_url.endswith("/chat/completions"):
            return base_url
        return f"{base_url}/chat/completions"

    def _ollama_chat_url(self) -> str:
        base_url = self.settings.llm_base_url.rstrip("/")
        if base_url.endswith("/api/chat"):
            return base_url
        return f"{base_url}/api/chat"

    def _parse_json_content(self, content: str) -> dict[str, Any]:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}")
            if start == -1 or end == -1 or end <= start:
                raise
            return json.loads(content[start : end + 1])

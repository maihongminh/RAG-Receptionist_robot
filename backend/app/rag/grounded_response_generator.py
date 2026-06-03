from app.config import get_settings
from app.llm.llm_client import LLMClient
from app.core.schemas import AuthContext, Intent, ToolResult
from app.rag.rag_config import get_rag_config


class GroundedResponseGenerator:
    """Generate natural answers from retrieved context only."""

    def __init__(self) -> None:
        self.llm_client = LLMClient()

    def generate(
        self,
        question: str,
        intent: Intent,
        result: ToolResult,
        auth: AuthContext | None = None,
    ) -> str | None:
        if result.tool_name == "policy_guard":
            return None

        auth = auth or AuthContext(role="guest")

        if intent.intent == "knowledge_search" and not intent.requires_auth:
            context = self._build_knowledge_context(result)
            if not context:
                return None
            grounded_answer = self.llm_client.generate_grounded_answer(
                question=question,
                context=context,
            )
            if grounded_answer:
                return grounded_answer

        context = self._build_context(result, auth)
        if not context:
            return None

        if intent.intent in {"greeting", "out_of_scope", "medical_advice"}:
            return None
        if not self._should_use_llm_formatter(intent, result):
            return None

        formatted_answer = self.llm_client.generate_formatted_answer(
            question=question,
            intent_name=intent.intent,
            context=context,
            is_private=intent.requires_auth,
            audience_role=auth.role,
        )
        if (
            formatted_answer
            and not self._contradicts_non_empty_result(formatted_answer, result)
            and not self._has_appointment_role_confusion(
                formatted_answer,
                result.rows,
                auth,
            )
            and not self._has_service_name_rewrite(
                formatted_answer,
                result.rows,
                intent.intent,
            )
            and not self._drops_public_profile_rows(
                formatted_answer,
                result.rows,
                intent.intent,
            )
        ):
            return formatted_answer
        return None

    def _build_context(
        self,
        result: ToolResult,
        auth: AuthContext | None = None,
        limit: int | None = None,
    ) -> str:
        chunks = []
        auth = auth or AuthContext(role="guest")
        row_limit = get_rag_config().context_max_rows
        max_chars = limit or get_settings().llm_context_char_limit
        if auth.role:
            chunks.append(f"[audience]\nrole: {auth.role}")
        for index, row in enumerate(result.rows[:row_limit], start=1):
            title = row.get("title_vi") or row.get("title") or row.get("topic") or f"Dòng {index}"
            content = self._compact_text(self._serialize_row(row, auth))
            score = row.get("_score")
            score_text = f" score={score}" if score is not None else ""
            chunks.append(f"[{index}] {title}{score_text}\n{content}")

        if result.message:
            chunks.append(f"[message]\n{self._compact_text(result.message)}")

        context = "\n\n".join(chunks)
        if len(context) <= max_chars:
            return context
        return context[:max_chars].rstrip()

    def _build_knowledge_context(self, result: ToolResult, limit: int | None = None) -> str:
        chunks = []
        row_limit = min(get_rag_config().context_max_rows, 3)
        max_chars = min(limit or get_settings().llm_context_char_limit, 1800)
        for index, row in enumerate(result.rows[:row_limit], start=1):
            title = row.get("title_vi") or row.get("title") or row.get("topic") or f"Tài liệu {index}"
            content = row.get("content_vi") or row.get("content") or ""
            content = self._compact_text(content)
            if not content:
                continue
            chunks.append(f"[{index}] {title}\n{content}")

        context = "\n\n".join(chunks)
        if len(context) <= max_chars:
            return context
        return context[:max_chars].rstrip()

    def _should_use_llm_formatter(self, intent: Intent, result: ToolResult) -> bool:
        if not result.rows:
            return False
        if intent.intent in {
            "doctor_schedule",
            "service_category_list",
            "service_catalog_summary",
            "service_category_detail",
        }:
            return False
        if intent.intent == "service_price" and len(result.rows) > 1:
            return False
        return intent.intent in {
            "general_info",
            "service_price",
            "appointment_lookup",
            "personal_data",
            "lab_result_lookup",
            "patient_timeline_summary",
            "visit_summary_lookup",
            "billing_summary_lookup",
            "patient_profile_summary",
        }

    def _serialize_row(self, row: dict, auth: AuthContext) -> str:
        if self._is_appointment_row(row):
            return self._serialize_appointment_row(row, auth)
        if self._is_service_row(row):
            return self._serialize_service_row(row)

        lines = []
        for key, value in row.items():
            if key.startswith("_") or value in {None, ""}:
                continue
            lines.append(f"{key}: {value}")
        return "\n".join(lines)

    def _is_service_row(self, row: dict) -> bool:
        return "price_amount" in row and ("name" in row or "code" in row)

    def _serialize_service_row(self, row: dict) -> str:
        lines = [
            "record_type: service",
            "field_rule: Giữ nguyên văn name, code, category_name và currency_code; không dịch tên dịch vụ.",
        ]
        for key, value in row.items():
            if key.startswith("_") or value in {None, ""}:
                continue
            lines.append(f"{key}: {value}")
        return "\n".join(lines)

    def _is_appointment_row(self, row: dict) -> bool:
        return "appointment_date" in row and (
            "patient_name" in row or "doctor_name" in row or "visit_type" in row
        )

    def _serialize_appointment_row(self, row: dict, auth: AuthContext) -> str:
        doctor_name = row.get("doctor_name") or "không có dữ liệu"
        service = row.get("service_name") or row.get("visit_type") or "không có dữ liệu"
        audience_rule = {
            "patient": (
                "audience_rule: Người đang hỏi là bệnh nhân. Trả lời là lịch của họ; "
                "chỉ gọi doctor_name là bác sĩ nếu doctor_name có dữ liệu."
            ),
            "doctor": (
                "audience_rule: Người đang hỏi là bác sĩ. Trả lời là lịch bệnh nhân với bác sĩ này; "
                "không viết 'với bác sĩ <patient_name>'."
            ),
            "receptionist": (
                "audience_rule: Người đang hỏi là lễ tân. Trả lời dạng danh sách lịch hẹn của bệnh nhân trong phòng khám."
            ),
            "clinic_admin": (
                "audience_rule: Người đang hỏi là clinic admin. Trả lời dạng danh sách lịch hẹn của bệnh nhân trong phòng khám."
            ),
        }.get(auth.role, "audience_rule: Trả lời trung lập theo dữ liệu lịch hẹn.")
        return "\n".join(
            [
                "record_type: appointment",
                f"audience_role: {auth.role}",
                audience_rule,
                "field_rule: patient_name là bệnh nhân; doctor_name là bác sĩ.",
                "field_rule: Nếu doctor_name là 'không có dữ liệu', không được dùng patient_name làm tên bác sĩ.",
                f"appointment_id: {row.get('id') or 'không có dữ liệu'}",
                f"appointment_date: {row.get('appointment_date') or 'không có dữ liệu'}",
                f"start_time: {row.get('start_time') or 'không có dữ liệu'}",
                f"end_time: {row.get('end_time') or 'không có dữ liệu'}",
                f"patient_name: {row.get('patient_name') or 'không có dữ liệu'}",
                f"doctor_name: {doctor_name}",
                f"service_or_visit_type: {service}",
                f"status: {row.get('status') or 'không có dữ liệu'}",
                f"chief_complaint: {row.get('chief_complaint') or 'không có dữ liệu'}",
            ]
        )

    def _has_appointment_role_confusion(
        self,
        answer: str,
        rows: list[dict],
        auth: AuthContext | None = None,
    ) -> bool:
        normalized_answer = self._normalize(answer)
        auth = auth or AuthContext(role="guest")
        if "bác sĩ" not in normalized_answer:
            return False

        for row in rows:
            if not self._is_appointment_row(row):
                continue
            patient_name = str(row.get("patient_name") or "").strip()
            doctor_name = str(row.get("doctor_name") or "").strip()
            if not patient_name or patient_name == doctor_name:
                continue
            if f"bác sĩ {self._normalize(patient_name)}" in normalized_answer:
                return True
            if auth.role == "doctor" and f"với bác sĩ {self._normalize(patient_name)}" in normalized_answer:
                return True
        return False

    def _contradicts_non_empty_result(self, answer: str, result: ToolResult) -> bool:
        if not result.rows:
            return False

        normalized_answer = self._normalize(answer)
        negative_phrases = (
            "chưa có lịch",
            "không có lịch",
            "chưa có lịch hẹn",
            "không có lịch hẹn",
            "không tìm thấy",
            "chưa tìm thấy",
            "không có dữ liệu",
            "chưa có dữ liệu",
        )
        return any(phrase in normalized_answer for phrase in negative_phrases)

    def _has_service_name_rewrite(
        self,
        answer: str,
        rows: list[dict],
        intent_name: str,
    ) -> bool:
        if intent_name != "service_price" or not rows:
            return False

        normalized_answer = self._normalize(answer)
        row_limit = get_rag_config().context_max_rows
        for row in rows[:row_limit]:
            service_name = str(row.get("name") or "").strip()
            if service_name and self._normalize(service_name) not in normalized_answer:
                return True
        return False

    def _drops_public_profile_rows(
        self,
        answer: str,
        rows: list[dict],
        intent_name: str,
    ) -> bool:
        if intent_name != "general_info" or len(rows) <= 1:
            return False

        normalized_answer = self._normalize(answer)
        row_limit = get_rag_config().context_max_rows
        for row in rows[:row_limit]:
            clinic_name = str(row.get("name") or "").strip()
            if clinic_name and self._normalize(clinic_name) not in normalized_answer:
                return True
        return False

    def _compact_text(self, value: str) -> str:
        lines = []
        for line in str(value or "").replace("#", " ").replace("*", " ").splitlines():
            compacted = " ".join(line.split())
            if compacted:
                lines.append(compacted)
        return "\n".join(lines)

    def _normalize(self, value: str) -> str:
        return " ".join(str(value or "").lower().split())

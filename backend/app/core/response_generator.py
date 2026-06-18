from app.core.schemas import AuthContext, Intent, ToolResult
from app.rag.rag_config import get_rag_config


class ResponseGenerator:
    def generate(
        self,
        question: str,
        intent: Intent,
        result: ToolResult,
        auth: AuthContext | None = None,
    ) -> str:
        if result.tool_name == "policy_guard":
            return "Bạn chưa có quyền thực hiện yêu cầu này hoặc cần xác thực trước khi tra cứu."

        if intent.intent in {"appointment_lookup", "personal_data"}:
            return self._private_data(result, auth or AuthContext(role="guest"))
        if intent.intent == "lab_result_lookup":
            return self._lab_result_lookup(result)
        if intent.intent == "partner_lab_request_lookup":
            return self._partner_lab_request_lookup(result)
        if intent.intent == "patient_timeline_summary":
            return self._patient_timeline_summary(result)
        if intent.intent == "visit_summary_lookup":
            return self._visit_summary_lookup(result)
        if intent.intent == "billing_summary_lookup":
            return self._billing_summary_lookup(result)
        if intent.intent == "patient_profile_summary":
            return self._patient_profile_summary(result)

        if intent.requires_auth:
            return (
                "Thông tin này thuộc dữ liệu cá nhân. Vui lòng xác thực bằng số điện thoại, "
                "CCCD/ID hoặc OTP trước khi tôi tra cứu."
            )

        if intent.intent == "greeting":
            return self._greeting()
        if intent.intent == "general_info":
            return self._general_info(result)
        if intent.intent == "service_price":
            return self._service_price(result)
        if intent.intent == "service_category_list":
            return self._service_category_list(result)
        if intent.intent == "service_catalog_summary":
            return self._service_catalog_summary(result)
        if intent.intent == "service_category_detail":
            return self._service_category_detail(result)
        if intent.intent == "service_package_detail":
            return self._service_package_detail(result)
        if intent.intent == "lab_indicator_detail":
            return self._lab_indicator_detail(result)
        if intent.intent == "doctor_schedule":
            return self._doctor_schedule(intent, result)
        if intent.intent == "knowledge_search":
            return self._knowledge_search(question, result)
        if intent.intent == "appointment_booking":
            return self._appointment_booking()
        if intent.intent == "medical_advice":
            return self._medical_advice(question)

        if result.message:
            return result.message
        return "Tôi chưa có đủ dữ liệu để trả lời câu hỏi này. Vui lòng liên hệ nhân viên lễ tân để được hỗ trợ."

    def _greeting(self) -> str:
        return (
            "Xin chào, tôi là robot lễ tân. Hiện tôi có thể hỗ trợ tra cứu thông tin phòng khám, "
            "địa chỉ, số điện thoại, giờ làm việc, giá dịch vụ và lịch bác sĩ. "
            "Với thông tin cá nhân như lịch hẹn hoặc kết quả xét nghiệm, tôi sẽ yêu cầu xác thực trước khi tra cứu."
        )

    def _general_info(self, result: ToolResult) -> str:
        if not result.rows:
            return "Tôi chưa tìm thấy thông tin cơ sở trong hệ thống."
        lines = []
        max_rows = get_rag_config().context_max_rows
        for row in result.rows[:max_rows]:
            parts = [f"{row.get('name')}"]
            if row.get("address"):
                parts.append(f"địa chỉ: {row.get('address')}")
            else:
                parts.append("địa chỉ: chưa có dữ liệu")
            if row.get("city"):
                parts.append(f"thành phố: {row.get('city')}")
            if row.get("phone"):
                parts.append(f"số điện thoại: {row.get('phone')}")
            if row.get("email"):
                parts.append(f"email: {row.get('email')}")
            if row.get("working_hours_start") and row.get("working_hours_end"):
                parts.append(
                    f"giờ làm việc: {row.get('working_hours_start')} - {row.get('working_hours_end')}"
                )
            lines.append(". ".join(str(part) for part in parts if part) + ".")
        if len(lines) == 1:
            return lines[0]
        return "Tôi tìm thấy các cơ sở đang hoạt động:\n" + "\n".join(
            f"{index}. {line}" for index, line in enumerate(lines, start=1)
        )

    def _service_price(self, result: ToolResult) -> str:
        if not result.rows:
            return "Tôi chưa tìm thấy dịch vụ phù hợp trong bảng dịch vụ."
        if len(result.rows) > 1:
            lines = []
            max_rows = get_rag_config().context_max_rows
            for row in result.rows[:max_rows]:
                price = row.get("price_amount")
                currency = row.get("currency_code") or ""
                price_text = f"{price} {currency}" if price is not None else "chưa có giá"
                code = f"{row.get('code')} - " if row.get("code") else ""
                lines.append(f"{code}{row.get('name')}: {price_text}")
            return "Tôi tìm thấy các dịch vụ phù hợp:\n" + "\n".join(
                f"{index}. {line}" for index, line in enumerate(lines, start=1)
            )
        row = result.rows[0]
        price = row.get("price_amount")
        currency = row.get("currency_code") or ""
        if price is None:
            return f"Tôi tìm thấy dịch vụ {row.get('name')}, nhưng chưa có giá trong hệ thống."
        return f"Dịch vụ {row.get('name')} có giá {price} {currency}."

    def _service_category_list(self, result: ToolResult) -> str:
        if not result.rows:
            return "Tôi chưa tìm thấy nhóm dịch vụ phù hợp trong hệ thống."
        lines = []
        first = result.rows[0]
        offset = self._safe_int(first.get("category_offset"), default=0)
        total_categories = self._safe_int(first.get("total_categories"), default=offset + len(result.rows))
        display_limit = self._safe_int(first.get("display_limit"), default=12)
        display_rows = result.rows[: min(display_limit, len(result.rows))]
        for row in display_rows:
            category = row.get("category_name") or "Chưa phân nhóm"
            service_type = row.get("service_type") or "dịch vụ"
            count = row.get("service_count") or 0
            min_price = row.get("min_price")
            max_price = row.get("max_price")
            currency = row.get("currency_code") or ""
            price_text = ""
            if min_price is not None and max_price is not None:
                price_text = f", giá từ {min_price} đến {max_price} {currency}"
            lines.append(f"{category} ({service_type}, {count} dịch vụ{price_text})")
        suffix = ""
        hidden_count = max(total_categories - offset - len(display_rows), 0)
        if hidden_count > 0:
            suffix = f"\nCòn {hidden_count} nhóm khác trong dữ liệu. Bạn muốn xem chi tiết nhóm nào?"
        title = (
            "Các nhóm dịch vụ còn lại phù hợp:\n"
            if offset > 0
            else "Tôi tìm thấy các nhóm dịch vụ phù hợp:\n"
        )
        return title + "\n".join(
            f"{index}. {line}" for index, line in enumerate(lines, start=offset + 1)
        ) + suffix

    def _safe_int(self, value: object, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _service_catalog_summary(self, result: ToolResult) -> str:
        if not result.rows:
            return "Tôi chưa tìm thấy danh mục dịch vụ phù hợp trong hệ thống."

        first = result.rows[0]
        total_services = first.get("total_services") or sum(
            int(row.get("service_count") or 0) for row in result.rows
        )
        total_categories = first.get("total_categories") or len(result.rows)
        offset = self._safe_int(first.get("category_offset"), default=0)
        display_limit = self._safe_int(first.get("display_limit"), default=10)
        display_rows = result.rows[: min(display_limit, len(result.rows))]

        lines = []
        for row in display_rows:
            category = row.get("category_name") or "Chưa phân nhóm"
            service_type = row.get("service_type") or "dịch vụ"
            count = row.get("service_count") or 0
            min_price = row.get("min_price")
            max_price = row.get("max_price")
            currency = row.get("currency_code") or ""
            price_text = ""
            if min_price is not None and max_price is not None:
                price_text = f", giá từ {min_price} đến {max_price} {currency}".rstrip()
            lines.append(f"{category} ({service_type}, {count} dịch vụ{price_text})")

        hidden_count = max(int(total_categories) - offset - len(display_rows), 0)
        suffix = "\nBạn muốn xem chi tiết nhóm nào?"
        if hidden_count > 0:
            suffix = f"\nCòn {hidden_count} nhóm khác trong dữ liệu. Bạn muốn xem chi tiết nhóm nào?"
        title = (
            f"Phòng khám hiện có {total_services} dịch vụ trong {total_categories} nhóm. "
            f"Dưới đây là {len(display_rows)} nhóm lớn nhất:\n"
            if offset == 0
            else "Các nhóm dịch vụ còn lại phù hợp:\n"
        )
        return (
            title
            + "\n".join(f"{index}. {line}" for index, line in enumerate(lines, start=offset + 1))
            + suffix
        )

    def _service_category_detail(self, result: ToolResult) -> str:
        if not result.rows:
            return result.message or "Tôi chưa tìm thấy dịch vụ trong nhóm phù hợp."

        first = result.rows[0]
        category = first.get("matched_category_name") or first.get("category_name") or "nhóm dịch vụ"
        total = first.get("total_services_in_category") or len(result.rows)
        display_rows = result.rows[: min(20, len(result.rows))]

        lines = []
        for row in display_rows:
            price = row.get("price_amount")
            currency = row.get("currency_code") or ""
            price_text = f"{price} {currency}" if price is not None else "chưa có giá"
            code = f"{row.get('code')} - " if row.get("code") else ""
            duration = f", thời lượng {row.get('duration_minutes')} phút" if row.get("duration_minutes") else ""
            lines.append(f"{code}{row.get('name')}: {price_text}{duration}")

        hidden_count = int(total) - len(display_rows)
        suffix = ""
        if hidden_count > 0:
            suffix = f"\nNhóm này còn {hidden_count} dịch vụ khác. Bạn có thể hỏi tên dịch vụ cụ thể để xem giá."

        return (
            f"Nhóm {category} có {total} dịch vụ. Dưới đây là {len(display_rows)} dịch vụ đầu tiên:\n"
            + "\n".join(f"{index}. {line}" for index, line in enumerate(lines, start=1))
            + suffix
        )

    def _service_package_detail(self, result: ToolResult) -> str:
        if not result.rows:
            return result.message or "Tôi chưa tìm thấy gói dịch vụ phù hợp."

        first = result.rows[0]
        package_name = first.get("package_name") or first.get("name") or "gói dịch vụ"
        package_code = first.get("package_code") or first.get("code")
        total = self._safe_int(first.get("total_items_in_package"), default=len(result.rows))
        price = first.get("package_price_amount")
        currency = first.get("currency_code") or ""
        price_text = f", giá gói {price} {currency}" if price is not None else ""
        valid_days = f", hiệu lực {first.get('valid_days')} ngày" if first.get("valid_days") else ""
        package_label = f"{package_code} - {package_name}" if package_code else str(package_name)

        service_rows = [row for row in result.rows if row.get("service_name") or row.get("service_code")]
        if not service_rows:
            return f"Tôi tìm thấy {package_label}{price_text}{valid_days}, nhưng chưa có thành phần dịch vụ trong hệ thống."

        lines = []
        for row in service_rows[: min(20, len(service_rows))]:
            code = f"{row.get('service_code')} - " if row.get("service_code") else ""
            service = row.get("service_name") or "dịch vụ chưa rõ"
            quantity = row.get("quantity")
            quantity_text = f", số lượng {quantity}" if quantity not in {None, ""} else ""
            service_price = row.get("service_price_amount")
            service_currency = row.get("service_currency_code") or ""
            service_price_text = (
                f", giá lẻ {service_price} {service_currency}" if service_price is not None else ""
            )
            category = f", nhóm {row.get('service_category_name')}" if row.get("service_category_name") else ""
            lines.append(f"{code}{service}{category}{quantity_text}{service_price_text}")

        hidden_count = max(total - len(lines), 0)
        suffix = ""
        if hidden_count > 0:
            suffix = f"\nGói này còn {hidden_count} dịch vụ khác trong dữ liệu."

        return (
            f"{package_label} có {total} dịch vụ{price_text}{valid_days}:\n"
            + "\n".join(f"{index}. {line}" for index, line in enumerate(lines, start=1))
            + suffix
        )

    def _lab_indicator_detail(self, result: ToolResult) -> str:
        if not result.rows:
            return result.message or "Tôi chưa tìm thấy chỉ số xét nghiệm phù hợp."

        first = result.rows[0]
        same_service = len({row.get("service_id") for row in result.rows if row.get("service_id")}) == 1
        service_name = first.get("service_name") or first.get("service_code") or "dịch vụ xét nghiệm"
        total = self._safe_int(first.get("total_indicators"), default=len(result.rows))
        display_rows = result.rows[: min(20, len(result.rows))]

        lines = []
        for row in display_rows:
            code = f"{row.get('code')} - " if row.get("code") else ""
            name = row.get("name") or row.get("name_en") or "chỉ số chưa rõ"
            unit = f", đơn vị {row.get('unit')}" if row.get("unit") else ""
            reference = (
                f", khoảng tham chiếu {row.get('reference_range_text')}"
                if row.get("reference_range_text")
                else ""
            )
            specimen = f", mẫu {row.get('specimen_type')}" if row.get("specimen_type") else ""
            method = f", phương pháp {row.get('method')}" if row.get("method") else ""
            if same_service:
                lines.append(f"{code}{name}{unit}{reference}{specimen}{method}")
            else:
                service = row.get("service_name") or row.get("service_code") or "dịch vụ chưa rõ"
                lines.append(f"{service}: {code}{name}{unit}{reference}{specimen}{method}")

        hidden_count = max(total - len(display_rows), 0)
        suffix = ""
        if hidden_count > 0:
            suffix = f"\nCòn {hidden_count} chỉ số khác trong dữ liệu."

        if same_service:
            return (
                f"Dịch vụ {service_name} có {total} chỉ số xét nghiệm:\n"
                + "\n".join(f"{index}. {line}" for index, line in enumerate(lines, start=1))
                + suffix
            )
        return (
            "Tôi tìm thấy các chỉ số xét nghiệm phù hợp:\n"
            + "\n".join(f"{index}. {line}" for index, line in enumerate(lines, start=1))
            + suffix
        )

    def _doctor_schedule(self, intent: Intent, result: ToolResult) -> str:
        if not result.rows:
            return "Tôi chưa tìm thấy lịch phù hợp cho bác sĩ trong hệ thống."

        lines = []
        max_rows = get_rag_config().context_max_rows
        for row in result.rows[:max_rows]:
            doctor = row.get("doctor_name") or "bác sĩ"
            day = row.get("day_of_week")
            start = row.get("start_time")
            end = row.get("end_time")
            room = row.get("room_name") or row.get("room_code") or "chưa rõ phòng"
            lines.append(f"{doctor} có lịch thứ {day}, từ {start} đến {end}, tại {room}")

        return "Tôi tìm thấy lịch bác sĩ phù hợp:\n" + "\n".join(
            f"{index}. {line}" for index, line in enumerate(lines, start=1)
        )

    def _knowledge_search(self, question: str, result: ToolResult) -> str:
        if not result.rows:
            return "Tôi chưa tìm thấy hướng dẫn phù hợp trong dữ liệu hiện có."

        if result.rows[0].get("document_type") == "patient_question_template":
            return self._patient_question_template_answer(question, result)

        row = result.rows[0]
        title = row.get("title_vi") or row.get("title") or row.get("topic") or "Thông tin hướng dẫn"
        content = row.get("content_vi") or row.get("content") or ""
        summary_lines = self._knowledge_summary_lines(content, title)
        if summary_lines:
            return f"{title}:\n" + "\n".join(summary_lines)
        return f"Tôi tìm thấy nội dung liên quan: {title}."

    def _patient_question_template_answer(self, question: str, result: ToolResult) -> str:
        max_rows = get_rag_config().context_max_rows
        preferred_topic = self._preferred_question_template_topic(question)
        rows = result.rows
        if preferred_topic:
            topic_rows = [row for row in rows if row.get("topic") == preferred_topic]
            if topic_rows:
                rows = topic_rows

        questions = []
        for row in rows[:max_rows]:
            question = row.get("title_vi") or row.get("title")
            if question and question not in questions:
                questions.append(str(question))

        if not questions:
            return "Tôi tìm thấy mẫu câu hỏi gợi ý, nhưng dữ liệu hiện chưa có nội dung chi tiết."

        lines = [f"{index}. {question}" for index, question in enumerate(questions, start=1)]
        return "Bạn có thể tham khảo các câu hỏi sau để trao đổi với bác sĩ:\n" + "\n".join(lines)

    def _preferred_question_template_topic(self, question: str) -> str | None:
        normalized = question.lower()
        if any(keyword in normalized for keyword in ("thuốc", "medication", "uống thuốc")):
            return "medication"
        if any(keyword in normalized for keyword in ("xét nghiệm", "kết quả", "test result")):
            return "test_results"
        if any(keyword in normalized for keyword in ("lối sống", "sinh hoạt", "hoạt động", "lifestyle")):
            return "lifestyle"
        return None

    def _knowledge_summary_lines(self, content: str, title: str, limit: int = 8) -> list[str]:
        raw_lines = str(content or "").splitlines()
        lines = []
        for raw_line in raw_lines:
            line = " ".join(raw_line.strip().split())
            if not line:
                continue
            line = line.replace("**", "").replace("__", "")
            line = line.lstrip("#").strip()
            line = line.lstrip("-•").strip()
            line = self._strip_repeated_title(line, title)
            if not line:
                continue
            if line.lower() in {"workflow", "tips", "mẹo"}:
                continue
            if line.startswith("###"):
                line = line.lstrip("#").strip()
            lines.append(line)

        cleaned = []
        for line in lines:
            if len(cleaned) >= limit:
                break
            if self._is_unhelpful_knowledge_heading(line):
                continue
            if line not in cleaned:
                cleaned.append(line)
        while cleaned and self._is_unhelpful_knowledge_heading(cleaned[-1]):
            cleaned.pop()
        return cleaned

    def _is_unhelpful_knowledge_heading(self, line: str) -> bool:
        normalized = " ".join(str(line or "").lower().split())
        return normalized in {
            "quy trình",
            "loại lấy mẫu",
            "phương thức trả kết quả",
            "mẹo",
            "tips",
            "workflow",
        }

    def _compact_text(self, value: str, limit: int = 520) -> str:
        text = " ".join(str(value or "").replace("#", " ").replace("*", " ").split())
        if len(text) <= limit:
            return text
        return text[:limit].rstrip() + "..."

    def _strip_repeated_title(self, summary: str, title: str) -> str:
        text = summary.strip()
        normalized_title = " ".join(str(title or "").replace("#", " ").replace("*", " ").split())
        if normalized_title and text.lower().startswith(normalized_title.lower()):
            text = text[len(normalized_title) :].lstrip(" :-")
        return text

    def _appointment_booking(self) -> str:
        return (
            "Tôi đã hiểu bạn muốn đặt lịch khám. Hiện chức năng tạo lịch hẹn tự động chưa được bật. "
            "Bạn có thể cho biết dịch vụ/chuyên khoa, ngày giờ mong muốn và số điện thoại liên hệ; "
            "nhân viên lễ tân sẽ xác nhận lịch cho bạn. Nếu cần, tôi cũng có thể cung cấp số điện thoại hoặc giờ làm việc của phòng khám."
        )

    def _lab_result_lookup(self, result: ToolResult) -> str:
        if not result.rows:
            return result.message or "Tôi chưa tìm thấy kết quả xét nghiệm/cận lâm sàng phù hợp."
        lines = []
        for index, row in enumerate(result.rows, start=1):
            service = row.get("service_name") or row.get("service_code") or "dịch vụ chưa rõ"
            status = self._lab_result_status_label(row.get("status"))
            result_state = "đã có kết quả" if row.get("has_result") else "chưa có kết quả"
            parts = [f"{index}. {service}: {status}, {result_state}"]
            if row.get("completed_at"):
                parts.append(f"hoàn tất lúc {row.get('completed_at')}")
            detail = row.get("result_summary") or row.get("result_file_url")
            if detail:
                parts.append(f"kết quả: {detail}")
            lines.append("\n   ".join(parts))
        return "Tôi tìm thấy các chỉ định/kết quả xét nghiệm trong phạm vi đã xác thực:\n" + "\n".join(lines)

    def _partner_lab_request_lookup(self, result: ToolResult) -> str:
        if not result.rows:
            return result.message or "Tôi chưa tìm thấy yêu cầu xét nghiệm/lấy mẫu phù hợp."

        lines = []
        for index, row in enumerate(result.rows, start=1):
            accession = row.get("accession_number") or row.get("barcode") or row.get("id")
            patient = row.get("patient_name") or "bệnh nhân chưa rõ"
            if row.get("record_type") == "partner_onsite_collection":
                parts = [
                    f"{index}. Lấy mẫu tận nơi {accession}: {row.get('onsite_status') or 'chưa rõ trạng thái'}",
                    f"bệnh nhân {patient}",
                ]
                if row.get("preferred_date"):
                    preferred_time = ""
                    if row.get("preferred_time_start") or row.get("preferred_time_end"):
                        preferred_time = f" {row.get('preferred_time_start') or ''}-{row.get('preferred_time_end') or ''}".strip()
                    parts.append(f"lịch mong muốn {row.get('preferred_date')}{(' ' + preferred_time) if preferred_time else ''}")
                if row.get("collection_address"):
                    parts.append(f"địa chỉ {row.get('collection_address')}")
                if row.get("assigned_collector_name"):
                    parts.append(f"người lấy mẫu {row.get('assigned_collector_name')}")
                if row.get("collected_at"):
                    parts.append(f"đã lấy mẫu lúc {row.get('collected_at')}")
                if row.get("returned_to_lab_at"):
                    parts.append(f"đã chuyển về lab lúc {row.get('returned_to_lab_at')}")
                lines.append(", ".join(str(part) for part in parts if part) + ".")
                continue

            parts = [
                f"{index}. Yêu cầu xét nghiệm {accession}: {row.get('status') or 'chưa rõ trạng thái'}",
                f"bệnh nhân {patient}",
            ]
            if row.get("sample_type"):
                parts.append(f"mẫu {row.get('sample_type')}")
            if row.get("collection_method"):
                parts.append(f"hình thức {row.get('collection_method')}")
            if row.get("requested_at"):
                parts.append(f"tạo lúc {row.get('requested_at')}")
            if row.get("sample_collected_at"):
                parts.append(f"đã lấy mẫu lúc {row.get('sample_collected_at')}")
            if row.get("processing_started_at"):
                parts.append(f"bắt đầu xử lý lúc {row.get('processing_started_at')}")
            if row.get("completed_at"):
                parts.append(f"hoàn tất lúc {row.get('completed_at')}")
            if row.get("delivered_at"):
                parts.append(f"đã trả lúc {row.get('delivered_at')}")
            if row.get("estimated_completion_at"):
                parts.append(f"dự kiến hoàn tất {row.get('estimated_completion_at')}")
            lines.append(", ".join(str(part) for part in parts if part) + ".")

        return "Tôi tìm thấy yêu cầu xét nghiệm/lấy mẫu trong phạm vi đã xác thực:\n" + "\n".join(lines)

    def _patient_profile_summary(self, result: ToolResult) -> str:
        if not result.rows:
            return result.message or "Tôi chưa tìm thấy hồ sơ bệnh nhân phù hợp."

        lines = []
        for index, row in enumerate(result.rows, start=1):
            parts = [
                f"{row.get('full_name') or 'Bệnh nhân chưa rõ tên'}",
                f"mã bệnh nhân: {row.get('patient_code') or 'chưa có dữ liệu'}",
            ]
            if row.get("date_of_birth"):
                parts.append(f"ngày sinh: {row.get('date_of_birth')}")
            if row.get("gender"):
                parts.append(f"giới tính: {row.get('gender')}")
            if row.get("phone_primary"):
                parts.append(f"số điện thoại: {row.get('phone_primary')}")
            if row.get("email"):
                parts.append(f"email: {row.get('email')}")
            address_parts = [
                value
                for value in [row.get("address"), row.get("district"), row.get("city")]
                if value
            ]
            if address_parts:
                parts.append(f"địa chỉ: {', '.join(address_parts)}")
            if row.get("patient_category"):
                parts.append(f"nhóm bệnh nhân: {row.get('patient_category')}")
            lines.append(f"{index}. " + ". ".join(parts) + ".")

        title = "Tôi tìm thấy hồ sơ bệnh nhân trong phạm vi đã xác thực:"
        return title + "\n" + "\n".join(lines)

    def _patient_timeline_summary(self, result: ToolResult) -> str:
        if not result.rows:
            return result.message or "Tôi chưa tìm thấy timeline bệnh nhân phù hợp."

        lines = []
        for index, row in enumerate(result.rows, start=1):
            event_at = row.get("event_at") or row.get("appointment_date") or "chưa rõ thời gian"
            patient = row.get("patient_name")
            if row.get("event_type") == "appointment":
                title = row.get("service_name") or row.get("visit_type") or "lịch hẹn"
                parts = [f"{index}. {event_at} - Lịch hẹn: {title}"]
                if patient:
                    parts.append(f"bệnh nhân {patient}")
                if row.get("doctor_name"):
                    parts.append(f"bác sĩ {row.get('doctor_name')}")
                if row.get("status"):
                    parts.append(f"trạng thái {row.get('status')}")
                if row.get("chief_complaint"):
                    parts.append(f"lý do khám: {row.get('chief_complaint')}")
            else:
                service = row.get("service_name") or row.get("service_code") or "cận lâm sàng"
                parts = [f"{index}. {event_at} - Xét nghiệm/cận lâm sàng: {service}"]
                if patient:
                    parts.append(f"bệnh nhân {patient}")
                if row.get("status"):
                    parts.append(f"trạng thái {row.get('status')}")
                parts.append("đã có kết quả" if row.get("has_result") else "chưa có kết quả")
                if row.get("result_summary"):
                    parts.append(f"kết quả: {row.get('result_summary')}")
            lines.append("; ".join(parts) + ".")

        return "Tôi tìm thấy timeline bệnh nhân trong phạm vi đã xác thực:\n" + "\n".join(lines)

    def _visit_summary_lookup(self, result: ToolResult) -> str:
        if not result.rows:
            return result.message or "Tôi chưa tìm thấy tóm tắt lượt khám phù hợp."

        lines = []
        for index, row in enumerate(result.rows, start=1):
            visit_date = row.get("visit_date") or row.get("check_in_time") or "chưa rõ ngày"
            parts = [f"{index}. Ngày {visit_date}"]
            if row.get("patient_name"):
                parts.append(f"bệnh nhân {row.get('patient_name')}")
            if row.get("doctor_name"):
                parts.append(f"bác sĩ {row.get('doctor_name')}")
            if row.get("visit_type"):
                parts.append(f"loại khám {row.get('visit_type')}")
            if row.get("record_status"):
                parts.append(f"trạng thái hồ sơ {row.get('record_status')}")
            if row.get("chief_complaint"):
                parts.append(f"lý do khám: {row.get('chief_complaint')}")
            if row.get("examination_findings"):
                parts.append(f"ghi nhận khám: {row.get('examination_findings')}")
            if row.get("confirmed_diagnosis"):
                diagnosis = row.get("confirmed_diagnosis")
                if row.get("diagnosis_icd_code"):
                    diagnosis = f"{diagnosis} ({row.get('diagnosis_icd_code')})"
                parts.append(f"chẩn đoán đã ghi nhận: {diagnosis}")
            if row.get("treatment_plan"):
                parts.append(f"kế hoạch điều trị: {row.get('treatment_plan')}")
            vital_parts = []
            if row.get("blood_pressure_systolic") and row.get("blood_pressure_diastolic"):
                vital_parts.append(
                    f"huyết áp {row.get('blood_pressure_systolic')}/{row.get('blood_pressure_diastolic')}"
                )
            if row.get("heart_rate"):
                vital_parts.append(f"mạch {row.get('heart_rate')}")
            if row.get("temperature_celsius"):
                vital_parts.append(f"nhiệt độ {row.get('temperature_celsius')}")
            if row.get("oxygen_saturation"):
                vital_parts.append(f"SpO2 {row.get('oxygen_saturation')}")
            if vital_parts:
                parts.append("sinh hiệu: " + ", ".join(vital_parts))
            if row.get("follow_up_required") is True and row.get("follow_up_date"):
                parts.append(f"hẹn theo dõi {row.get('follow_up_date')}")
            elif row.get("follow_up_required") is False:
                parts.append("không ghi nhận yêu cầu tái khám")
            if row.get("follow_up_notes"):
                parts.append(f"ghi chú theo dõi: {row.get('follow_up_notes')}")
            lines.append("; ".join(parts) + ".")

        return "Tôi tìm thấy tóm tắt lượt khám trong phạm vi đã xác thực:\n" + "\n".join(lines)

    def _billing_summary_lookup(self, result: ToolResult) -> str:
        if not result.rows:
            return result.message or "Tôi chưa tìm thấy hóa đơn/thanh toán phù hợp."

        lines = []
        for index, row in enumerate(result.rows, start=1):
            invoice = row.get("invoice_number") or row.get("queue_number") or row.get("id")
            currency = row.get("currency_code") or ""
            parts = [f"{index}. Hóa đơn {invoice}"]
            if row.get("registered_at"):
                parts.append(f"ngày {row.get('registered_at')}")
            if row.get("patient_name"):
                parts.append(f"bệnh nhân {row.get('patient_name')}")
            if row.get("payment_status"):
                parts.append(f"trạng thái thanh toán {row.get('payment_status')}")
            if row.get("total_amount") is not None:
                parts.append(f"tổng tiền {row.get('total_amount')} {currency}".strip())
            if row.get("paid_amount") is not None:
                parts.append(f"đã thanh toán {row.get('paid_amount')} {currency}".strip())
            if row.get("balance_amount") is not None:
                parts.append(f"còn lại {row.get('balance_amount')} {currency}".strip())
            if row.get("payment_method"):
                parts.append(f"phương thức {row.get('payment_method')}")
            if row.get("paid_at"):
                parts.append(f"thanh toán lúc {row.get('paid_at')}")
            lines.append("; ".join(parts) + ".")

        return "Tôi tìm thấy hóa đơn/thanh toán trong phạm vi đã xác thực:\n" + "\n".join(lines)

    def _medical_advice(self, question: str) -> str:
        symptom = self._symptom_text(question)
        symptom_part = f" về tình trạng {symptom}" if symptom else " về triệu chứng của bạn"
        return (
            f"Tôi chưa thể chẩn đoán hoặc quyết định bạn nên khám chuyên khoa nào{symptom_part}. "
            "Bạn nên liên hệ bác sĩ hoặc nhân viên y tế để được hướng dẫn phù hợp. "
            "Nếu triệu chứng đau nhiều, kéo dài, kèm sốt cao, nôn ói liên tục, khó thở, ngất, "
            "chảy máu hoặc đau tăng nhanh, hãy đến cơ sở y tế/cấp cứu sớm. "
            "Tôi có thể giúp tra giờ làm việc, địa chỉ phòng khám, danh sách dịch vụ hoặc hướng dẫn đặt lịch để bạn tham khảo."
        )

    def _symptom_text(self, question: str) -> str:
        text = " ".join(str(question or "").strip(" ?.!\n\t").split())
        lowered = text.lower()
        for phrase in (
            "nên khám gì",
            "nên đi khám gì",
            "nên khám ở đâu",
            "cần khám gì",
            "cần đi khám gì",
            "nên xét nghiệm gì",
            "phải làm gì",
            "nên làm gì",
            "làm gì",
            "thì sao",
        ):
            lowered = lowered.replace(phrase, " ")
        lowered = lowered.removeprefix("tôi có triệu chứng").strip()
        lowered = lowered.removeprefix("triệu chứng").strip()
        lowered = lowered.removeprefix("tôi bị").strip()
        lowered = lowered.removeprefix("em bị").strip()
        lowered = lowered.removeprefix("mình bị").strip()
        lowered = lowered.removeprefix("tôi").strip()
        lowered = lowered.removeprefix("em").strip()
        lowered = lowered.removeprefix("mình").strip()
        symptom = " ".join(lowered.split()).strip(" ,.;:!?")
        if not symptom or symptom == text.lower():
            return ""
        return symptom[:120]

    def _private_data(self, result: ToolResult, auth: AuthContext) -> str:
        if not result.rows:
            return result.message or "Tôi chưa tìm thấy dữ liệu cá nhân phù hợp trong phạm vi đã xác thực."

        lines = []
        for index, row in enumerate(result.rows, start=1):
            date = row.get("appointment_date") or "chưa rõ ngày"
            start = row.get("start_time") or "chưa rõ giờ"
            patient = row.get("patient_name") or "chưa rõ bệnh nhân"
            doctor = row.get("doctor_name")
            service = row.get("service_name") or self._appointment_type_label(row.get("visit_type"))
            status = self._appointment_status_label(row.get("status"))
            parts = [f"{index}. {date} lúc {start}"]
            if auth.role == "patient":
                parts.append(f"Nội dung: {service}")
                parts.append(f"Trạng thái: {status}")
                if doctor:
                    parts.append(f"Bác sĩ: {doctor}")
                else:
                    parts.append("Bác sĩ: chưa có thông tin")
            else:
                parts.append(f"Bệnh nhân: {patient}")
                parts.append(f"Nội dung: {service}")
                parts.append(f"Trạng thái: {status}")
                if auth.role not in {"doctor"} and doctor:
                    parts.append(f"Bác sĩ: {doctor}")
            lines.append("\n   ".join(parts))

        return "Tôi tìm thấy lịch hẹn trong phạm vi đã xác thực:\n" + "\n".join(lines)

    def _appointment_type_label(self, value: str | None) -> str:
        labels = {
            "walk_in": "khám trực tiếp/walk-in",
            "scheduled": "lịch hẹn đã đặt",
            "follow_up": "tái khám",
            "consultation": "tư vấn/khám",
        }
        return labels.get(str(value or "").strip(), str(value or "chưa rõ dịch vụ"))

    def _appointment_status_label(self, value: str | None) -> str:
        labels = {
            "scheduled": "đã lên lịch",
            "arrived": "bệnh nhân đã đến",
            "in_progress": "đang xử lý/đang khám",
            "completed": "đã hoàn tất",
            "cancelled": "đã hủy",
            "no_show": "không đến",
        }
        return labels.get(str(value or "").strip(), str(value or "chưa rõ trạng thái"))

    def _lab_result_status_label(self, value: str | None) -> str:
        labels = {
            "ordered": "đã chỉ định",
            "collected": "đã lấy mẫu",
            "processing": "đang xử lý",
            "completed": "đã hoàn tất",
            "verified": "đã xác nhận",
            "cancelled": "đã hủy",
        }
        return labels.get(str(value or "").strip(), str(value or "chưa rõ trạng thái"))

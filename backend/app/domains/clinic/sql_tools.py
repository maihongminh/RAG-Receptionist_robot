import logging
from difflib import SequenceMatcher
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[4]
SCRIPTS_ROOT = PROJECT_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from app.config import get_settings
from app.rag.embedding_client import EmbeddingClient
from app.rag.qdrant_store import QdrantVectorStore
from app.rag.rag_config import get_rag_config
from app.core.schemas import AuthContext, ToolResult
from app.db import fetch_all
from rag_documents import load_rag_documents


logger = logging.getLogger(__name__)


class ClinicSqlTools:
    def get_public_profile(self, profile_query: str = "") -> ToolResult:
        rows = fetch_all(
            """
            SELECT
              c.id,
              c.name,
              c.phone,
              c.email,
              c.address,
              c.city,
              c.timezone,
              c.currency,
              s.working_hours_start::text AS working_hours_start,
              s.working_hours_end::text AS working_hours_end,
              s.lunch_break_start::text AS lunch_break_start,
              s.lunch_break_end::text AS lunch_break_end
            FROM robo_app.clinics c
            LEFT JOIN robo_app.clinic_settings s ON s.clinic_id = c.id
            WHERE c.status = 'active'
            ORDER BY c.name
            LIMIT 100
            """
        )
        ranked_rows = self._rank_rows(
            rows,
            profile_query,
            ["name", "city", "address"],
            min_score=0.45,
        )
        if profile_query:
            rows = ranked_rows[: get_rag_config().context_max_rows]
        return ToolResult(
            tool_name="clinic.get_public_profile",
            source="robo_app.clinics, robo_app.clinic_settings",
            rows=rows,
            confidence=0.85 if rows else 0.0,
        )

    def search_services(self, query: str) -> ToolResult:
        rag_config = get_rag_config()
        services = fetch_all(
            f"""
            SELECT
              id,
              code,
              name,
              name_en,
              category_name,
              price_amount,
              currency_code,
              duration_minutes,
              service_type
            FROM robo_app.services
            WHERE COALESCE(is_active, true) = true
            LIMIT {rag_config.sql_result_limit}
            """
        )
        rows = self._rank_service_rows(services, query)
        max_rows = rag_config.context_max_rows
        if self._is_specific_service_query(query, rows):
            rows = rows[:1]
        else:
            rows = rows[:max_rows]
        return ToolResult(
            tool_name="clinic.search_services",
            source="robo_app.services",
            rows=rows,
            confidence=rows[0].get("_score", 0.0) if rows else 0.0,
        )

    def list_service_categories(
        self,
        service_type: str = "all",
        offset: int | str | None = 0,
        display_limit: int | str | None = None,
    ) -> ToolResult:
        rag_config = get_rag_config()
        params: dict[str, Any] = {}
        service_type_clause = ""
        if service_type in {"lab", "imaging"}:
            service_type_clause = "AND service_type = %(service_type)s"
            params["service_type"] = service_type
        offset_value = self._safe_positive_int(offset, default=0)
        display_limit_value = self._safe_positive_int(display_limit, default=12)
        row_limit = min(display_limit_value, rag_config.api_preview_max_rows)

        rows = fetch_all(
            f"""
            SELECT
              service_type,
              COALESCE(NULLIF(category_name, ''), 'Chưa phân nhóm') AS category_name,
              COUNT(*)::integer AS service_count,
              MIN(price_amount) AS min_price,
              MAX(price_amount) AS max_price,
              currency_code
            FROM robo_app.services
            WHERE COALESCE(is_active, true) = true
              {service_type_clause}
            GROUP BY service_type, COALESCE(NULLIF(category_name, ''), 'Chưa phân nhóm'), currency_code
            ORDER BY service_type, category_name
            LIMIT 1000
            """,
            params,
        )
        total_categories = len(rows)
        rows = rows[offset_value : offset_value + row_limit]
        for index, row in enumerate(rows, start=offset_value + 1):
            row["total_categories"] = total_categories
            row["category_offset"] = offset_value
            row["display_limit"] = display_limit_value
            row["category_display_index"] = index
        return ToolResult(
            tool_name="clinic.list_service_categories",
            source="robo_app.services",
            rows=rows,
            confidence=0.85 if rows else 0.0,
        )

    def _safe_positive_int(self, value: int | str | None, default: int) -> int:
        try:
            parsed = int(value) if value is not None else default
        except (TypeError, ValueError):
            return default
        return parsed if parsed > 0 else default

    def summarize_service_catalog(
        self,
        service_type: str = "all",
        offset: int | str | None = 0,
        display_limit: int | str | None = None,
    ) -> ToolResult:
        rag_config = get_rag_config()
        params: dict[str, Any] = {}
        service_type_clause = ""
        if service_type in {"lab", "imaging"}:
            service_type_clause = "AND service_type = %(service_type)s"
            params["service_type"] = service_type
        offset_value = self._safe_positive_int(offset, default=0)
        display_limit_value = self._safe_positive_int(display_limit, default=10)
        row_limit = min(display_limit_value, rag_config.api_preview_max_rows)

        rows = fetch_all(
            f"""
            WITH grouped AS (
              SELECT
                service_type,
                COALESCE(NULLIF(category_name, ''), 'Chưa phân nhóm') AS category_name,
                COUNT(*)::integer AS service_count,
                MIN(price_amount) AS min_price,
                MAX(price_amount) AS max_price,
                currency_code
              FROM robo_app.services
              WHERE COALESCE(is_active, true) = true
                {service_type_clause}
              GROUP BY service_type, COALESCE(NULLIF(category_name, ''), 'Chưa phân nhóm'), currency_code
            )
            SELECT
              service_type,
              category_name,
              service_count,
              min_price,
              max_price,
              currency_code,
              SUM(service_count) OVER ()::integer AS total_services,
              COUNT(*) OVER ()::integer AS total_categories
            FROM grouped
            ORDER BY service_count DESC, service_type, category_name
            LIMIT %(limit)s OFFSET %(offset)s
            """,
            {**params, "limit": row_limit, "offset": offset_value},
        )
        for index, row in enumerate(rows, start=offset_value + 1):
            row["category_offset"] = offset_value
            row["display_limit"] = display_limit_value
            row["category_display_index"] = index
        return ToolResult(
            tool_name="clinic.summarize_service_catalog",
            source="robo_app.services",
            rows=rows,
            confidence=0.88 if rows else 0.0,
        )

    def list_services_by_category(self, category_query: str, service_type: str = "all") -> ToolResult:
        category_query = (category_query or "").strip()
        if not category_query:
            return ToolResult(
                tool_name="clinic.list_services_by_category",
                source="robo_app.services",
                rows=[],
                message="Chưa có tên nhóm dịch vụ để tra cứu.",
                confidence=0.0,
            )

        category = self._find_service_category(category_query, service_type)
        if not category:
            return ToolResult(
                tool_name="clinic.list_services_by_category",
                source="robo_app.services",
                rows=[],
                message=f"Không tìm thấy nhóm dịch vụ phù hợp với '{category_query}'.",
                confidence=0.0,
            )

        rag_config = get_rag_config()
        params: dict[str, Any] = {
            "category_name": category["category_name"],
            "limit": rag_config.api_preview_max_rows,
        }
        service_type_clause = ""
        if category.get("service_type"):
            service_type_clause = "AND service_type = %(service_type)s"
            params["service_type"] = category["service_type"]

        rows = fetch_all(
            f"""
            SELECT
              id,
              code,
              name,
              name_en,
              category_name,
              price_amount,
              currency_code,
              duration_minutes,
              service_type,
              COUNT(*) OVER ()::integer AS total_services_in_category
            FROM robo_app.services
            WHERE COALESCE(is_active, true) = true
              AND COALESCE(NULLIF(category_name, ''), 'Chưa phân nhóm') = %(category_name)s
              {service_type_clause}
            ORDER BY code, name
            LIMIT %(limit)s
            """,
            params,
        )
        for row in rows:
            row["matched_category_name"] = category["category_name"]
            row["matched_category_score"] = category.get("_score", 1.0)
        return ToolResult(
            tool_name="clinic.list_services_by_category",
            source="robo_app.services",
            rows=rows,
            confidence=category.get("_score", 0.88) if rows else 0.0,
        )

    def search_doctor_schedules(self, doctor_query: str, weekday: int | None = None) -> ToolResult:
        params: dict[str, Any] = {}
        weekday_clause = ""
        if weekday is not None:
            weekday_clause = "AND s.day_of_week = %(weekday)s"
            params["weekday"] = weekday

        schedules = fetch_all(
            f"""
            SELECT
              s.doctor_name,
              s.day_of_week,
              s.start_time::text AS start_time,
              s.end_time::text AS end_time,
              s.room_name,
              s.room_code,
              s.floor,
              s.notes
            FROM robo_app.doctor_schedules s
            WHERE COALESCE(s.is_active, true) = true
            {weekday_clause}
            ORDER BY s.doctor_name, s.day_of_week, s.start_time
            LIMIT {get_rag_config().sql_result_limit}
            """,
            params,
        )

        rows = self._rank_rows(schedules, doctor_query, ["doctor_name"], min_score=0.5)
        return ToolResult(
            tool_name="clinic.search_doctor_schedules",
            source="robo_app.doctor_schedules",
            rows=rows[: get_rag_config().context_max_rows],
            confidence=rows[0].get("_score", 0.0) if rows else 0.0,
        )

    def search_knowledge(self, query: str) -> ToolResult:
        rag_config = get_rag_config()
        vector_result = self._search_knowledge_vector(query)
        if vector_result.rows:
            vector_result.rows = self._rank_knowledge_rows(
                vector_result.rows,
                query,
                min_score=0.0,
            )[: rag_config.vector_top_k]
            vector_result.confidence = (
                vector_result.rows[0].get("_score", vector_result.confidence)
                if vector_result.rows
                else vector_result.confidence
            )
            return vector_result

        articles = [
            row
            for row in load_rag_documents()
            if row.get("access_level") == "public"
        ][: rag_config.keyword_source_limit]
        articles = self._filter_rag_rows(articles, rag_config)
        rows = self._rank_knowledge_rows(
            articles,
            query,
            min_score=rag_config.keyword_min_score,
        )
        return ToolResult(
            tool_name="clinic.search_knowledge",
            source="scripts/rag_documents.py",
            rows=rows[: rag_config.keyword_top_k],
            confidence=rows[0].get("_score", rag_config.empty_confidence)
            if rows
            else rag_config.empty_confidence,
        )

    def lookup_private_data(self, entities: dict[str, Any], auth: AuthContext) -> ToolResult:
        rows = self._lookup_appointments(auth)
        return ToolResult(
            tool_name="clinic.lookup_private_data",
            source="robo_app.appointments",
            rows=rows,
            message=None if rows else "Không tìm thấy lịch hẹn phù hợp trong phạm vi đã xác thực.",
            confidence=0.9 if rows else 0.0,
        )

    def lookup_lab_results(self, entities: dict[str, Any], auth: AuthContext) -> ToolResult:
        rows = self._lookup_paraclinical_results(auth)
        return ToolResult(
            tool_name="clinic.lookup_lab_results",
            source="robo_app.paraclinical_results",
            rows=rows,
            message=None if rows else "Không tìm thấy kết quả xét nghiệm/cận lâm sàng phù hợp trong phạm vi đã xác thực.",
            confidence=0.9 if rows else 0.0,
        )

    def lookup_patient_profile(self, entities: dict[str, Any], auth: AuthContext) -> ToolResult:
        rows = self._lookup_patient_profiles(auth, entities.get("patient_query", ""))
        return ToolResult(
            tool_name="clinic.lookup_patient_profile",
            source="robo_app.patients",
            rows=rows,
            message=None if rows else "Không tìm thấy hồ sơ bệnh nhân phù hợp trong phạm vi đã xác thực.",
            confidence=0.9 if rows else 0.0,
        )

    def _lookup_appointments(self, auth: AuthContext) -> list[dict[str, Any]]:
        where_clauses = []
        params: dict[str, Any] = {}

        if auth.role == "patient":
            where_clauses.append("patient_id = %(patient_id)s")
            params["patient_id"] = auth.patient_id
        elif auth.role == "doctor":
            where_clauses.append("doctor_id = %(doctor_id)s")
            params["doctor_id"] = auth.doctor_id
        elif auth.role in {"receptionist", "clinic_admin"}:
            where_clauses.append("clinic_id = %(clinic_id)s")
            params["clinic_id"] = auth.clinic_id
        else:
            return []

        if auth.clinic_id and auth.role in {"patient", "doctor"}:
            where_clauses.append("clinic_id = %(clinic_id)s")
            params["clinic_id"] = auth.clinic_id

        where_sql = " AND ".join(where_clauses)
        return fetch_all(
            f"""
            SELECT
              id,
              clinic_id,
              patient_id,
              patient_name,
              doctor_id,
              doctor_name,
              appointment_date::text AS appointment_date,
              start_time::text AS start_time,
              end_time::text AS end_time,
              visit_type,
              status,
              service_name,
              chief_complaint
            FROM robo_app.appointments
            WHERE {where_sql}
            ORDER BY appointment_date DESC NULLS LAST, start_time DESC NULLS LAST
            LIMIT 5
            """,
            params,
        )

    def _lookup_paraclinical_results(self, auth: AuthContext) -> list[dict[str, Any]]:
        where_clauses = []
        params: dict[str, Any] = {}

        if auth.role == "patient":
            where_clauses.append("patient_id = %(patient_id)s")
            params["patient_id"] = auth.patient_id
        elif auth.role in {"receptionist", "clinic_admin"}:
            where_clauses.append("clinic_id = %(clinic_id)s")
            params["clinic_id"] = auth.clinic_id
        elif auth.role == "doctor":
            where_clauses.append("ordered_by = %(doctor_id)s")
            params["doctor_id"] = auth.doctor_id
        else:
            return []

        where_sql = " AND ".join(where_clauses)
        return fetch_all(
            f"""
            SELECT
              id,
              clinic_id,
              patient_id,
              order_type,
              patient_name,
              order_type,
              service_code,
              service_name,
              service_category_name,
              status,
              priority,
              ordered_at::text AS ordered_at,
              collected_at::text AS collected_at,
              processed_at::text AS processed_at,
              completed_at::text AS completed_at,
              result_summary,
              result_file_url,
              has_result
            FROM robo_app.paraclinical_results
            WHERE {where_sql}
            ORDER BY
              COALESCE(completed_at, processed_at, collected_at, ordered_at) DESC NULLS LAST
            LIMIT 20
            """,
            params,
        )

    def _lookup_patient_profiles(self, auth: AuthContext, patient_query: str = "") -> list[dict[str, Any]]:
        where_clauses = []
        params: dict[str, Any] = {}

        if auth.role == "patient":
            where_clauses.append("id = %(patient_id)s")
            params["patient_id"] = auth.patient_id
        elif auth.role in {"receptionist", "clinic_admin"}:
            where_clauses.append("clinic_id = %(clinic_id)s")
            params["clinic_id"] = auth.clinic_id
        elif auth.role == "system_admin":
            where_clauses.append("TRUE")
        else:
            return []

        query = str(patient_query or "").strip()
        if query and auth.role in {"receptionist", "clinic_admin", "system_admin"}:
            where_clauses.append(
                """
                (
                  full_name ILIKE %(patient_query)s
                  OR patient_code ILIKE %(patient_query)s
                  OR phone_primary ILIKE %(patient_query)s
                  OR email ILIKE %(patient_query)s
                )
                """
            )
            params["patient_query"] = f"%{query}%"

        where_sql = " AND ".join(where_clauses)
        return fetch_all(
            f"""
            SELECT
              id,
              clinic_id,
              patient_code,
              full_name,
              date_of_birth::text AS date_of_birth,
              gender,
              phone_primary,
              phone_secondary,
              email,
              address,
              district,
              city,
              patient_category
            FROM robo_app.patients
            WHERE {where_sql}
            ORDER BY full_name, patient_code
            LIMIT {get_rag_config().context_max_rows}
            """,
            params,
        )

    def _search_knowledge_vector(self, query: str) -> ToolResult:
        settings = get_settings()
        rag_config = get_rag_config()
        if not settings.rag_vector_enabled:
            return ToolResult(
                tool_name="clinic.search_knowledge_vector",
                source="qdrant:disabled",
                rows=[],
                confidence=rag_config.empty_confidence,
            )

        try:
            embedding = EmbeddingClient().embed_text(query)
            if not embedding:
                return ToolResult(
                    tool_name="clinic.search_knowledge_vector",
                    source="qdrant:no_embedding",
                    rows=[],
                    confidence=rag_config.empty_confidence,
                )
            rows = QdrantVectorStore().search(
                query_vector=embedding,
                limit=rag_config.vector_top_k,
                score_threshold=rag_config.vector_min_score,
            )
            rows = self._filter_rag_rows(rows, rag_config)
        except Exception as exc:
            logger.warning("Qdrant knowledge search failed; using keyword fallback: %s", exc)
            return ToolResult(
                tool_name="clinic.search_knowledge_vector",
                source="qdrant:error",
                rows=[],
                confidence=rag_config.empty_confidence,
            )

        return ToolResult(
            tool_name="clinic.search_knowledge_vector",
            source=f"qdrant:{settings.qdrant_collection}",
            rows=rows,
            confidence=rows[0].get("_score", rag_config.empty_confidence)
            if rows
            else rag_config.empty_confidence,
        )

    def _filter_rag_rows(self, rows: list[dict[str, Any]], rag_config: Any) -> list[dict[str, Any]]:
        excluded_topics = {
            str(topic).strip().lower()
            for topic in getattr(rag_config, "excluded_topics", ())
            if str(topic).strip()
        }
        if not excluded_topics:
            return rows
        return [
            row
            for row in rows
            if str(row.get("topic") or "").strip().lower() not in excluded_topics
        ]

    def _find_service_category(self, category_query: str, service_type: str = "all") -> dict[str, Any] | None:
        params: dict[str, Any] = {}
        service_type_clause = ""
        if service_type in {"lab", "imaging"}:
            service_type_clause = "AND service_type = %(service_type)s"
            params["service_type"] = service_type

        categories = fetch_all(
            f"""
            SELECT
              service_type,
              COALESCE(NULLIF(category_name, ''), 'Chưa phân nhóm') AS category_name,
              COUNT(*)::integer AS service_count,
              MIN(price_amount) AS min_price,
              MAX(price_amount) AS max_price,
              currency_code
            FROM robo_app.services
            WHERE COALESCE(is_active, true) = true
              {service_type_clause}
            GROUP BY service_type, COALESCE(NULLIF(category_name, ''), 'Chưa phân nhóm'), currency_code
            ORDER BY service_type, category_name
            LIMIT {get_rag_config().sql_result_limit}
            """,
            params,
        )
        category = self._match_service_category(categories, category_query)
        if category:
            return category

        ranked = self._rank_rows(
            categories,
            category_query,
            ["category_name", "service_type"],
            min_score=0.45,
        )
        return ranked[0] if ranked else None

    def _match_service_category(
        self,
        categories: list[dict[str, Any]],
        category_query: str,
    ) -> dict[str, Any] | None:
        normalized_query = self._normalize(category_query)
        if not normalized_query:
            return None

        if normalized_query.isdigit():
            display_index = int(normalized_query)
            if 1 <= display_index <= len(categories):
                matched = dict(categories[display_index - 1])
                matched["_score"] = 1.0
                return matched

        for category in categories:
            if self._normalize(str(category.get("category_name") or "")) == normalized_query:
                matched = dict(category)
                matched["_score"] = 1.0
                return matched
        return None

    def _rank_knowledge_rows(
        self,
        rows: list[dict[str, Any]],
        query: str,
        min_score: float = 0.18,
    ) -> list[dict[str, Any]]:
        normalized_query = self._normalize(query)
        if not normalized_query:
            return rows

        ranked = []
        for row in rows:
            title_text = " ".join(
                str(row.get(field) or "") for field in ["topic", "title", "title_vi"]
            )
            content_text = " ".join(
                str(row.get(field) or "") for field in ["content", "content_vi"]
            )
            title_score = self._score(normalized_query, title_text)
            content_score = self._score(normalized_query, content_text)
            boost = self._knowledge_title_boost(normalized_query, title_text)
            score = max(content_score, min(1.0, title_score + boost))
            if score >= min_score:
                item = dict(row)
                item["_score"] = round(score, 3)
                ranked.append(item)

        return sorted(ranked, key=lambda item: item["_score"], reverse=True)

    def _knowledge_title_boost(self, normalized_query: str, title_text: str) -> float:
        normalized_title = self._normalize(title_text)
        boost = 0.0
        important_terms = ("check-in", "checkin", "tiếp nhận", "tiep nhan", "trả kết quả", "tra ket qua")
        for term in important_terms:
            if term in normalized_query and term in normalized_title:
                boost += 0.35
        return min(boost, 0.5)

    def _rank_rows(
        self,
        rows: list[dict[str, Any]],
        query: str,
        fields: list[str],
        min_score: float = 0.25,
    ) -> list[dict[str, Any]]:
        normalized_query = self._normalize(query)
        if not normalized_query:
            return rows

        ranked = []
        for row in rows:
            haystack = " ".join(str(row.get(field) or "") for field in fields)
            score = self._score(normalized_query, haystack)
            if score >= min_score:
                item = dict(row)
                item["_score"] = round(score, 3)
                ranked.append(item)

        return sorted(ranked, key=lambda item: item["_score"], reverse=True)

    def _rank_service_rows(self, rows: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
        normalized_query = self._normalize(query)
        if not normalized_query:
            return rows

        ranked = []
        category_terms = self._service_category_terms(normalized_query)
        for row in rows:
            haystack = " ".join(
                str(row.get(field) or "")
                for field in ["name", "name_en", "code", "category_name", "service_type"]
            )
            base_score = self._score(normalized_query, haystack)
            boost = self._service_category_boost(row, category_terms)
            score = max(base_score, boost)
            if score >= 0.25:
                item = dict(row)
                item["_score"] = round(score, 3)
                ranked.append(item)

        category_ranked = [
            item for item in ranked if self._service_category_boost(item, category_terms) > 0
        ]
        if category_ranked:
            ranked = category_ranked

        return sorted(
            ranked,
            key=lambda item: (
                -float(item["_score"]),
                -self._service_category_boost(item, category_terms),
                str(item.get("code") or ""),
            ),
        )

    def _service_category_terms(self, normalized_query: str) -> set[str]:
        terms = set(normalized_query.split())
        if "x-ray" in normalized_query or "xray" in normalized_query or "x quang" in normalized_query:
            terms.add("xray")
        if "siêu âm" in normalized_query or "sieu am" in normalized_query or "ultrasound" in normalized_query:
            terms.add("ultrasound")
        if "nội soi" in normalized_query or "noi soi" in normalized_query or "endoscopy" in normalized_query:
            terms.add("endoscopy")
        return terms

    def _service_category_boost(self, row: dict[str, Any], category_terms: set[str]) -> float:
        code = self._normalize(str(row.get("code") or ""))
        name = self._normalize(str(row.get("name") or ""))
        category = self._normalize(str(row.get("category_name") or ""))

        if "ct" in category_terms and (
            code.startswith("ct") or "ct scan" in category or name.startswith("ct ")
        ):
            return 0.92
        if {"mri", "mr"} & category_terms and (
            code.startswith("mr") or "mri" in category or name.startswith("mri ")
        ):
            return 0.92
        if "xray" in category_terms and (
            code.startswith("xr") or "x-ray" in category or "x-ray" in name
        ):
            return 0.92
        if "ultrasound" in category_terms and (
            code.startswith("us") or "ultrasound" in category or "ultrasound" in name
        ):
            return 0.92
        if "endoscopy" in category_terms and (
            code.startswith("ed") or "endoscopy" in category or "endoscopy" in name
        ):
            return 0.92
        return 0.0

    def _is_specific_service_query(self, query: str, rows: list[dict[str, Any]]) -> bool:
        if not rows:
            return False
        normalized_query = self._normalize(query)
        top = rows[0]
        top_code = self._normalize(str(top.get("code") or ""))
        top_name = self._normalize(str(top.get("name") or ""))
        top_name_en = self._normalize(str(top.get("name_en") or ""))
        if normalized_query == top_code:
            return True
        if normalized_query in {top_name, top_name_en}:
            return True
        query_tokens = normalized_query.split()
        return len(query_tokens) >= 3 and normalized_query in top_name

    def _score(self, query: str, text: str) -> float:
        normalized_text = self._normalize(text)
        if not normalized_text:
            return 0.0
        if query in normalized_text:
            return 1.0

        query_tokens = set(query.split())
        text_tokens = set(normalized_text.split())
        overlap = len(query_tokens & text_tokens) / max(len(query_tokens), 1)
        fuzzy = SequenceMatcher(None, query, normalized_text).ratio()
        return max(overlap, fuzzy)

    def _normalize(self, value: str) -> str:
        return " ".join(value.lower().strip().split())

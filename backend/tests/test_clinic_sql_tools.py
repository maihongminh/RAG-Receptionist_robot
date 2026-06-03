from app.core.schemas import AuthContext, ToolResult
from app.domains.clinic import sql_tools
from app.domains.clinic.sql_tools import ClinicSqlTools


def test_public_profile_returns_all_active_clinics_for_generic_question(monkeypatch):
    tool = ClinicSqlTools()
    calls = {}

    def fake_fetch_all(query):
        calls["query"] = query
        return [
            {"name": "BIOMEDIC DIAGNOSTIC CENTER", "address": "No.55", "city": "Phnom Penh"},
            {"name": "Phòng Khám Đa Khoa Mẫu", "address": "123 Nguyễn Huệ", "city": "Hồ Chí Minh"},
        ]

    monkeypatch.setattr(sql_tools, "fetch_all", fake_fetch_all)

    result = tool.get_public_profile("")

    assert "LIMIT 100" in calls["query"]
    assert [row["name"] for row in result.rows] == [
        "BIOMEDIC DIAGNOSTIC CENTER",
        "Phòng Khám Đa Khoa Mẫu",
    ]


def test_public_profile_filters_specific_clinic_name(monkeypatch):
    tool = ClinicSqlTools()

    monkeypatch.setattr(
        sql_tools,
        "fetch_all",
        lambda query: [
            {"name": "BIOMEDIC DIAGNOSTIC CENTER", "address": "No.55", "city": "Phnom Penh"},
            {"name": "Phòng Khám Đa Khoa Mẫu", "address": "123 Nguyễn Huệ", "city": "Hồ Chí Minh"},
        ],
    )

    result = tool.get_public_profile("Đa Khoa Mẫu")

    assert len(result.rows) == 1
    assert result.rows[0]["name"] == "Phòng Khám Đa Khoa Mẫu"


def test_search_services_prefers_ct_category_for_generic_ct_query(monkeypatch):
    tool = ClinicSqlTools()

    monkeypatch.setattr(
        sql_tools,
        "fetch_all",
        lambda query: [
            {
                "code": "MR005",
                "name": "MRI Abdomen with contrast",
                "category_name": "MRI",
                "price_amount": 380000,
                "currency_code": "USD",
                "service_type": "imaging",
            },
            {
                "code": "CT006",
                "name": "CT Abdomen with contrast",
                "category_name": "CT Scan",
                "price_amount": 210000,
                "currency_code": "USD",
                "service_type": "imaging",
            },
            {
                "code": "CT001",
                "name": "CT Brain without contrast",
                "category_name": "CT Scan",
                "price_amount": 120000,
                "currency_code": "USD",
                "service_type": "imaging",
            },
        ],
    )

    result = tool.search_services("ct")

    assert len(result.rows) == 2
    assert [row["code"] for row in result.rows] == ["CT001", "CT006"]


def test_search_services_returns_single_row_for_specific_service_name(monkeypatch):
    tool = ClinicSqlTools()

    monkeypatch.setattr(
        sql_tools,
        "fetch_all",
        lambda query: [
            {
                "code": "CT001",
                "name": "CT Brain without contrast",
                "category_name": "CT Scan",
                "price_amount": 120000,
                "currency_code": "USD",
                "service_type": "imaging",
            },
            {
                "code": "CT002",
                "name": "CT Brain with contrast",
                "category_name": "CT Scan",
                "price_amount": 180000,
                "currency_code": "USD",
                "service_type": "imaging",
            },
        ],
    )

    result = tool.search_services("CT Brain without contrast")

    assert len(result.rows) == 1
    assert result.rows[0]["code"] == "CT001"


def test_search_services_returns_single_row_for_exact_short_name(monkeypatch):
    tool = ClinicSqlTools()

    monkeypatch.setattr(
        sql_tools,
        "fetch_all",
        lambda query: [
            {
                "code": "LAB468",
                "name": "TIBC",
                "name_en": "TIBC",
                "category_name": "Check Liver Function",
                "price_amount": 6.25,
                "currency_code": "USD",
                "service_type": "lab",
            },
            {
                "code": "LFT006",
                "name": "Protein",
                "name_en": "Protein",
                "category_name": "Check Liver Function",
                "price_amount": 1.0,
                "currency_code": "USD",
                "service_type": "lab",
            },
        ],
    )

    result = tool.search_services("TIBC")

    assert len(result.rows) == 1
    assert result.rows[0]["code"] == "LAB468"


def test_list_service_categories_filters_lab(monkeypatch):
    tool = ClinicSqlTools()
    calls = {}

    def fake_fetch_all(query, params):
        calls["query"] = query
        calls["params"] = params
        return [
            {
                "service_type": "lab",
                "category_name": "Check Liver Function",
                "service_count": 10,
                "min_price": 1.0,
                "max_price": 6.25,
                "currency_code": "USD",
            }
        ]

    monkeypatch.setattr(sql_tools, "fetch_all", fake_fetch_all)

    result = tool.list_service_categories("lab")

    assert calls["params"] == {"service_type": "lab"}
    assert result.tool_name == "clinic.list_service_categories"
    assert result.rows[0]["category_name"] == "Check Liver Function"


def test_list_service_categories_supports_remaining_offset(monkeypatch):
    tool = ClinicSqlTools()

    def fake_fetch_all(query, params):
        return [
            {
                "service_type": "lab",
                "category_name": f"Group {index}",
                "service_count": index,
                "min_price": 1.0,
                "max_price": 2.0,
                "currency_code": "USD",
            }
            for index in range(1, 16)
        ]

    monkeypatch.setattr(sql_tools, "fetch_all", fake_fetch_all)

    result = tool.list_service_categories("lab", offset=12, display_limit=24)

    assert [row["category_name"] for row in result.rows] == ["Group 13", "Group 14", "Group 15"]
    assert result.rows[0]["total_categories"] == 15
    assert result.rows[0]["category_offset"] == 12
    assert result.rows[0]["display_limit"] == 24


def test_summarize_service_catalog_returns_group_totals(monkeypatch):
    tool = ClinicSqlTools()
    calls = {}

    def fake_fetch_all(query, params):
        calls["query"] = query
        calls["params"] = params
        return [
            {
                "service_type": "lab",
                "category_name": "Blood test",
                "service_count": 12,
                "min_price": 2.0,
                "max_price": 5.0,
                "currency_code": "USD",
                "total_services": 20,
                "total_categories": 2,
            }
        ]

    monkeypatch.setattr(sql_tools, "fetch_all", fake_fetch_all)

    result = tool.summarize_service_catalog("all")

    assert "SUM(service_count) OVER" in calls["query"]
    assert "limit" in calls["params"]
    assert result.tool_name == "clinic.summarize_service_catalog"
    assert result.rows[0]["total_services"] == 20
    assert result.rows[0]["category_display_index"] == 1


def test_summarize_service_catalog_supports_offset(monkeypatch):
    tool = ClinicSqlTools()
    calls = {}

    def fake_fetch_all(query, params):
        calls["query"] = query
        calls["params"] = params
        return [
            {
                "service_type": "lab",
                "category_name": "Group 11",
                "service_count": 5,
                "min_price": 1.0,
                "max_price": 2.0,
                "currency_code": "USD",
                "total_services": 50,
                "total_categories": 12,
            }
        ]

    monkeypatch.setattr(sql_tools, "fetch_all", fake_fetch_all)

    result = tool.summarize_service_catalog("all", offset=10, display_limit=10)

    assert calls["params"]["offset"] == 10
    assert calls["params"]["limit"] == 10
    assert result.rows[0]["category_offset"] == 10
    assert result.rows[0]["category_display_index"] == 11


def test_list_services_by_category_matches_category_then_lists_services(monkeypatch):
    tool = ClinicSqlTools()
    calls = []

    def fake_fetch_all(query, params=None):
        calls.append((query, params or {}))
        if "GROUP BY service_type" in query:
            return [
                {
                    "service_type": "imaging",
                    "category_name": "CT Scan",
                    "service_count": 2,
                    "min_price": 120000,
                    "max_price": 180000,
                    "currency_code": "USD",
                },
                {
                    "service_type": "imaging",
                    "category_name": "MRI",
                    "service_count": 1,
                    "min_price": 250000,
                    "max_price": 250000,
                    "currency_code": "USD",
                },
            ]
        return [
            {
                "code": "CT001",
                "name": "CT Brain without contrast",
                "category_name": "CT Scan",
                "price_amount": 120000,
                "currency_code": "USD",
                "duration_minutes": 30,
                "service_type": "imaging",
                "total_services_in_category": 2,
            }
        ]

    monkeypatch.setattr(sql_tools, "fetch_all", fake_fetch_all)

    result = tool.list_services_by_category("CT Scan", "imaging")

    assert result.tool_name == "clinic.list_services_by_category"
    assert result.rows[0]["code"] == "CT001"
    assert result.rows[0]["matched_category_name"] == "CT Scan"
    assert calls[-1][1]["category_name"] == "CT Scan"


def test_list_services_by_category_can_match_numeric_category_index(monkeypatch):
    tool = ClinicSqlTools()
    calls = []

    def fake_fetch_all(query, params=None):
        calls.append((query, params or {}))
        if "GROUP BY service_type" in query:
            return [
                {
                    "service_type": "lab",
                    "category_name": "Blood test",
                    "service_count": 4,
                    "min_price": 2.0,
                    "max_price": 5.0,
                    "currency_code": "USD",
                },
                {
                    "service_type": "lab",
                    "category_name": "Check Liver Function",
                    "service_count": 6,
                    "min_price": 1.0,
                    "max_price": 3.0,
                    "currency_code": "USD",
                },
            ]
        return [
            {
                "code": "LFT001",
                "name": "ALT",
                "category_name": "Check Liver Function",
                "price_amount": 1.5,
                "currency_code": "USD",
                "duration_minutes": 30,
                "service_type": "lab",
                "total_services_in_category": 1,
            }
        ]

    monkeypatch.setattr(sql_tools, "fetch_all", fake_fetch_all)

    result = tool.list_services_by_category("2", "lab")

    assert result.rows[0]["matched_category_name"] == "Check Liver Function"
    assert calls[-1][1]["category_name"] == "Check Liver Function"


def test_list_services_by_category_matches_exact_lowercase_category(monkeypatch):
    tool = ClinicSqlTools()

    def fake_fetch_all(query, params=None):
        if "GROUP BY service_type" in query:
            return [
                {
                    "service_type": "lab",
                    "category_name": "check for insects in the blood",
                    "service_count": 2,
                    "min_price": 2.0,
                    "max_price": 7.5,
                    "currency_code": "USD",
                }
            ]
        return [
            {
                "code": "PAR001",
                "name": "CBC",
                "category_name": "check for insects in the blood",
                "price_amount": 2.0,
                "currency_code": "USD",
                "duration_minutes": 30,
                "service_type": "lab",
                "total_services_in_category": 2,
            }
        ]

    monkeypatch.setattr(sql_tools, "fetch_all", fake_fetch_all)

    result = tool.list_services_by_category("check for insects in the blood", "all")

    assert result.rows[0]["matched_category_name"] == "check for insects in the blood"
    assert result.confidence == 1.0


def test_lookup_lab_results_filters_patient_scope(monkeypatch):
    tool = ClinicSqlTools()
    calls = {}

    def fake_fetch_all(query, params):
        calls["query"] = query
        calls["params"] = params
        return [
            {
                "service_name": "CBC",
                "status": "collected",
                "has_result": False,
            }
        ]

    monkeypatch.setattr(sql_tools, "fetch_all", fake_fetch_all)

    result = tool.lookup_lab_results({}, AuthContext(role="patient", patient_id="patient-1"))

    assert calls["params"] == {"patient_id": "patient-1"}
    assert "patient_id = %(patient_id)s" in calls["query"]
    assert result.tool_name == "clinic.lookup_lab_results"
    assert result.rows[0]["service_name"] == "CBC"


def test_lookup_patient_profile_filters_patient_scope(monkeypatch):
    tool = ClinicSqlTools()
    calls = {}

    def fake_fetch_all(query, params):
        calls["query"] = query
        calls["params"] = params
        return [
            {
                "id": "patient-1",
                "patient_code": "PT-001",
                "full_name": "Nguyễn Văn A",
                "phone_primary": "0900000001",
            }
        ]

    monkeypatch.setattr(sql_tools, "fetch_all", fake_fetch_all)

    result = tool.lookup_patient_profile({}, AuthContext(role="patient", patient_id="patient-1"))

    assert calls["params"] == {"patient_id": "patient-1"}
    assert "id = %(patient_id)s" in calls["query"]
    assert result.tool_name == "clinic.lookup_patient_profile"
    assert result.source == "robo_app.patients"
    assert result.rows[0]["patient_code"] == "PT-001"


def test_lookup_patient_profile_filters_clinic_admin_query(monkeypatch):
    tool = ClinicSqlTools()
    calls = {}

    def fake_fetch_all(query, params):
        calls["query"] = query
        calls["params"] = params
        return [
            {
                "id": "patient-1",
                "patient_code": "PT-001",
                "full_name": "Nguyễn Văn A",
            }
        ]

    monkeypatch.setattr(sql_tools, "fetch_all", fake_fetch_all)

    result = tool.lookup_patient_profile(
        {"patient_query": "Nguyễn"},
        AuthContext(role="clinic_admin", clinic_id="clinic-1"),
    )

    assert calls["params"] == {"clinic_id": "clinic-1", "patient_query": "%Nguyễn%"}
    assert "clinic_id = %(clinic_id)s" in calls["query"]
    assert "full_name ILIKE %(patient_query)s" in calls["query"]
    assert result.rows[0]["full_name"] == "Nguyễn Văn A"


def test_lookup_patient_profile_allows_system_admin_query(monkeypatch):
    tool = ClinicSqlTools()
    calls = {}

    def fake_fetch_all(query, params):
        calls["query"] = query
        calls["params"] = params
        return [
            {
                "id": "patient-1",
                "patient_code": "PT-001",
                "full_name": "Nguyễn Văn A",
            }
        ]

    monkeypatch.setattr(sql_tools, "fetch_all", fake_fetch_all)

    result = tool.lookup_patient_profile(
        {"patient_query": "PT-001"},
        AuthContext(role="system_admin"),
    )

    assert calls["params"] == {"patient_query": "%PT-001%"}
    assert "clinic_id = %(clinic_id)s" not in calls["query"]
    assert "patient_code ILIKE %(patient_query)s" in calls["query"]
    assert result.rows[0]["patient_code"] == "PT-001"


def test_search_knowledge_prefers_qdrant_vector_rows(monkeypatch):
    tool = ClinicSqlTools()

    monkeypatch.setattr(
        tool,
        "_search_knowledge_vector",
        lambda query: ToolResult(
            tool_name="clinic.search_knowledge_vector",
            source="qdrant:clinic_knowledge",
            rows=[
                {
                    "title_vi": "Tiếp nhận & Check-in",
                    "content_vi": "Bệnh nhân đến quầy tiếp nhận để xác nhận lịch hẹn.",
                    "_score": 0.91,
                }
            ],
            confidence=0.91,
        ),
    )

    result = tool.search_knowledge("quy trình check-in")

    assert result.tool_name == "clinic.search_knowledge_vector"
    assert result.source == "qdrant:clinic_knowledge"
    assert result.rows[0]["title_vi"] == "Tiếp nhận & Check-in"


def test_search_knowledge_falls_back_to_keyword_rows(monkeypatch):
    tool = ClinicSqlTools()

    monkeypatch.setattr(
        tool,
        "_search_knowledge_vector",
        lambda query: ToolResult(
            tool_name="clinic.search_knowledge_vector",
            source="qdrant:empty",
            rows=[],
            confidence=0.0,
        ),
    )
    monkeypatch.setattr(
        sql_tools,
        "load_rag_documents",
        lambda: [
            {
                "source_table": "admin_help_templates",
                "source_id": "article-1",
                "topic": "check-in",
                "title": "Reception",
                "title_vi": "Tiếp nhận",
                "content": "Check-in patient.",
                "content_vi": "Quy trình check-in bệnh nhân tại quầy tiếp nhận.",
                "document_type": "knowledge_article",
                "access_level": "public",
            }
        ],
    )

    result = tool.search_knowledge("quy trình check-in")

    assert result.tool_name == "clinic.search_knowledge"
    assert result.source == "scripts/rag_documents.py"
    assert result.rows[0]["title_vi"] == "Tiếp nhận"


def test_search_knowledge_excludes_platform_topics(monkeypatch):
    tool = ClinicSqlTools()

    monkeypatch.setattr(
        tool,
        "_search_knowledge_vector",
        lambda query: ToolResult(
            tool_name="clinic.search_knowledge_vector",
            source="qdrant:empty",
            rows=[],
            confidence=0.0,
        ),
    )
    monkeypatch.setattr(
        sql_tools,
        "load_rag_documents",
        lambda: [
            {
                "source_table": "admin_help_templates",
                "source_id": "overview-1",
                "topic": "overview",
                "title": "System Overview",
                "title_vi": "Tổng quan hệ thống",
                "content": "SmartClinic platform overview.",
                "content_vi": "SmartClinic là nền tảng quản lý phòng khám.",
                "document_type": "knowledge_article",
                "access_level": "public",
            },
            {
                "source_table": "admin_help_templates",
                "source_id": "reception-1",
                "topic": "reception",
                "title": "Reception",
                "title_vi": "Tiếp nhận",
                "content": "Check-in patient.",
                "content_vi": "Quy trình tiếp nhận bệnh nhân tại quầy.",
                "document_type": "knowledge_article",
                "access_level": "public",
            },
        ],
    )

    result = tool.search_knowledge("quy trình tiếp nhận SmartClinic")

    assert result.rows
    assert {row["topic"] for row in result.rows} == {"reception"}


def test_vector_search_uses_rag_config(monkeypatch):
    calls = {}
    tool = ClinicSqlTools()

    class FakeSettings:
        rag_vector_enabled = True
        qdrant_collection = "clinic_knowledge"

    class FakeRagConfig:
        vector_top_k = 7
        vector_min_score = 0.66
        empty_confidence = 0.0

    class FakeEmbeddingClient:
        def embed_text(self, query):
            return [0.1, 0.2, 0.3]

    class FakeQdrantVectorStore:
        def search(self, query_vector, limit, score_threshold):
            calls["query_vector"] = query_vector
            calls["limit"] = limit
            calls["score_threshold"] = score_threshold
            return [{"title_vi": "RAG", "content_vi": "Context", "_score": 0.77}]

    monkeypatch.setattr(sql_tools, "get_settings", lambda: FakeSettings())
    monkeypatch.setattr(sql_tools, "get_rag_config", lambda: FakeRagConfig())
    monkeypatch.setattr(sql_tools, "EmbeddingClient", FakeEmbeddingClient)
    monkeypatch.setattr(sql_tools, "QdrantVectorStore", FakeQdrantVectorStore)

    result = tool._search_knowledge_vector("quy trình")

    assert calls == {
        "query_vector": [0.1, 0.2, 0.3],
        "limit": 7,
        "score_threshold": 0.66,
    }
    assert result.confidence == 0.77


def test_lookup_private_data_filters_patient_appointments(monkeypatch):
    calls = {}
    tool = ClinicSqlTools()

    def fake_fetch_all(query, params):
        calls["query"] = query
        calls["params"] = params
        return [
            {
                "id": "appointment-1",
                "patient_id": "patient-1",
                "appointment_date": "2026-04-24",
                "start_time": "08:00:00",
                "doctor_name": "SUON SAVUTH",
                "status": "scheduled",
            }
        ]

    monkeypatch.setattr(sql_tools, "fetch_all", fake_fetch_all)

    result = tool.lookup_private_data({}, AuthContext(role="patient", patient_id="patient-1"))

    assert calls["params"] == {"patient_id": "patient-1"}
    assert "patient_id = %(patient_id)s" in calls["query"]
    assert result.source == "robo_app.appointments"
    assert result.rows[0]["id"] == "appointment-1"


def test_lookup_patient_timeline_combines_patient_events(monkeypatch):
    calls = []
    tool = ClinicSqlTools()

    def fake_fetch_all(query, params=None):
        calls.append((query, params or {}))
        if "FROM robo_app.patients" in query:
            return [{"id": "patient-1", "full_name": "Nguyễn Văn A"}]
        if "FROM robo_app.appointments" in query:
            return [
                {
                    "event_type": "appointment",
                    "event_at": "2026-04-24 08:00:00",
                    "id": "appointment-1",
                    "patient_id": "patient-1",
                    "patient_name": "Nguyễn Văn A",
                    "service_name": "Khám tổng quát",
                    "status": "scheduled",
                }
            ]
        if "FROM robo_app.paraclinical_results" in query:
            return [
                {
                    "event_type": "paraclinical_result",
                    "event_at": "2026-04-25 09:00:00+00",
                    "id": "lab-1",
                    "patient_id": "patient-1",
                    "patient_name": "Nguyễn Văn A",
                    "service_name": "Glucose",
                    "status": "completed",
                    "has_result": True,
                    "result_summary": "Normal",
                }
            ]
        return []

    monkeypatch.setattr(sql_tools, "fetch_all", fake_fetch_all)

    result = tool.lookup_patient_timeline({}, AuthContext(role="patient", patient_id="patient-1"))

    assert result.tool_name == "clinic.lookup_patient_timeline"
    assert result.source == "robo_app.appointments, robo_app.paraclinical_results"
    assert len(result.rows) == 2
    assert result.rows[0]["event_type"] == "paraclinical_result"
    assert calls[1][1]["patient_ids"] == ["patient-1"]
    assert calls[1][1]["patient_id"] == "patient-1"


def test_lookup_patient_timeline_requires_query_for_clinic_admin(monkeypatch):
    tool = ClinicSqlTools()

    def fake_fetch_all(query, params=None):
        raise AssertionError("timeline should not query broad clinic data without patient_query")

    monkeypatch.setattr(sql_tools, "fetch_all", fake_fetch_all)

    result = tool.lookup_patient_timeline({}, AuthContext(role="clinic_admin", clinic_id="clinic-1"))

    assert result.rows == []
    assert "nêu tên" in result.message


def test_lookup_visit_summary_filters_patient_scope(monkeypatch):
    calls = {}
    tool = ClinicSqlTools()

    def fake_fetch_all(query, params):
        calls["query"] = query
        calls["params"] = params
        return [
            {
                "medical_record_id": "record-1",
                "patient_id": "patient-1",
                "patient_name": "Nguyễn Văn A",
                "chief_complaint": "Đau đầu nhẹ",
                "confirmed_diagnosis": "Theo dõi đau đầu",
            }
        ]

    monkeypatch.setattr(sql_tools, "fetch_all", fake_fetch_all)

    result = tool.lookup_visit_summary({}, AuthContext(role="patient", patient_id="patient-1"))

    assert calls["params"] == {"patient_id": "patient-1"}
    assert "patient_id = %(patient_id)s" in calls["query"]
    assert result.tool_name == "clinic.lookup_visit_summary"
    assert result.source == "robo_app.patient_visit_summaries"
    assert result.rows[0]["chief_complaint"] == "Đau đầu nhẹ"


def test_lookup_visit_summary_requires_query_for_doctor(monkeypatch):
    tool = ClinicSqlTools()

    def fake_fetch_all(query, params=None):
        raise AssertionError("doctor visit summary should require patient_query")

    monkeypatch.setattr(sql_tools, "fetch_all", fake_fetch_all)

    result = tool.lookup_visit_summary({}, AuthContext(role="doctor", doctor_id="doctor-1"))

    assert result.rows == []
    assert "nêu tên" in result.message


def test_lookup_visit_summary_filters_doctor_and_patient_query(monkeypatch):
    calls = {}
    tool = ClinicSqlTools()

    def fake_fetch_all(query, params):
        calls["query"] = query
        calls["params"] = params
        return [
            {
                "medical_record_id": "record-1",
                "patient_name": "Nguyễn Văn A",
            }
        ]

    monkeypatch.setattr(sql_tools, "fetch_all", fake_fetch_all)

    result = tool.lookup_visit_summary(
        {"patient_query": "Nguyễn"},
        AuthContext(role="doctor", doctor_id="doctor-1"),
    )

    assert calls["params"] == {"doctor_id": "doctor-1", "patient_query": "%Nguyễn%"}
    assert "doctor_id = %(doctor_id)s" in calls["query"]
    assert "patient_name ILIKE %(patient_query)s" in calls["query"]
    assert result.rows[0]["patient_name"] == "Nguyễn Văn A"


def test_lookup_billing_summary_filters_patient_scope(monkeypatch):
    calls = {}
    tool = ClinicSqlTools()

    def fake_fetch_all(query, params):
        calls["query"] = query
        calls["params"] = params
        return [
            {
                "invoice_number": "HD-001",
                "patient_id": "patient-1",
                "payment_status": "paid",
                "total_amount": 25,
                "paid_amount": 25,
                "balance_amount": 0,
                "currency_code": "USD",
            }
        ]

    monkeypatch.setattr(sql_tools, "fetch_all", fake_fetch_all)

    result = tool.lookup_billing_summary({}, AuthContext(role="patient", patient_id="patient-1"))

    assert calls["params"] == {"patient_id": "patient-1"}
    assert "patient_id = %(patient_id)s" in calls["query"]
    assert result.tool_name == "clinic.lookup_billing_summary"
    assert result.source == "robo_app.billing_records"
    assert result.rows[0]["invoice_number"] == "HD-001"


def test_lookup_billing_summary_requires_query_for_clinic_admin(monkeypatch):
    tool = ClinicSqlTools()

    def fake_fetch_all(query, params=None):
        raise AssertionError("billing lookup should not query broad clinic data without patient_query")

    monkeypatch.setattr(sql_tools, "fetch_all", fake_fetch_all)

    result = tool.lookup_billing_summary({}, AuthContext(role="clinic_admin", clinic_id="clinic-1"))

    assert result.rows == []
    assert "nêu tên" in result.message

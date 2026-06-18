#!/usr/bin/env python3
"""Run MVP chatbot scenarios through the FastAPI /ask endpoint.

This is a lightweight regression runner for manual MVP validation. It checks
intent routing, source selection and a few must-have answer/data fragments.
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

DEMO_ACCOUNTS_BY_ROLE = {
    "patient": ("patient.demo@robo.local", "demo123"),
    "doctor": ("doctor@clinic.local", "demo123"),
    "receptionist": ("receptionist@clinic.local", "demo123"),
    "clinic_admin": ("admin@clinic.local", "demo123"),
    "system_admin": ("system.admin@robo.local", "demo123"),
}


@dataclass(frozen=True)
class Scenario:
    name: str
    question: str
    auth: dict[str, Any] | None = None
    expected_intent: str | None = None
    expected_intents: tuple[str, ...] = ()
    expected_source: str | None = None
    expected_answer_contains: tuple[str, ...] = ()
    expected_data_contains: tuple[str, ...] = ()
    expected_requires_auth: bool | None = None
    min_data_rows: int = 0


@dataclass
class ScenarioResult:
    scenario: Scenario
    ok: bool
    errors: list[str] = field(default_factory=list)
    response: dict[str, Any] | None = None


SCENARIOS = [
    Scenario(
        name="public_clinic_list",
        question="Địa chỉ phòng khám ở đâu?",
        expected_intent="general_info",
        expected_source="robo_app.clinics, robo_app.clinic_settings",
        expected_answer_contains=("BIOMEDIC",),
        expected_data_contains=("BIOMEDIC DIAGNOSTIC CENTER", "Phòng Khám Đa Khoa Mẫu"),
        min_data_rows=2,
    ),
    Scenario(
        name="service_ct_generic",
        question="tôi muốn chụp ct",
        expected_intent="service_price",
        expected_source="robo_app.services",
        expected_answer_contains=("CT",),
        expected_data_contains=("CT001", "CT Brain without contrast"),
        min_data_rows=2,
    ),
    Scenario(
        name="service_tibc_exact",
        question="xét nghiệm TIBC có giá bao nhiêu",
        expected_intent="service_price",
        expected_source="robo_app.services",
        expected_answer_contains=("TIBC", "6.25"),
        expected_data_contains=("LAB468", "TIBC"),
        min_data_rows=1,
    ),
    Scenario(
        name="lab_categories",
        question="có các loại xét nghiệm nào",
        expected_intent="service_category_list",
        expected_source="robo_app.services",
        expected_answer_contains=("nhóm",),
        expected_data_contains=("lab", "category_name"),
        min_data_rows=1,
    ),
    Scenario(
        name="lab_categories_short",
        question="danh sách xét nghiệm",
        expected_intent="service_category_list",
        expected_source="robo_app.services",
        expected_answer_contains=("nhóm",),
        expected_data_contains=("lab", "category_name"),
        min_data_rows=1,
    ),
    Scenario(
        name="lab_categories_remaining",
        question="24 nhóm khác là nhóm nào",
        expected_intent="service_category_list",
        expected_source="robo_app.services",
        expected_answer_contains=("13.", "nhóm"),
        expected_data_contains=("category_offset", "total_categories", "lab"),
        min_data_rows=1,
    ),
    Scenario(
        name="service_catalog_summary",
        question="các dịch vụ hiện có",
        expected_intent="service_catalog_summary",
        expected_source="robo_app.services",
        expected_answer_contains=("dịch vụ", "nhóm"),
        expected_data_contains=("total_services", "total_categories", "category_name"),
        min_data_rows=1,
    ),
    Scenario(
        name="service_category_detail_ct",
        question="xem chi tiết nhóm CT Scan",
        expected_intent="service_category_detail",
        expected_source="robo_app.services",
        expected_answer_contains=("CT Scan", "CT001"),
        expected_data_contains=("CT Brain without contrast", "total_services_in_category"),
        min_data_rows=1,
    ),
    Scenario(
        name="service_package_detail",
        question="gói khám General Health Check Up gồm gì?",
        expected_intent="service_package_detail",
        expected_source="robo_app.service_packages, robo_app.service_package_items",
        expected_answer_contains=("General Health Check Up", "CBC"),
        expected_data_contains=("PKG-0001", "GHC001", "CBC", "total_items_in_package"),
        min_data_rows=1,
    ),
    Scenario(
        name="lab_indicator_detail",
        question="CBC gồm những chỉ số nào?",
        expected_intent="lab_indicator_detail",
        expected_source="robo_app.service_lab_indicators",
        expected_answer_contains=("CBC", "WBC"),
        expected_data_contains=("WBC", "Bạch cầu", "reference_range_text"),
        min_data_rows=1,
    ),
    Scenario(
        name="icd10_lookup",
        question="ICD10 E061 là gì?",
        expected_intent="icd10_lookup",
        expected_source="robo_app.icd10_codes",
        expected_answer_contains=("E061", "Viêm tuyến giáp", "không phải chẩn đoán y khoa"),
        expected_data_contains=("E061", "Viêm tuyến giáp bán cấp"),
        min_data_rows=1,
    ),
    Scenario(
        name="medical_advice_safety",
        question="tôi đau bụng nên khám gì?",
        expected_intent="medical_advice",
        expected_answer_contains=("đau bụng", "bác sĩ", "cấp cứu"),
    ),
    Scenario(
        name="guest_lab_result_blocked",
        question="tôi muốn nhận kết quả xét nghiệm",
        expected_intent="lab_result_lookup",
        expected_source="policy",
        expected_requires_auth=True,
        expected_answer_contains=("xác thực",),
    ),
    Scenario(
        name="patient_lab_result",
        question="tôi muốn nhận kết quả xét nghiệm",
        auth={
            "role": "patient",
            "patient_id": "d7402d44-a12f-420b-93b9-90372a3b2e6e",
        },
        expected_intent="lab_result_lookup",
        expected_source="robo_app.paraclinical_results",
        expected_answer_contains=("Glucose",),
        expected_data_contains=("Glucose", "has_result"),
        expected_requires_auth=True,
        min_data_rows=1,
    ),
    Scenario(
        name="patient_partner_lab_request_lookup",
        question="Mẫu xét nghiệm của tôi đã lấy chưa?",
        auth={
            "role": "patient",
            "patient_id": "d7402d44-a12f-420b-93b9-90372a3b2e6e",
        },
        expected_intent="partner_lab_request_lookup",
        expected_source="robo_app.partner_lab_requests, robo_app.partner_onsite_collections",
        expected_answer_contains=("PLR-PROD", "Trần Thị Bình"),
        expected_data_contains=("PLR-PROD-0003", "sample_collected", "partner_lab_request"),
        expected_requires_auth=True,
        min_data_rows=1,
    ),
    Scenario(
        name="patient_appointment_lookup",
        question="tôi có lịch hẹn nào không",
        auth={
            "role": "patient",
            "patient_id": "d7402d44-a12f-420b-93b9-90372a3b2e6e",
        },
        expected_intents=("appointment_lookup", "personal_data"),
        expected_source="robo_app.appointments",
        expected_answer_contains=("Dr. MVP Demo",),
        expected_data_contains=("Trần Thị Bình", "Dr. MVP Demo", "Glucose"),
        expected_requires_auth=True,
        min_data_rows=1,
    ),
    Scenario(
        name="patient_profile_summary",
        question="Thông tin hồ sơ của tôi là gì?",
        auth={
            "role": "patient",
            "patient_id": "d7402d44-a12f-420b-93b9-90372a3b2e6e",
        },
        expected_intent="patient_profile_summary",
        expected_source="robo_app.patients",
        expected_answer_contains=("Trần Thị Bình",),
        expected_data_contains=("BIO2690-00038", "Trần Thị Bình"),
        expected_requires_auth=True,
        min_data_rows=1,
    ),
    Scenario(
        name="patient_timeline_summary",
        question="Tóm tắt lịch sử khám của tôi",
        auth={
            "role": "patient",
            "patient_id": "d7402d44-a12f-420b-93b9-90372a3b2e6e",
        },
        expected_intent="patient_timeline_summary",
        expected_source="robo_app.appointments, robo_app.paraclinical_results",
        expected_answer_contains=("timeline",),
        expected_data_contains=("Trần Thị Bình",),
        expected_requires_auth=True,
        min_data_rows=1,
    ),
    Scenario(
        name="patient_visit_summary",
        question="Tóm tắt lần khám gần đây của tôi",
        auth={
            "role": "patient",
            "patient_id": "d7402d44-a12f-420b-93b9-90372a3b2e6e",
        },
        expected_intent="visit_summary_lookup",
        expected_source="robo_app.patient_visit_summaries",
        expected_answer_contains=("lượt khám",),
        expected_data_contains=("Đau đầu nhẹ", "Theo dõi đau đầu"),
        expected_requires_auth=True,
        min_data_rows=1,
    ),
    Scenario(
        name="patient_billing_summary",
        question="Tôi đã thanh toán chưa?",
        auth={
            "role": "patient",
            "patient_id": "d7402d44-a12f-420b-93b9-90372a3b2e6e",
        },
        expected_intent="billing_summary_lookup",
        expected_source="robo_app.billing_records",
        expected_answer_contains=("hóa đơn",),
        expected_data_contains=("HD-PROD-0001", "paid"),
        expected_requires_auth=True,
        min_data_rows=1,
    ),
    Scenario(
        name="doctor_appointment_lookup",
        question="tôi có lịch hẹn nào không",
        auth={
            "role": "doctor",
            "doctor_id": "d1a2b3c4-d1a2-b3c4-d1a2-b3c4d1a2b3c4",
        },
        expected_intents=("appointment_lookup", "personal_data"),
        expected_source="robo_app.appointments",
        expected_answer_contains=("Chea Reaksmey",),
        expected_data_contains=("Chea Reaksmey", "Dr. MVP Demo"),
        expected_requires_auth=True,
        min_data_rows=1,
    ),
    Scenario(
        name="receptionist_appointment_lookup",
        question="tôi có lịch hẹn nào không",
        auth={
            "role": "receptionist",
            "clinic_id": "d5ac6269-d8cf-4821-ac8b-a6341e68987b",
        },
        expected_intents=("appointment_lookup", "personal_data"),
        expected_source="robo_app.appointments",
        expected_data_contains=("d5ac6269-d8cf-4821-ac8b-a6341e68987b",),
        expected_requires_auth=True,
        min_data_rows=1,
    ),
    Scenario(
        name="clinic_admin_lab_result_lookup",
        question="tôi muốn nhận kết quả xét nghiệm",
        auth={
            "role": "clinic_admin",
            "clinic_id": "d5ac6269-d8cf-4821-ac8b-a6341e68987b",
        },
        expected_intent="lab_result_lookup",
        expected_source="robo_app.paraclinical_results",
        expected_data_contains=("d5ac6269-d8cf-4821-ac8b-a6341e68987b", "Glucose"),
        expected_requires_auth=True,
        min_data_rows=1,
    ),
    Scenario(
        name="system_admin_security_check_summary",
        question="trạng thái kiểm tra bảo mật hệ thống",
        auth={"role": "system_admin"},
        expected_intent="security_check_summary",
        expected_source="robo_app.security_check_results",
        expected_answer_contains=("bảo mật hệ thống", "check"),
        expected_data_contains=("all_tables_rls_enabled", "AI_BOUNDARY"),
        expected_requires_auth=True,
        min_data_rows=1,
    ),
    Scenario(
        name="rag_checkin",
        question="Quy trình check-in bệnh nhân như thế nào?",
        expected_intent="knowledge_search",
        expected_answer_contains=("tiếp nhận",),
        min_data_rows=1,
    ),
    Scenario(
        name="rag_result_process",
        question="Quy trình nhận kết quả xét nghiệm như thế nào?",
        expected_intent="knowledge_search",
        expected_answer_contains=("kết quả",),
        min_data_rows=1,
    ),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MVP chatbot /ask scenarios.")
    parser.add_argument(
        "--llm-provider",
        default=None,
        help="Override LLM_PROVIDER for this run, e.g. none or ollama.",
    )
    parser.add_argument(
        "--rag-vector",
        action="store_true",
        help="Enable vector RAG during this run. By default the runner uses keyword fallback to stay fast/stable.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print full answer and compact data preview for every scenario.",
    )
    args = parser.parse_args()

    if args.llm_provider is not None:
        os.environ["LLM_PROVIDER"] = args.llm_provider
    if not args.rag_vector:
        os.environ["RAG_VECTOR_ENABLED"] = "false"

    from fastapi.testclient import TestClient
    from app.config import get_settings
    from app.main import app

    get_settings.cache_clear()
    client = TestClient(app)

    token_cache: dict[str, str] = {}
    results = [run_scenario(client, scenario, token_cache) for scenario in SCENARIOS]
    print_results(results, verbose=args.verbose)
    return 0 if all(result.ok for result in results) else 1


def run_scenario(client: Any, scenario: Scenario, token_cache: dict[str, str]) -> ScenarioResult:
    payload: dict[str, Any] = {"question": scenario.question, "domain": "clinic"}
    headers: dict[str, str] = {}
    if scenario.auth:
        role = str(scenario.auth.get("role") or "")
        token = token_cache.get(role)
        if token is None:
            token_result = login_demo_account(client, role)
            if isinstance(token_result, ScenarioResult):
                return ScenarioResult(
                    scenario=scenario,
                    ok=False,
                    errors=token_result.errors,
                )
            token = token_result
            token_cache[role] = token
        headers["Authorization"] = f"Bearer {token}"

    response = client.post("/ask", json=payload, headers=headers)
    errors: list[str] = []
    if response.status_code != 200:
        return ScenarioResult(
            scenario=scenario,
            ok=False,
            errors=[f"HTTP {response.status_code}: {response.text}"],
        )

    body = response.json()
    if scenario.expected_intent and body.get("intent") != scenario.expected_intent:
        errors.append(f"intent={body.get('intent')!r}, expected {scenario.expected_intent!r}")
    if scenario.expected_intents and body.get("intent") not in scenario.expected_intents:
        errors.append(f"intent={body.get('intent')!r}, expected one of {scenario.expected_intents!r}")

    if scenario.expected_source:
        sources = body.get("sources") or []
        if scenario.expected_source not in sources:
            errors.append(f"sources={sources!r}, expected to include {scenario.expected_source!r}")

    if scenario.expected_requires_auth is not None and body.get("requires_auth") is not scenario.expected_requires_auth:
        errors.append(
            f"requires_auth={body.get('requires_auth')!r}, expected {scenario.expected_requires_auth!r}"
        )

    answer = str(body.get("answer") or "")
    for text in scenario.expected_answer_contains:
        if text.lower() not in answer.lower():
            errors.append(f"answer missing {text!r}")

    data = body.get("data") or []
    if len(data) < scenario.min_data_rows:
        errors.append(f"data rows={len(data)}, expected at least {scenario.min_data_rows}")

    data_text = str(data)
    for text in scenario.expected_data_contains:
        if text.lower() not in data_text.lower():
            errors.append(f"data missing {text!r}")

    if scenario.name == "service_ct_generic":
        first_names = " ".join(str(item.get("name") or "") for item in data[:3]).lower()
        if "mri" in first_names:
            errors.append("generic CT query returned MRI in top 3 data rows")

    return ScenarioResult(
        scenario=scenario,
        ok=not errors,
        errors=errors,
        response=body,
    )


def login_demo_account(client: Any, role: str) -> str | ScenarioResult:
    credentials = DEMO_ACCOUNTS_BY_ROLE.get(role)
    if not credentials:
        return ScenarioResult(
            scenario=Scenario(name=f"login_{role}", question=""),
            ok=False,
            errors=[f"No demo account configured for role {role!r}"],
        )

    email, password = credentials
    response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    if response.status_code != 200:
        return ScenarioResult(
            scenario=Scenario(name=f"login_{role}", question=""),
            ok=False,
            errors=[f"Login failed for {role}: HTTP {response.status_code}: {response.text}"],
        )

    token = response.json().get("access_token")
    if not token:
        return ScenarioResult(
            scenario=Scenario(name=f"login_{role}", question=""),
            ok=False,
            errors=[f"Login response for {role} did not include access_token"],
        )
    return str(token)


def print_results(results: list[ScenarioResult], verbose: bool) -> None:
    for result in results:
        marker = "PASS" if result.ok else "FAIL"
        response = result.response or {}
        print(
            f"[{marker}] {result.scenario.name}: "
            f"intent={response.get('intent')} "
            f"answer_source={response.get('answer_source')} "
            f"sources={response.get('sources')}"
        )
        if result.errors:
            for error in result.errors:
                print(f"  - {error}")
        if verbose and response:
            print(f"  answer: {response.get('answer')}")
            print(f"  data: {response.get('data')}")
    passed = sum(1 for result in results if result.ok)
    print(f"\n{passed}/{len(results)} scenarios passed")


if __name__ == "__main__":
    raise SystemExit(main())

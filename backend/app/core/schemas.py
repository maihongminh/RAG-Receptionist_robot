from typing import Any, Literal

from pydantic import BaseModel, Field


IntentName = Literal[
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
    "personal_data",
    "medical_advice",
    "out_of_scope",
]

DataSource = Literal["sql", "rag", "auth", "none"]
ParserSource = Literal["llm", "rule"]
AnswerSource = Literal["template", "llm_grounded", "llm_formatted"]
AuthRole = Literal["guest", "patient", "doctor", "receptionist", "clinic_admin", "system_admin"]


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    domain: str | None = "clinic"
    session_id: str | None = None
    auth: "AuthContext | None" = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuthContext(BaseModel):
    account_id: str | None = None
    session_id: str | None = None
    user_id: str | None = None
    role: AuthRole | str = "guest"
    organization_id: str | None = None
    clinic_id: str | None = None
    patient_id: str | None = None
    doctor_id: str | None = None
    staff_id: str | None = None


class AuthLoginRequest(BaseModel):
    role: AuthRole | None = None
    email: str | None = None
    password: str | None = None
    patient_id: str | None = None
    doctor_id: str | None = None
    clinic_id: str | None = None
    staff_id: str | None = None


class AuthLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    auth: AuthContext


class AuthMeResponse(BaseModel):
    auth: AuthContext


class AuthLogoutResponse(BaseModel):
    ok: bool = True


class Intent(BaseModel):
    domain: str = "clinic"
    intent: IntentName
    entities: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0
    requires_auth: bool = False
    data_source: DataSource = "none"
    reasoning: str | None = None


class ToolResult(BaseModel):
    tool_name: str
    source: str
    rows: list[dict[str, Any]] = Field(default_factory=list)
    message: str | None = None
    confidence: float = 0.0


class AskResponse(BaseModel):
    request_id: str | None = None
    latency_ms: float | None = None
    session_id: str | None = None
    question: str
    answer: str
    domain: str
    intent: IntentName
    confidence: float
    parser_source: ParserSource = "rule"
    answer_source: AnswerSource = "template"
    sources: list[str] = Field(default_factory=list)
    data: list[dict[str, Any]] = Field(default_factory=list)
    requires_auth: bool = False

from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.core.orchestrator import Orchestrator
from app.core.schemas import AskRequest, AskResponse
from app.domains.clinic.adapter import ClinicAdapter


router = APIRouter(tags=["chat"])


def build_orchestrator() -> Orchestrator:
    settings = get_settings()
    adapters = {
        "clinic": ClinicAdapter(),
    }
    return Orchestrator(adapters=adapters, default_domain=settings.default_domain)


@router.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest) -> AskResponse:
    orchestrator = build_orchestrator()
    try:
        return orchestrator.handle(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

from fastapi import APIRouter, Header, HTTPException

from app.auth.audit_logger import AuditLogger
from app.auth.login_service import AuthLoginError, AuthLoginService
from app.auth.session_service import AuthSessionService
from app.auth.token_service import AuthTokenError, AuthTokenService, bearer_token_from_header
from app.core.schemas import AuthLoginRequest, AuthLoginResponse, AuthLogoutResponse, AuthMeResponse


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthLoginResponse)
def login(payload: AuthLoginRequest) -> AuthLoginResponse:
    try:
        return AuthLoginService().login(payload)
    except AuthLoginError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.get("/me", response_model=AuthMeResponse)
def me(authorization: str | None = Header(default=None)) -> AuthMeResponse:
    try:
        token = bearer_token_from_header(authorization)
        if not token:
            raise AuthTokenError("Missing bearer token.")
        return AuthMeResponse(auth=AuthTokenService().verify(token))
    except AuthTokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/logout", response_model=AuthLogoutResponse)
def logout(authorization: str | None = Header(default=None)) -> AuthLogoutResponse:
    try:
        token = bearer_token_from_header(authorization)
        if not token:
            raise AuthTokenError("Missing bearer token.")
        token_service = AuthTokenService()
        auth = token_service.verify(token)
        session_id = auth.session_id or token_service.session_id(token)
        if session_id:
            AuthSessionService().revoke(session_id)
            AuditLogger().log_auth_event(
                event_type="logout_success",
                account_id=auth.account_id,
                session_id=session_id,
                user_id=auth.user_id,
                role=str(auth.role),
                clinic_id=auth.clinic_id,
            )
        return AuthLogoutResponse(ok=True)
    except AuthTokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

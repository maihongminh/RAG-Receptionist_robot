from fastapi import APIRouter, Header, HTTPException

from app.auth.audit_logger import AuditLogger
from app.auth.login_service import AuthLoginError, AuthLoginService
from app.auth.session_service import AuthSessionError, AuthSessionService
from app.auth.token_service import AuthTokenError, AuthTokenService, bearer_token_from_header
from app.config import get_settings
from app.core.schemas import (
    AuthLoginRequest,
    AuthLoginResponse,
    AuthLogoutResponse,
    AuthMeResponse,
    AuthRefreshRequest,
)


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthLoginResponse)
def login(payload: AuthLoginRequest) -> AuthLoginResponse:
    try:
        return AuthLoginService().login(payload)
    except AuthLoginError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/refresh", response_model=AuthLoginResponse)
def refresh(payload: AuthRefreshRequest) -> AuthLoginResponse:
    try:
        session_service = AuthSessionService()
        auth, refresh_token = session_service.refresh(
            payload.refresh_token,
            get_settings().auth_refresh_token_ttl_seconds,
        )
        token, expires_in = AuthTokenService().issue(auth, session_id=auth.session_id)
        AuditLogger().log_auth_event(
            event_type="refresh_success",
            account_id=auth.account_id,
            session_id=auth.session_id,
            user_id=auth.user_id,
            role=str(auth.role),
            clinic_id=auth.clinic_id,
        )
        return AuthLoginResponse(
            access_token=token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            auth=auth,
        )
    except AuthSessionError as exc:
        AuditLogger().log_auth_event(
            event_type="refresh_failed",
            reason="invalid_or_expired_refresh_token",
        )
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.get("/me", response_model=AuthMeResponse)
def me(authorization: str | None = Header(default=None)) -> AuthMeResponse:
    try:
        token = bearer_token_from_header(authorization)
        if not token:
            raise AuthTokenError("Missing bearer token.")
        return AuthMeResponse(auth=AuthTokenService().verify(token))
    except AuthTokenError as exc:
        AuditLogger().log_auth_event(
            event_type="token_rejected",
            reason=str(exc),
            metadata={"endpoint": "/auth/me"},
        )
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
        AuditLogger().log_auth_event(
            event_type="token_rejected",
            reason=str(exc),
            metadata={"endpoint": "/auth/logout"},
        )
        raise HTTPException(status_code=401, detail=str(exc)) from exc

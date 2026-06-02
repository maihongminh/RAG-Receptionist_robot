from fastapi import APIRouter, Header, HTTPException, Request

from app.auth.admin_service import AuthAdminError, AuthAdminForbidden, AuthAdminService
from app.auth.audit_logger import AuditLogger
from app.auth.login_service import AuthLoginError, AuthLoginService
from app.auth.password_change_service import AuthPasswordChangeError, AuthPasswordChangeService
from app.auth.password_reset_service import AuthPasswordResetError, AuthPasswordResetService
from app.auth.rate_limiter import login_rate_limiter
from app.auth.session_service import AuthSessionError, AuthSessionService
from app.auth.token_service import AuthTokenError, AuthTokenService, bearer_token_from_header
from app.config import get_settings
from app.core.schemas import (
    AuthLoginRequest,
    AuthLoginResponse,
    AuthContext,
    AuthAdminAccountDetail,
    AuthAdminAccountsResponse,
    AuthAdminActionResponse,
    AuthChangePasswordRequest,
    AuthChangePasswordResponse,
    AuthPasswordResetCompleteRequest,
    AuthPasswordResetRequest,
    AuthPasswordResetResponse,
    AuthLogoutResponse,
    AuthMeResponse,
    AuthRefreshRequest,
)


router = APIRouter(prefix="/auth", tags=["auth"])


def _auth_from_bearer(authorization: str | None) -> tuple[str, AuthContext]:
    token = bearer_token_from_header(authorization)
    if not token:
        raise AuthTokenError("Missing bearer token.")
    return token, AuthTokenService().verify(token)


@router.post("/login", response_model=AuthLoginResponse)
def login(payload: AuthLoginRequest, request: Request) -> AuthLoginResponse:
    settings = get_settings()
    client_host = request.client.host if request.client else "unknown"
    email_key = (payload.email or "").strip().lower()
    rate_limit_key = f"{client_host}:{email_key}"
    if not login_rate_limiter.allow(
        rate_limit_key,
        max_attempts=settings.auth_login_rate_limit_attempts,
        window_seconds=settings.auth_login_rate_limit_window_seconds,
    ):
        AuditLogger().log_auth_event(
            event_type="login_failed",
            reason="rate_limited",
            metadata={"client_host": client_host, "email": email_key},
        )
        raise HTTPException(status_code=429, detail="Too many login attempts. Please try again later.")
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


@router.post("/change-password", response_model=AuthChangePasswordResponse)
def change_password(
    payload: AuthChangePasswordRequest,
    authorization: str | None = Header(default=None),
) -> AuthChangePasswordResponse:
    try:
        _, auth = _auth_from_bearer(authorization)
        AuthPasswordChangeService().change_password(auth, payload)
        return AuthChangePasswordResponse(ok=True)
    except AuthTokenError as exc:
        AuditLogger().log_auth_event(
            event_type="token_rejected",
            reason=str(exc),
            metadata={"endpoint": "/auth/change-password"},
        )
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except AuthPasswordChangeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/admin/accounts", response_model=AuthAdminAccountsResponse)
def list_admin_accounts(
    query: str = "",
    limit: int = 50,
    authorization: str | None = Header(default=None),
) -> AuthAdminAccountsResponse:
    try:
        _, auth = _auth_from_bearer(authorization)
        accounts = AuthAdminService().list_accounts(auth, query=query, limit=limit)
        return AuthAdminAccountsResponse(accounts=accounts)
    except AuthTokenError as exc:
        AuditLogger().log_auth_event(
            event_type="token_rejected",
            reason=str(exc),
            metadata={"endpoint": "/auth/admin/accounts"},
        )
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except AuthAdminForbidden as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except AuthAdminError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/admin/accounts/{account_id}", response_model=AuthAdminAccountDetail)
def get_admin_account(
    account_id: str,
    authorization: str | None = Header(default=None),
) -> AuthAdminAccountDetail:
    try:
        _, auth = _auth_from_bearer(authorization)
        return AuthAdminService().get_account(auth, account_id)
    except AuthTokenError as exc:
        AuditLogger().log_auth_event(
            event_type="token_rejected",
            reason=str(exc),
            metadata={"endpoint": "/auth/admin/accounts/{account_id}"},
        )
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except AuthAdminForbidden as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except AuthAdminError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/admin/accounts/{account_id}/unlock", response_model=AuthAdminActionResponse)
def unlock_admin_account(
    account_id: str,
    authorization: str | None = Header(default=None),
) -> AuthAdminActionResponse:
    try:
        _, auth = _auth_from_bearer(authorization)
        return AuthAdminService().unlock_account(auth, account_id)
    except AuthTokenError as exc:
        AuditLogger().log_auth_event(
            event_type="token_rejected",
            reason=str(exc),
            metadata={"endpoint": "/auth/admin/accounts/{account_id}/unlock"},
        )
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except AuthAdminForbidden as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except AuthAdminError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/admin/accounts/{account_id}/revoke-sessions", response_model=AuthAdminActionResponse)
def revoke_admin_account_sessions(
    account_id: str,
    authorization: str | None = Header(default=None),
) -> AuthAdminActionResponse:
    try:
        _, auth = _auth_from_bearer(authorization)
        return AuthAdminService().revoke_sessions(auth, account_id)
    except AuthTokenError as exc:
        AuditLogger().log_auth_event(
            event_type="token_rejected",
            reason=str(exc),
            metadata={"endpoint": "/auth/admin/accounts/{account_id}/revoke-sessions"},
        )
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except AuthAdminForbidden as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except AuthAdminError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/password-reset/request", response_model=AuthPasswordResetResponse)
def request_password_reset(payload: AuthPasswordResetRequest) -> AuthPasswordResetResponse:
    reset_token = AuthPasswordResetService().request_reset(payload.email)
    if get_settings().auth_password_reset_expose_token:
        return AuthPasswordResetResponse(ok=True, reset_token=reset_token)
    return AuthPasswordResetResponse(ok=True)


@router.post("/password-reset/complete", response_model=AuthChangePasswordResponse)
def complete_password_reset(
    payload: AuthPasswordResetCompleteRequest,
) -> AuthChangePasswordResponse:
    try:
        AuthPasswordResetService().complete_reset(payload.reset_token, payload.new_password)
        return AuthChangePasswordResponse(ok=True)
    except AuthPasswordResetError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/me", response_model=AuthMeResponse)
def me(authorization: str | None = Header(default=None)) -> AuthMeResponse:
    try:
        _, auth = _auth_from_bearer(authorization)
        return AuthMeResponse(auth=auth)
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

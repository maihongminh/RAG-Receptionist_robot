from fastapi import APIRouter, Header, HTTPException

from app.auth.login_service import AuthLoginError, AuthLoginService
from app.auth.token_service import AuthTokenError, AuthTokenService, bearer_token_from_header
from app.core.schemas import AuthLoginRequest, AuthLoginResponse, AuthMeResponse


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

from app.core.schemas import AskRequest, AuthContext
from app.auth.token_service import AuthTokenService, bearer_token_from_header
from app.config import get_settings


class AuthContextResolver:
    """Resolve the effective auth context for a request.

    Product behavior:
    - Trust bearer tokens issued by /auth/login.
    - Treat requests without a valid token as guest.
    - Ignore request-body auth context by default because clients can forge it.
    """

    def resolve(self, payload: AskRequest, authorization: str | None = None) -> AuthContext:
        token = bearer_token_from_header(authorization)
        if token:
            return AuthTokenService().verify(token)
        if payload.auth is not None and get_settings().auth_allow_request_context:
            return payload.auth
        return AuthContext(role="guest")

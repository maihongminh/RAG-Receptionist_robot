from app.core.schemas import AskRequest, AuthContext
from app.auth.token_service import AuthTokenService, bearer_token_from_header


class AuthContextResolver:
    """Resolve the effective auth context for a request.

    MVP behavior:
    - If the request has auth context, use it.
    - Otherwise treat the user as a guest.

    Later this class should verify JWT/session/OTP and enrich the context with
    clinic_id, patient_id, doctor_id and organization_id from trusted sources.
    """

    def resolve(self, payload: AskRequest, authorization: str | None = None) -> AuthContext:
        token = bearer_token_from_header(authorization)
        if token:
            return AuthTokenService().verify(token)
        if payload.auth is not None:
            return payload.auth
        return AuthContext(role="guest")

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any

from app.config import get_settings
from app.core.schemas import AuthContext


class AuthTokenError(ValueError):
    pass


class AuthTokenService:
    """Issue and verify signed auth-context bearer tokens.

    This is a small JWT-like HMAC token implemented with stdlib only. It is
    sufficient for MVP auth; production can replace it with JWT/OIDC without
    changing the rest of the auth flow.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    def issue(self, auth: AuthContext) -> tuple[str, int]:
        now = int(time.time())
        expires_in = self.settings.auth_token_ttl_seconds
        payload = {
            "iat": now,
            "exp": now + expires_in,
            "auth": auth.model_dump(),
        }
        header = {"alg": "HS256", "typ": "JWT"}
        unsigned = ".".join(
            [
                self._b64_json(header),
                self._b64_json(payload),
            ]
        )
        signature = self._sign(unsigned)
        return f"{unsigned}.{signature}", expires_in

    def verify(self, token: str) -> AuthContext:
        parts = token.split(".")
        if len(parts) != 3:
            raise AuthTokenError("Invalid token format.")

        unsigned = ".".join(parts[:2])
        expected_signature = self._sign(unsigned)
        if not hmac.compare_digest(expected_signature, parts[2]):
            raise AuthTokenError("Invalid token signature.")

        payload = self._decode_json(parts[1])
        exp = int(payload.get("exp") or 0)
        if exp < int(time.time()):
            raise AuthTokenError("Token has expired.")

        auth_data = payload.get("auth") or {}
        return AuthContext(**auth_data)

    def _sign(self, unsigned: str) -> str:
        digest = hmac.new(
            self.settings.auth_token_secret.encode("utf-8"),
            unsigned.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        return self._b64_bytes(digest)

    def _b64_json(self, value: dict[str, Any]) -> str:
        data = json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return self._b64_bytes(data)

    def _b64_bytes(self, value: bytes) -> str:
        return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")

    def _decode_json(self, value: str) -> dict[str, Any]:
        try:
            padded = value + "=" * (-len(value) % 4)
            data = base64.urlsafe_b64decode(padded.encode("ascii"))
            return json.loads(data)
        except (ValueError, json.JSONDecodeError) as exc:
            raise AuthTokenError("Invalid token payload.") from exc


def bearer_token_from_header(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise AuthTokenError("Authorization header must use Bearer token.")
    return token.strip()

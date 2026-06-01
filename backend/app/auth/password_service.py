from __future__ import annotations

import base64
import hashlib
import hmac
import secrets


PASSWORD_ALGORITHM = "pbkdf2_sha256"
DEFAULT_ITERATIONS = 260_000


class PasswordHashError(ValueError):
    pass


def hash_password(password: str, *, salt: str | None = None) -> str:
    if not password:
        raise PasswordHashError("Password cannot be empty.")
    salt_value = salt or secrets.token_urlsafe(16)
    digest = _pbkdf2(password, salt_value, DEFAULT_ITERATIONS)
    return f"{PASSWORD_ALGORITHM}${DEFAULT_ITERATIONS}${salt_value}${digest}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations_raw, salt, expected = password_hash.split("$", 3)
        if algorithm != PASSWORD_ALGORITHM:
            return False
        iterations = int(iterations_raw)
    except (ValueError, AttributeError):
        return False

    actual = _pbkdf2(password, salt, iterations)
    return hmac.compare_digest(actual, expected)


def _pbkdf2(password: str, salt: str, iterations: int) -> str:
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    )
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")

import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.core.config import get_settings


settings = get_settings()


def create_token(subject: str, token_type: str = "access", expires_delta: timedelta | None = None) -> str:
    now = datetime.now(timezone.utc)
    if expires_delta is None:
        if token_type == "refresh":
            expires_delta = timedelta(days=settings.refresh_token_expire_days)
        else:
            expires_delta = timedelta(minutes=settings.access_token_expire_minutes)

    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])


def check_password(password: str, encoded: str | None) -> bool:
    """Verify Django pbkdf2_sha256 hashes and a couple of common fallbacks."""

    if not encoded:
        return False

    if encoded.startswith("pbkdf2_sha256$"):
        try:
            algorithm, iterations, salt, hash_value = encoded.split("$", 3)
            digest = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode(),
                salt.encode(),
                int(iterations),
            )
            calculated = base64.b64encode(digest).decode().strip()
            return algorithm == "pbkdf2_sha256" and hmac.compare_digest(calculated, hash_value)
        except (ValueError, TypeError):
            return False

    if encoded.startswith("sha256$"):
        try:
            _, salt, hash_value = encoded.split("$", 2)
            calculated = hashlib.sha256((salt + password).encode()).hexdigest()
            return hmac.compare_digest(calculated, hash_value)
        except ValueError:
            return False

    return hmac.compare_digest(password, encoded)


def make_password(password: str) -> str:
    salt = secrets.token_urlsafe(12)[:12]
    iterations = 720000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations)
    hash_value = base64.b64encode(digest).decode().strip()
    return f"pbkdf2_sha256${iterations}${salt}${hash_value}"


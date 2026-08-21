"""
Security utilities: password hashing, JWT generation/validation.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import secrets

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, additional_claims: Optional[dict] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    if additional_claims:
        payload.update(additional_claims)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token. Raises JWTError on failure."""
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def generate_api_key() -> str:
    """Generate a secure random API key."""
    return f"vapt_{secrets.token_urlsafe(32)}"


# ── Sensitive field masking ──────────────────────────────────────────────────
SENSITIVE_HEADERS = {
    "authorization", "cookie", "set-cookie", "x-api-key",
    "api-key", "x-auth-token", "x-access-token", "password",
    "x-csrf-token", "proxy-authorization",
}


def mask_sensitive_headers(headers: dict[str, str]) -> dict[str, str]:
    """Mask sensitive header values for safe logging/display."""
    masked = {}
    for k, v in headers.items():
        if k.lower() in SENSITIVE_HEADERS:
            masked[k] = "****REDACTED****"
        else:
            masked[k] = v
    return masked

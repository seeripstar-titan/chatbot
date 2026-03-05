"""
JWT token creation and verification.
"""

import uuid
from datetime import datetime, timedelta, timezone

import jwt

from backend.config import get_settings

settings = get_settings()


class TokenError(Exception):
    """Raised when a token is invalid or expired."""


def create_access_token(
    subject: str,
    tenant_id: str,
    extra_claims: dict | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes))

    payload = {
        "sub": subject,
        "tenant_id": tenant_id,
        "iat": now,
        "exp": expire,
        "jti": str(uuid.uuid4()),
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(
    subject: str,
    tenant_id: str,
) -> str:
    """Create a signed JWT refresh token."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.jwt_refresh_token_expire_days)

    payload = {
        "sub": subject,
        "tenant_id": tenant_id,
        "iat": now,
        "exp": expire,
        "jti": str(uuid.uuid4()),
        "type": "refresh",
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise TokenError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise TokenError(f"Invalid token: {e}")

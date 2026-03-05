"""
FastAPI dependency functions for authentication and authorization.
"""

import uuid

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.api_keys import hash_api_key
from backend.auth.jwt import TokenError, decode_token
from backend.db.models import APIKey, EndUser, Tenant
from backend.db.session import get_db


class AuthContext:
    """Holds the authenticated context for a request."""

    def __init__(
        self,
        tenant: Tenant,
        end_user: EndUser | None = None,
    ):
        self.tenant = tenant
        self.end_user = end_user

    @property
    def tenant_id(self) -> uuid.UUID:
        return self.tenant.id

    @property
    def user_id(self) -> uuid.UUID | None:
        return self.end_user.id if self.end_user else None

    @property
    def is_authenticated(self) -> bool:
        return self.end_user is not None and self.end_user.is_verified


async def validate_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> Tenant:
    """
    Validate the API key from the request header and return the associated tenant.
    This is the primary authentication for widget requests.
    """
    key_hash = hash_api_key(x_api_key)

    result = await db.execute(
        select(APIKey)
        .where(APIKey.key_hash == key_hash, APIKey.is_active.is_(True))
    )
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key",
        )

    # Load the tenant
    result = await db.execute(
        select(Tenant).where(Tenant.id == api_key.tenant_id)
    )
    tenant = result.scalar_one_or_none()

    if not tenant or tenant.status.value == "suspended":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant account is suspended or not found",
        )

    # Update last_used_at
    from sqlalchemy import func

    api_key.last_used_at = func.now()
    await db.flush()

    return tenant


async def get_current_user_optional(
    tenant: Tenant = Depends(validate_api_key),
    authorization: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
) -> AuthContext:
    """
    Optionally authenticate an end user via Bearer token.
    Always requires a valid API key. User auth is optional.
    """
    end_user = None

    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        try:
            payload = decode_token(token)
            if payload.get("tenant_id") != str(tenant.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Token tenant mismatch",
                )
            user_id = payload.get("sub")
            if user_id:
                result = await db.execute(
                    select(EndUser).where(
                        EndUser.id == uuid.UUID(user_id),
                        EndUser.tenant_id == tenant.id,
                    )
                )
                end_user = result.scalar_one_or_none()
        except TokenError:
            # Token invalid but API key is valid, proceed without user
            pass

    return AuthContext(tenant=tenant, end_user=end_user)


async def get_current_user_required(
    auth: AuthContext = Depends(get_current_user_optional),
) -> AuthContext:
    """Require an authenticated end user."""
    if not auth.is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
        )
    return auth

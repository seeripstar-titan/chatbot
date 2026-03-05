"""
Authentication endpoints – user registration, login, and token refresh.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import AuthContext, validate_api_key
from backend.auth.jwt import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from backend.auth.passwords import hash_password, verify_password
from backend.config import get_settings
from backend.db.models import EndUser, Tenant
from backend.db.session import get_db
from backend.schemas import (
    RefreshTokenRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: UserRegisterRequest,
    tenant: Tenant = Depends(validate_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Register a new end user for this tenant."""
    # Check if user already exists
    result = await db.execute(
        select(EndUser).where(
            EndUser.tenant_id == tenant.id,
            EndUser.email == body.email.lower(),
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    # Create user
    user = EndUser(
        tenant_id=tenant.id,
        email=body.email.lower(),
        name=body.name,
        password_hash=hash_password(body.password),
        is_verified=True,  # Auto-verify for now; add email verification in production
    )
    db.add(user)
    await db.flush()

    # Generate tokens
    access_token = create_access_token(
        subject=str(user.id),
        tenant_id=str(tenant.id),
        extra_claims={"email": user.email, "name": user.name},
    )
    refresh_token = create_refresh_token(
        subject=str(user.id),
        tenant_id=str(tenant.id),
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    body: UserLoginRequest,
    tenant: Tenant = Depends(validate_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Authenticate an end user and return tokens."""
    result = await db.execute(
        select(EndUser).where(
            EndUser.tenant_id == tenant.id,
            EndUser.email == body.email.lower(),
        )
    )
    user = result.scalar_one_or_none()

    if not user or not user.password_hash or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(
        subject=str(user.id),
        tenant_id=str(tenant.id),
        extra_claims={"email": user.email, "name": user.name},
    )
    refresh_token = create_refresh_token(
        subject=str(user.id),
        tenant_id=str(tenant.id),
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshTokenRequest,
    tenant: Tenant = Depends(validate_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Refresh an access token using a refresh token."""
    try:
        payload = decode_token(body.refresh_token)
    except TokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    if payload.get("tenant_id") != str(tenant.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token tenant mismatch",
        )

    user_id = payload.get("sub")
    result = await db.execute(
        select(EndUser).where(
            EndUser.id == uuid.UUID(user_id),
            EndUser.tenant_id == tenant.id,
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    access_token = create_access_token(
        subject=str(user.id),
        tenant_id=str(tenant.id),
        extra_claims={"email": user.email, "name": user.name},
    )
    new_refresh_token = create_refresh_token(
        subject=str(user.id),
        tenant_id=str(tenant.id),
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )

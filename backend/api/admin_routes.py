"""
Admin endpoints – tenant management and API key generation.
These would typically be protected by admin auth in production.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.api_keys import generate_api_key
from backend.db.models import APIKey, Tenant, TenantStatus
from backend.db.session import get_db
from backend.schemas import APIKeyCreateResponse, TenantCreateRequest, TenantResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/tenants", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    body: TenantCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new tenant (website/business).
    In production, this would require admin authentication.
    """
    # Check uniqueness
    result = await db.execute(
        select(Tenant).where(Tenant.domain == body.domain)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A tenant with this domain already exists",
        )

    tenant = Tenant(
        name=body.name,
        domain=body.domain,
        status=TenantStatus.ACTIVE,
        system_prompt=body.system_prompt,
        welcome_message=body.welcome_message,
    )
    db.add(tenant)
    await db.flush()

    return TenantResponse(
        id=str(tenant.id),
        name=tenant.name,
        domain=tenant.domain,
        status=tenant.status.value,
        welcome_message=tenant.welcome_message,
        created_at=tenant.created_at,
    )


@router.post("/tenants/{tenant_id}/api-keys", response_model=APIKeyCreateResponse)
async def create_api_key(
    tenant_id: str,
    name: str = "Default Key",
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a new API key for a tenant.
    The raw key is only returned once — store it securely.
    """
    try:
        t_id = uuid.UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tenant ID")

    result = await db.execute(select(Tenant).where(Tenant.id == t_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    raw_key, key_hash, key_prefix = generate_api_key()

    api_key = APIKey(
        tenant_id=tenant.id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=name,
        is_active=True,
        allowed_origins=[],
    )
    db.add(api_key)
    await db.flush()

    return APIKeyCreateResponse(
        api_key=raw_key,
        key_prefix=key_prefix,
        name=name,
    )


@router.get("/tenants", response_model=list[TenantResponse])
async def list_tenants(db: AsyncSession = Depends(get_db)):
    """List all tenants."""
    result = await db.execute(select(Tenant).order_by(Tenant.created_at.desc()))
    tenants = result.scalars().all()
    return [
        TenantResponse(
            id=str(t.id),
            name=t.name,
            domain=t.domain,
            status=t.status.value,
            welcome_message=t.welcome_message,
            created_at=t.created_at,
        )
        for t in tenants
    ]


@router.get("/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(tenant_id: str, db: AsyncSession = Depends(get_db)):
    """Get tenant details."""
    try:
        t_id = uuid.UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tenant ID")

    result = await db.execute(select(Tenant).where(Tenant.id == t_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return TenantResponse(
        id=str(tenant.id),
        name=tenant.name,
        domain=tenant.domain,
        status=tenant.status.value,
        welcome_message=tenant.welcome_message,
        created_at=tenant.created_at,
    )

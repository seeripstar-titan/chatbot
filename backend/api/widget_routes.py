"""
Widget configuration endpoint – serves widget config and tenant info.
"""

from fastapi import APIRouter, Depends

from backend.auth.dependencies import validate_api_key
from backend.db.models import Tenant

router = APIRouter(prefix="/widget", tags=["Widget"])


@router.get("/config")
async def get_widget_config(
    tenant: Tenant = Depends(validate_api_key),
):
    """
    Get widget configuration for the tenant.
    Called by the embedded widget on initialization.
    """
    return {
        "tenant_id": str(tenant.id),
        "tenant_name": tenant.name,
        "welcome_message": tenant.welcome_message,
        "settings": tenant.settings or {},
        "features": {
            "auth_required": False,
            "auth_available": True,
            "order_tracking": True,
            "product_search": True,
            "support_tickets": True,
        },
    }

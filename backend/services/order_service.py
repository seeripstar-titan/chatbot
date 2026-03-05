"""
Order service – handles order tracking and retrieval.
"""

import uuid

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import Order
from backend.logging_config import get_logger

logger = get_logger(__name__)


class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def track_order(
        self,
        tenant_id: uuid.UUID,
        order_number: str,
        customer_email: str,
    ) -> dict | None:
        """
        Track an order by order number and customer email.
        Both must match for security.
        """
        result = await self.db.execute(
            select(Order).where(
                and_(
                    Order.tenant_id == tenant_id,
                    Order.order_number == order_number,
                    Order.customer_email == customer_email.lower(),
                )
            )
        )
        order = result.scalar_one_or_none()

        if order:
            logger.info(
                "order_tracked",
                tenant_id=str(tenant_id),
                order_number=order_number,
            )
            return self._order_to_dict(order)

        logger.warning(
            "order_not_found",
            tenant_id=str(tenant_id),
            order_number=order_number,
        )
        return None

    async def get_orders_by_email(
        self,
        tenant_id: uuid.UUID,
        customer_email: str,
        limit: int = 10,
    ) -> list[dict]:
        """Get all orders for a customer email."""
        result = await self.db.execute(
            select(Order)
            .where(
                Order.tenant_id == tenant_id,
                Order.customer_email == customer_email.lower(),
            )
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        orders = result.scalars().all()
        return [self._order_to_dict(o) for o in orders]

    @staticmethod
    def _order_to_dict(order: Order) -> dict:
        return {
            "order_number": order.order_number,
            "customer_name": order.customer_name,
            "status": order.status.value,
            "items": order.items,
            "total_amount": order.total_amount,
            "currency": order.currency,
            "shipping_address": order.shipping_address,
            "tracking_number": order.tracking_number,
            "carrier": order.carrier,
            "estimated_delivery": (
                order.estimated_delivery.isoformat() if order.estimated_delivery else None
            ),
            "shipped_at": order.shipped_at.isoformat() if order.shipped_at else None,
            "delivered_at": order.delivered_at.isoformat() if order.delivered_at else None,
            "created_at": order.created_at.isoformat(),
        }

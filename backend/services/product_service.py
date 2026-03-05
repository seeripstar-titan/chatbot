"""
Product service – handles product search and retrieval.
"""

import uuid

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import Product
from backend.logging_config import get_logger

logger = get_logger(__name__)


class ProductService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_products(
        self,
        tenant_id: uuid.UUID,
        query: str,
        category: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """Search products by keyword, category, and price range."""
        conditions = [
            Product.tenant_id == tenant_id,
            Product.is_active.is_(True),
        ]

        # Full-text-like search on name and description
        if query:
            search_term = f"%{query.lower()}%"
            conditions.append(
                or_(
                    func.lower(Product.name).like(search_term),
                    func.lower(Product.description).like(search_term),
                    func.lower(Product.category).like(search_term),
                )
            )

        if category:
            conditions.append(func.lower(Product.category) == category.lower())
        if min_price is not None:
            conditions.append(Product.price >= min_price)
        if max_price is not None:
            conditions.append(Product.price <= max_price)

        result = await self.db.execute(
            select(Product).where(and_(*conditions)).limit(limit)
        )
        products = result.scalars().all()

        logger.info(
            "product_search",
            tenant_id=str(tenant_id),
            query=query,
            results_count=len(products),
        )

        return [self._product_to_dict(p) for p in products]

    async def get_product_by_sku(
        self, tenant_id: uuid.UUID, sku: str
    ) -> dict | None:
        """Get a product by its SKU."""
        result = await self.db.execute(
            select(Product).where(
                Product.tenant_id == tenant_id,
                Product.sku == sku,
                Product.is_active.is_(True),
            )
        )
        product = result.scalar_one_or_none()
        if product:
            return self._product_to_dict(product)
        return None

    async def get_product_by_id(
        self, tenant_id: uuid.UUID, product_id: uuid.UUID
    ) -> dict | None:
        """Get a product by its ID."""
        result = await self.db.execute(
            select(Product).where(
                Product.tenant_id == tenant_id,
                Product.id == product_id,
                Product.is_active.is_(True),
            )
        )
        product = result.scalar_one_or_none()
        if product:
            return self._product_to_dict(product)
        return None

    async def get_categories(self, tenant_id: uuid.UUID) -> list[str]:
        """Get all product categories for a tenant."""
        result = await self.db.execute(
            select(Product.category)
            .where(Product.tenant_id == tenant_id, Product.is_active.is_(True))
            .distinct()
        )
        return [row[0] for row in result.all()]

    @staticmethod
    def _product_to_dict(product: Product) -> dict:
        return {
            "id": str(product.id),
            "sku": product.sku,
            "name": product.name,
            "description": product.description,
            "category": product.category,
            "price": product.price,
            "currency": product.currency,
            "in_stock": product.in_stock,
            "stock_quantity": product.stock_quantity,
            "specifications": product.specifications,
            "image_url": product.image_url,
        }

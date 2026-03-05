"""
FAQ service – handles knowledge base retrieval.
"""

import uuid

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import FAQ
from backend.logging_config import get_logger

logger = get_logger(__name__)


class FAQService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_faqs(
        self,
        tenant_id: uuid.UUID,
        query: str,
        category: str | None = None,
        limit: int = 5,
    ) -> list[dict]:
        """Search FAQs by keyword matching on question, answer, and keywords."""
        conditions = [
            FAQ.tenant_id == tenant_id,
            FAQ.is_active.is_(True),
        ]

        if query:
            search_term = f"%{query.lower()}%"
            conditions.append(
                or_(
                    func.lower(FAQ.question).like(search_term),
                    func.lower(FAQ.answer).like(search_term),
                )
            )

        if category:
            conditions.append(func.lower(FAQ.category) == category.lower())

        result = await self.db.execute(
            select(FAQ)
            .where(and_(*conditions))
            .order_by(FAQ.view_count.desc())
            .limit(limit)
        )
        faqs = result.scalars().all()

        logger.info(
            "faq_search",
            tenant_id=str(tenant_id),
            query=query,
            results_count=len(faqs),
        )

        return [self._faq_to_dict(f) for f in faqs]

    async def get_faq_by_id(
        self, tenant_id: uuid.UUID, faq_id: uuid.UUID
    ) -> dict | None:
        """Get a specific FAQ and increment its view count."""
        result = await self.db.execute(
            select(FAQ).where(
                FAQ.tenant_id == tenant_id,
                FAQ.id == faq_id,
                FAQ.is_active.is_(True),
            )
        )
        faq = result.scalar_one_or_none()
        if faq:
            faq.view_count += 1
            await self.db.flush()
            return self._faq_to_dict(faq)
        return None

    async def get_categories(self, tenant_id: uuid.UUID) -> list[str]:
        """Get all FAQ categories for a tenant."""
        result = await self.db.execute(
            select(FAQ.category)
            .where(FAQ.tenant_id == tenant_id, FAQ.is_active.is_(True))
            .distinct()
        )
        return [row[0] for row in result.all()]

    @staticmethod
    def _faq_to_dict(faq: FAQ) -> dict:
        return {
            "id": str(faq.id),
            "question": faq.question,
            "answer": faq.answer,
            "category": faq.category,
            "keywords": faq.keywords,
        }

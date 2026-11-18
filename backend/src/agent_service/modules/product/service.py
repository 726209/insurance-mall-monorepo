# src/agent_service/modules/product/service.py
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from agent_service.modules.product.models import Product
from agent_service.modules.product.repository import ProductRepository


class ProductService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = ProductRepository(session)

    async def list_product(
        self,
        category: str | None = None,
    ) -> list[Product]:
        return await self.repository.query_by_category(category)

    async def list_candidates(
        self,
        categories: list[str],
        premium_min: Decimal | None,
        limit_per_category: int,
    ) -> list[Product]:
        return await self.repository.find_candidates(
            categories=categories,
            premium_min=premium_min,
            limit_per_category=limit_per_category,
        )

    async def query_product_page(
        self,
        category: str | None = None,
        product_name: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Product], int]:
        """产品分页业务逻辑"""
        return await self.repository.query_page(
            category=category,
            product_name=product_name,
            page=page,
            page_size=page_size,
        )

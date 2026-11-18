# src/agent_service/modules/policy/repository.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agent_service.modules.policy.models import Policy
from agent_service.modules.product.models import Product


class PolicyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_user(self, user_id: int) -> list[tuple[Policy, Product]]:
        result = await self.session.execute(
            select(Policy, Product)
            .join(Product, Product.id == Policy.product_id)
            .where(Policy.user_id == user_id)
            .order_by(Policy.effective_at.desc())
        )
        return list(result.all())

    async def find_by_number(
        self,
        user_id: int,
        policy_number: str,
    ) -> tuple[Policy, Product] | None:
        result = await self.session.execute(
            select(Policy, Product)
            .join(Product, Product.id == Policy.product_id)
            .where(
                Policy.user_id == user_id,
                Policy.policy_number == policy_number,
            )
        )
        row = result.first()
        # 如果没有查询到，返回 None；查到了则转换为 tuple 或直接返回行内元素
        return tuple(row) if row else None  # type: ignore

# src/agent_service/modules/product/repository.py

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from agent_service.modules.product.models import Product


class ProductRepository:
    """保险产品数据仓储层（Repository）

    负责处理所有与保险产品（Product）数据库交互的异步查询逻辑。
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def query_by_category(
        self,
        category: str | None = None,
    ) -> list[Product]:
        """根据产品分类查询已上架的产品列表

        Args:
            category: 产品分类代码（如 medical, critical_illness），若为 None 则查询所有上架产品。

        Returns:
            list[Product]: 符合条件的产品列表，按 ID 升序排列。
        """

        # 1.动态组装查询条件
        # 1.1.产品必须是上架产品，status是active
        conditions = [Product.status == "active"]
        # 1.1.分类条件
        if category:
            conditions.append(Product.category == category)

        # 2.执行查询
        result = await self.session.scalars(
            select(Product).where(*conditions).order_by(Product.id.asc())
        )

        # 3.返回结果
        return list(result.all())

    async def find_candidates(
        self,
        categories: list[str],
        premium_min: Decimal | None,
        limit_per_category: int,
    ) -> list[Product]:
        """多分类多条件组合查询候选产品（常用于智能推荐或匹配场景）

        对传入的每一个分类独立进行限制数量的查询，并保证最终结果去重且维持传入的分类顺序。

        Args:
            categories: 目标分类列表（可能包含重复项）
            premium_min: 最低保费上限过滤条件（若指定，则查询 min_premium 小于该值的商品）
            limit_per_category: 每个分类最多查询的产品数量

        Returns:
            list[Product]: 组合后的候选产品列表
        """
        # 每个险种查limit_per_category条，所以先定义list，收集结果
        candidate_products: list[Product] = []

        # 利用 dict.fromkeys() 去重，同时严格保留调用方传入的险种顺序
        for category in dict.fromkeys(categories):
            conditions = [
                Product.status == "active",
                Product.category == category,
            ]
            if premium_min is not None:
                # 筛选最低保费低于指定阈值的产品
                conditions.append(Product.min_premium < premium_min)

            products = await self.session.scalars(
                select(Product)
                .where(*conditions)
                .order_by(
                    Product.min_premium.asc().nullslast(),  # 保费从低到高，NULL 值放最后
                    Product.id.asc(),  # 次要排序条件：ID 升序
                )
                .limit(limit_per_category)
            )
            candidate_products.extend(products.all())

        return candidate_products

    async def query_page(
        self,
        category: str | None = None,
        product_name: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Product], int]:
        """分页动态组合查询保险产品列表

        Args:
            category: 产品分类过滤
            product_name: 产品名称模糊搜索关键词
            page: 当前页码（从 1 开始）
            page_size: 每页显示条数

        Returns:
            tuple[list[Product], int]: (当前页的产品列表, 符合条件的总记录数)
        """
        # 1. 基础过滤条件（默认上架状态）
        conditions = [Product.status == "active"]

        if category:
            conditions.append(Product.category == category)

        if product_name:
            # 使用 SQL 的 ILIKE 或 LIKE 进行模糊匹配
            conditions.append(Product.name.ilike(f"%{product_name}%"))

        # 2. 查询符合条件的总记录数 (COUNT)
        count_stmt = select(func.count()).select_from(Product).where(*conditions)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        # 3. 查询当前页的数据列表（带分页与排序）
        offset = (page - 1) * page_size
        stmt = (
            select(Product)
            .where(*conditions)
            .order_by(Product.id.desc())  # 按 ID 降序或升序排列
            .offset(offset)
            .limit(page_size)
        )
        result = await self.session.scalars(stmt)
        products = list(result.all())

        return products, total

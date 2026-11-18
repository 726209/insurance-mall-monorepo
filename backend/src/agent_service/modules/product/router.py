# src/agent_service/modules/product/router.py
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from agent_service.common.schemas import PageResult
from agent_service.infra.database import get_session
from agent_service.modules.product.schemas import ProductResponse
from agent_service.modules.product.service import ProductService

router = APIRouter(prefix="/api/v1/products", tags=["产品相关接口"])


def get_product_service(
    session: Annotated[AsyncSession, Depends(get_session)],
):
    return ProductService(session)


@router.get("", response_model=list[ProductResponse])
async def list_product(
    service: Annotated[ProductService, Depends(get_product_service)],
    category: str | None = None,
):
    return await service.list_product(category)


@router.get("/page", response_model=PageResult[ProductResponse])
async def page_product(
    service: Annotated[ProductService, Depends(get_product_service)],
    category: str | None = None,
    product_name: str | None = None,
    page: int = 1,
    page_size: int = 20,
):
    products, total = await service.query_product_page(category, product_name, page, page_size)
    return PageResult(
        items=products,
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/candidates", response_model=list[ProductResponse])
async def list_candidates(
    service: Annotated[ProductService, Depends(get_product_service)],
    categories: Annotated[list[str], Query(min_length=1)],
    premium_min: Decimal | None = None,
    limit_per_category: int = 5,
) -> list[ProductResponse]:
    # 2.查询结果
    products = await service.list_candidates(
        categories=categories,
        premium_min=premium_min,
        limit_per_category=limit_per_category,
    )
    return [ProductResponse.model_validate(p) for p in products]

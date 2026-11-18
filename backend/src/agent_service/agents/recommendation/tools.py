# src/agent_service/agents/recommendation/tools.py
"""保险推荐的专属工具"""

from decimal import Decimal
from typing import cast, Any

from fastapi.encoders import jsonable_encoder
from langchain_core.tools import tool
from langgraph.prebuilt import ToolRuntime
from langgraph.types import interrupt

from agent_service.agents.schemas import InsuranceAgentContext
from agent_service.infra.database import AsyncSessionFactory
from agent_service.modules.insurance_plan.schemas import InsurancePlanCreate
from agent_service.modules.insurance_plan.service import InsurancePlanService
from agent_service.modules.product.models import Product
from agent_service.modules.product.service import ProductService


@tool
async def query_candidate_products(
    categories: list[str], premium_min: Decimal | None = None, limit_per_category: int = 5
):
    """
    根据险种和保费条件查询可用于推荐的候选保险产品。当用户咨询具体保险产品或需要保险产品推荐时使用。

    Args:
        categories: 产品分类列表，可选值为 medical、critical_illness、life、accident。
        premium_min: 最低保费上限，可选参数，只返回最低保费小于该值的产品。
        limit_per_category: 每个险种最多返回的产品数量，可选参数，默认5。
    """
    async with AsyncSessionFactory() as session:
        # 1.初始化Service
        service = ProductService(session)
        # 2.调用Service，得到候选产品
        products: list[Product] = await service.list_candidates(
            categories=categories,
            premium_min=premium_min,
            limit_per_category=limit_per_category,
        )
        # 3.返回给AI，最好把Product处理成json返回，json就是字符串
        # return [ProductResponse.model_validate(product) for product in products]
        return jsonable_encoder(products)

# 【废弃】使用 from agent_service.agents.tools import query_product_clause
# @tool
# async def retrieve_insurance_clause(query: str, k: int, product_id: int):
#     """查询指定保险产品的条款内容。
#
#     Args:
#         query: 需要从保险条款中查询的问题。
#         k: 返回的文档的数量
#         product_id: 保险产品ID。
#     """
#     from agent_service.rag import retriever
#
#     chunks = await retriever.retrieve(query, k, product_id)
#     if not chunks:
#         return "没有查询到相关保险条款。"
#     return "\n\n".join(
#         f"章节：{' > '.join(chunk.section_path)}\n内容：{chunk.content}" for chunk in chunks
#     )


@tool
async def save_insurance_plan(
    plan: InsurancePlanCreate,
    runtime: ToolRuntime[InsuranceAgentContext],
) -> dict[str, str]:
    """请用户确认后，保存当前保险推荐方案。"""

    decision = interrupt(  # 中断执行，把方案发给用户看看
        {
            "plan": plan.model_dump(mode="json"),
            "confirm_info": "是否确认保存这份保险推荐方案？",
            "action": ["approve", "reject"],
        }
    )
    if decision.get("action") != "approve":
        return {"message": f"用户取消保存保险方案, 原因:{decision.get('reject_reason')}"}

    async with AsyncSessionFactory() as session:
        service = InsurancePlanService(session)
        context_dict = cast(dict[str, Any], cast(object, runtime.context))
        user_id = context_dict.get("user_id", 0)
        plan_id = await service.create_plan(
            user_id=user_id,
            # user_id=runtime.context.user_id,
            data=plan,
        )

    return {
        "plan_id": str(plan_id),
        "message": "保险方案保存成功",
    }

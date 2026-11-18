# src/agent_service/modules/insurance_plan/schemas.py
from decimal import Decimal
from typing import Any

from pydantic import Field

from agent_service.common.schemas import BaseSchema


class InsurancePlanItemCreate(BaseSchema):
    """保险方案项"""

    product_id: int
    priority: int = Field(default=1, ge=1)
    recommendation_reason: str | None = None
    annual_premium_budget: Decimal | None = Field(default=None, ge=0)


class InsurancePlanCreate(BaseSchema):
    """保险方案"""

    plan_name: str = Field(min_length=1, max_length=120)
    summary: str | None = None
    insured_profile: dict[str, Any] = Field(default_factory=dict)
    items: list[InsurancePlanItemCreate] = Field(min_length=1)

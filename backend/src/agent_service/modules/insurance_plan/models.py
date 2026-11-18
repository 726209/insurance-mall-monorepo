# src/agent_service/modules/insurance_plan/models.py
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, ForeignKey, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.dialects.sqlite import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from agent_service.common.models import SQLBase, TimestampMixin


class InsurancePlan(SQLBase, TimestampMixin):
    """用户保险方案"""

    __tablename__ = "insurance_plans"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="方案唯一标识 UUID",
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        comment="所属用户 ID",
    )

    plan_name: Mapped[str] = mapped_column(String(120), nullable=False, comment="方案名称")
    summary: Mapped[str | None] = mapped_column(Text, comment="方案整体说明")
    insured_profile: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
        comment="推荐时使用的被保险人画像",
    )
    annual_premium_budget: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2), comment="组合年缴预算参考"
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="uninsured",
        server_default="uninsured",
        comment="方案投保状态",
    )


class InsurancePlanItem(SQLBase, TimestampMixin):
    """保险方案项"""

    __tablename__ = "insurance_plan_items"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="方案项唯一标识 UUID",
    )

    plan_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("insurance_plans.id", ondelete="CASCADE"),
        comment="所属保险方案 ID",
    )

    product_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("products.id"),
        comment="推荐产品 ID",
    )

    priority: Mapped[int] = mapped_column(
        Integer,
        default=1,
        server_default="1",
        comment="方案内展示顺序",
    )

    recommendation_reason: Mapped[str | None] = mapped_column(Text, comment="推荐该产品理由")
    annual_premium_budget: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2), comment="产品年缴预算参考"
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="uninsured",
        server_default="uninsured",
        comment="方案项投保状态",
    )

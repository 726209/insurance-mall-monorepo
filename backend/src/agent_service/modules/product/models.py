# src/agent_service/modules/product/models.py

"""
CREATE TABLE IF NOT EXISTS products (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    clause_name VARCHAR(300) NOT NULL,
    category VARCHAR(50) NOT NULL,
    insurer VARCHAR(120) NOT NULL,
    image_url TEXT,
    description TEXT,
    min_premium DECIMAL(14,2),
    max_premium DECIMAL(14,2),
    target_group VARCHAR(300),
    highlights TEXT[],
    status VARCHAR(30) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_products_category CHECK (category IN ('medical', 'critical_illness', 'accident', 'life'))
);
"""

from decimal import Decimal

from sqlalchemy import ARRAY, BigInteger, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from agent_service.common.models import SQLBase, TimestampMixin


class Product(SQLBase, TimestampMixin):
    """保险产品数据模型

    对应数据库中的 products 表，用于存储各类保险产品的基本信息、保费及状态。
    """

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="产品唯一标识 ID",
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="产品名称",
    )

    clause_name: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
        comment="条款名称",
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="产品分类（medical: 医疗险, critical_illness: 重疾险, accident: 意外险, life: 寿险）",
    )

    insurer: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        comment="承保保险公司名称",
    )

    image_url: Mapped[str | None] = mapped_column(
        Text,
        comment="产品封面或图标链接",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        comment="产品详细描述",
    )

    min_premium: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        comment="最低保费（支持精确到分）",
    )

    max_premium: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        comment="最高保费（支持精确到分）",
    )

    target_group: Mapped[str | None] = mapped_column(
        String(300),
        comment="投保适用人群说明",
    )

    highlights: Mapped[list[str] | None] = mapped_column(
        ARRAY(Text),
        comment="产品核心亮点标签列表",
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="active",
        server_default="active",
        comment="产品状态（active: 上架, inactive: 下架）",
    )

# src/agent_service/modules/user/models.py
from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from agent_service.common.models import SQLBase


class User(SQLBase):
    """业务侧用户表

    该表由业务侧建表脚本（01-init-biz-schema.sql）维护，agent-service 不负责增删改。
    此处仅映射主键，用于让 insurance_plans.user_id 的外键能够解析到目标表。
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

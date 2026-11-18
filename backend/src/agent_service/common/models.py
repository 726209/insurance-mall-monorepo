# src/agent_service/common/models.py

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# SQLAlchemy的基类，所有数据库表模型都必须继承
class SQLBase(DeclarativeBase):
    def __repr__(self) -> str:
        """通用的repr函数，用于控制台输出对象信息"""

        cls_name = self.__class__.__name__
        attrs = {}
        for key, val in vars(self).items():
            if key.startswith("_"):
                continue
            if isinstance(val, datetime):
                attrs[key] = val.strftime("%Y-%m-%d %H:%M:%S")
            else:
                attrs[key] = val
        return f"{cls_name}({attrs})"


# 通用的时间戳【混入类】，这样其它数据模型不用重复定义时间相关字段
class TimestampMixin:
    """时间戳混入类（Timestamp Mixin）

    自动为数据模型添加创建时间和更新时间字段，避免重复定义。
    """

    # func.now() 会让数据库在插入时自动生成服务器时间（如 PostgreSQL 的 NOW()）
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="记录创建时间（UTC/服务器时间）",
    )

    # onupdate=func.now() 会在每次数据行被 UPDATE 时，由 SQLAlchemy 自动更新该字段
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="记录最后更新时间",
    )


class CreateAtMixin:
    """时间戳混入类（Timestamp Mixin）

    自动为数据模型添加创建时间和更新时间字段，避免重复定义。
    """

    # func.now() 会让数据库在插入时自动生成服务器时间（如 PostgreSQL 的 NOW()）
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="记录创建时间（UTC/服务器时间）",
    )

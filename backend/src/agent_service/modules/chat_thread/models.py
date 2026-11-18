# src/agent_service/modules/chat_thread/models.py

from uuid import UUID, uuid4

from sqlalchemy import BigInteger, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from agent_service.common.models import SQLBase, TimestampMixin


class ChatThread(SQLBase, TimestampMixin):
    """客服会话数据模型

    对应数据库中的 chat_threads 表，用于记录用户的客服聊天会话信息。
    """

    __tablename__ = "chat_threads"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="会话唯一标识 UUID",
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,  # 建议为经常需要按用户查询会话的字段建立索引
        comment="所属用户 ID",
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        default="新会话",
        server_default="新会话",
        comment="会话标题",
    )

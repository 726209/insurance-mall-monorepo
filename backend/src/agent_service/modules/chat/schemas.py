# src/agent_service/modules/chat/schemas.py
from typing import Any
from uuid import UUID

from pydantic import Field

from agent_service.common.schemas import BaseSchema


class ChatRequest(BaseSchema):
    """基础对话请求"""

    thread_id: UUID = Field(..., description="会话 ID")
    message: str | None = Field(default=None, min_length=1, description="消息正文内容")
    decision: dict[str, Any] | None = None

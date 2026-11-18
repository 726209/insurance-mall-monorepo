# src/agent_service/modules/chat_thread/schemas.py

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field, field_validator

from agent_service.common.schemas import BaseSchema


class ChatThreadCreate(BaseSchema):
    """创建会话请求"""

    title: str = Field(default="新会话", min_length=1, max_length=200, description="会话标题")

    @field_validator("title", mode="before")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        """去除标题首尾空格"""
        if isinstance(value, str):
            return value.strip()
        return value


class ChatThreadResponse(BaseSchema):
    """会话响应"""

    id: UUID = Field(..., description="会话唯一标识 UUID")
    title: str = Field(..., description="会话标题")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="最后更新时间")


class ChatMessageResponse(BaseSchema):
    """历史消息"""

    role: Literal["user", "assistant"] = Field(
        ..., description="消息发送角色（user: 用户, assistant: 助手）"
    )
    content: str = Field(..., description="消息正文内容")
    additional_info: dict | None = Field(default_factory=dict, description="附加信息")


class ChatHistoryResponse(BaseSchema):
    """会话历史响应"""

    thread_id: UUID = Field(..., description="会话 ID")
    messages: list[ChatMessageResponse] = Field(..., description="消息历史列表")
    interrupt: Any | None = Field(default=None, description="当前会话的挂起/中断信息（如有）")

# src/agent_service/modules/chat_thread/router.py
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from agent_service.infra.database import get_session
from agent_service.modules.chat_thread.schemas import (
    ChatHistoryResponse,
    ChatThreadCreate,
    ChatThreadResponse,
)
from agent_service.modules.chat_thread.service import ChatThreadService

router = APIRouter(prefix="/api/v1/chat-threads", tags=["会话管理的接口"])


def get_chat_thread_service(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    agent = request.app.state.agent
    return ChatThreadService(session, agent)


"""
curl --url 'http://localhost:5173/api/v1/chat-threads' \
  -H 'Content-Type: application/json' \
  -H 'x-user-id: 1' \
  --data-raw '{"title":"保险咨询"}'
"""


@router.post("", response_model=ChatThreadResponse)
async def create_chat_thread(
    request: ChatThreadCreate,
    user_id: Annotated[int, Header(alias="x-user-id")],
    service: Annotated[ChatThreadService, Depends(get_chat_thread_service)],
):
    """创建会话"""

    return await service.add(user_id, request.title)


"""
curl --url 'http://localhost:5173/api/v1/chat-threads' \
  -H 'Content-Type: application/json' \
  -H 'x-user-id: 1'
"""


@router.get("", response_model=list[ChatThreadResponse])
async def list_by_user(
    user_id: Annotated[int, Header(alias="x-user-id")],
    service: Annotated[ChatThreadService, Depends(get_chat_thread_service)],
):
    """查询会话列表"""
    return await service.list_by_user(user_id)


@router.delete("/{thread_id}", status_code=204)
async def remove(
    thread_id: str,
    user_id: Annotated[int, Header(alias="x-user-id")],
    service: Annotated[ChatThreadService, Depends(get_chat_thread_service)],
):
    """删除会话"""

    await service.remove(user_id, thread_id)


@router.patch("/{thread_id}", response_model=ChatThreadResponse)
async def rename(
    thread_id: str,
    request: ChatThreadCreate,
    user_id: Annotated[int, Header(alias="x-user-id")],
    service: Annotated[ChatThreadService, Depends(get_chat_thread_service)],
):
    """重命名会话"""

    return await service.rename(user_id, thread_id, request.title)


@router.get("/{thread_id}/messages", response_model=ChatHistoryResponse)
async def get_chat_history(
    thread_id: str,
    user_id: Annotated[int, Header(alias="x-user-id")],
    service: Annotated[ChatThreadService, Depends(get_chat_thread_service)],
):
    """查询当前用户的指定会话"""

    return await service.get_chat_history(user_id, thread_id)

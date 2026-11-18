# src/agent_service/modules/chat/router.py
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request
from fastapi.sse import EventSourceResponse, ServerSentEvent
from sqlalchemy.ext.asyncio import AsyncSession

from agent_service.infra.database import get_session
from agent_service.modules.chat.schemas import ChatRequest
from agent_service.modules.chat.service import ChatService

router = APIRouter(prefix="/api/v1/chat", tags=["与AI对话接口"])


def get_chat_service(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    agent = request.app.state.agent
    return ChatService(session, agent)


# sse两步走：
# 1.响应类型response_class=EventSourceResponse，标记响应格式是event_stream格式
# 2.返回值必须用ServerSentEvent包装


"""
curl --url 'http://localhost:5173/api/v1/chat' \
  -H 'Content-Type: application/json' \
  -H 'x-user-id: 1' \
  --data-raw '{"thread_id":"77b4aa37-fb3f-4c1f-90b6-9eede6e71a6d","message":"111"}'
"""


@router.post("/sse", response_class=EventSourceResponse)
async def sse_demo():
    # Generator, 用yield不断生成内容，形成动态列表
    for i in range(10):
        yield ServerSentEvent(data=f"data_{i}", event="message")

    yield ServerSentEvent(data="Don11e", event="done")


@router.post("", response_class=EventSourceResponse)
async def chat(
    request: ChatRequest,
    user_id: Annotated[int, Header(alias="x-user-id")],
    service: Annotated[ChatService, Depends(get_chat_service)],
):
    # Generator, 用yield不断生成内容，形成动态列表
    async for sse in service.chat_stream(user_id, request):
        yield sse

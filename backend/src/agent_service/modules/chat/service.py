# src/agent_service/modules/chat/service.py
from collections.abc import AsyncIterator

from fastapi.sse import ServerSentEvent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from langgraph.stream import CustomTransformer
from langgraph.types import Command
from sqlalchemy.ext.asyncio import AsyncSession

from agent_service.agents.schemas import AdditionalInfo
from agent_service.core.logger.logger import get_logger
from agent_service.modules.chat.schemas import ChatRequest
from agent_service.modules.chat_thread.exceptions import ChatThreadNotFound
from agent_service.modules.chat_thread.repository import ChatThreadRepository

logger = get_logger(__name__)


class ChatService:
    def __init__(self, session: AsyncSession, agent: CompiledStateGraph):
        self.agent = agent
        self.repository = ChatThreadRepository(session)

    async def chat_stream(
        self, user_id: int, request: ChatRequest
    ) -> AsyncIterator[ServerSentEvent]:
        """实现Agent流式对话的函数"""
        thread_id = str(request.thread_id)

        # 1.校验，判断当前thread_id是否属于当前用户
        chat_thread = await self.repository.required_owner(user_id, thread_id)
        if not chat_thread:
            # 指定会话不属于当前用户
            raise ChatThreadNotFound()

        # 2.校验通过后，调用Agent
        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
        if request.decision:
            _input = Command(resume=request.decision)
        else:
            _input = {"messages": [HumanMessage(content=request.message)]}

        # 使用v3协议获取异步事件流
        stream = await self.agent.astream_events(
            input=_input,
            config=config,
            version="v3",
            # 过滤掉不需要的噪音，把大模型吐出的文本流和业务自定义的附加信息（additional_info）精准、
            # 整洁地提取出来，供你的 SSE 接口消费。
            transformers=[CustomTransformer],
            context={"user_id": user_id},
        )
        # 记录AIMessage的ID和引用信息
        final_message_id: str | None = None
        additional_info: AdditionalInfo = {}

        """
        {
            "method": "messages" | "custom" | ...,  # 事件类型/通道名称
            "params": {                             # 事件携带的具体数据包
                "data": [...]                       # 具体的数据列表或对象
            }
        }
        
        method == "messages"（大模型消息流事件）:通常由 MessagesTransformer 等组件产生，用于流式传输大模型的回复内容。   
        method == "custom"（自定义业务事件）:通常由你在图（Graph）的节点内部主动通过 writer 或特定机制抛出，
                                            并由 CustomTransformer 捕获。   
        """
        async for event in stream:
            logger.debug("收到流式事件", event_data=event)
            method = event.get("method")
            # 判断事件类型，可以是messages、interrupts等等
            if method == "messages":
                data = event["params"]["data"][0]
                if isinstance(data, AIMessage):
                    yield ServerSentEvent(data=data.text, event="message")
                elif data.get("delta") and data["delta"].get("text"):
                    yield ServerSentEvent(data=data["delta"].get("text"), event="message")
                elif data.get("event") == "message-start" and data.get("id"):
                    # 第一个消息片段会传递Message的id
                    final_message_id = data.get("id")
            if method == "custom":
                data = event["params"]["data"]
                if isinstance(data, dict) and data.get("type") == "additional_info":
                    additional_info = data.get("data", {})
                    yield ServerSentEvent(data=additional_info, event="additional_info")

        interrupts = await stream.interrupts()
        for item in interrupts:
            yield ServerSentEvent(data=item.value, event="interrupt")

        if final_message_id and additional_info:
            # 将additional_info更新到state中
            await self.agent.aupdate_state(
                config=config, values={"additional_info": {final_message_id: additional_info}}
            )
        # 返回结束标识
        yield ServerSentEvent(data="[DONE]", event="done")

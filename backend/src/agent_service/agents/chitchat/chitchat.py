# src/agent_service/agents/chitchat/chitchat.py

from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, SystemMessage
from langgraph.graph import StateGraph

from agent_service.agents.schemas import InsuranceAgentState
from agent_service.core.configs.config import settings
from agent_service.core.logger.logger import get_logger

logger = get_logger(__name__)

SYSTEM_MESSAGE = """
你是《安心保》商城的智能客服，负责处理与保险业务无关的普通聊天。

要求：
1. 回复友好、自然，最多两句话。
2. 不假装有个人经历、情感、实时信息或外部能力。
3. 不回答医疗、法律、投资、政治等高风险专业建议。
4. 每次回复都自然引导用户回到保险产品、投保或理赔业务。
5. 超出能力范围时，如实说明无法提供。
""".strip()

MAX_CHITCHAT_COUNT = 3


class ChitchatState(InsuranceAgentState):
    """闲聊子Agent状态"""

    chitchat_count: int  # 统计闲聊次数


class ChitChatWorkflow:
    def __init__(self) -> None:
        self._model = init_chat_model(
            model=settings.llm.chat_model,
            api_key=settings.llm.api_key,
            extra_body={"thinking": {"type": "disabled"}},
        )

    def handle_chitchat(self, state: ChitchatState):
        # 取出State中的闲聊次数
        count = state.get("chitchat_count", 0)

        # 取出上一轮次的工作流，如果上一轮次不是闲聊，则重置count
        if state.get("previous_workflow") != "chitchat":
            count = 0

        logger.debug("处理闲聊消息", chitchat_count=count)

        # 判断count是否超出了闲聊的最大轮次
        if count >= MAX_CHITCHAT_COUNT:
            logger.info("闲聊次数超出最大轮次，结束闲聊")
            return {
                "messages": [
                    AIMessage(
                        "我主要协助处理保险产品、投保和理赔咨询，请告诉我想办理或了解的事项。"
                    )
                ]
            }

        logger.debug(f"当前闲聊次数: {count}")
        # 没超过闲聊最大轮次，可以正常对话
        response = self._model.invoke([SystemMessage(SYSTEM_MESSAGE), *state["messages"]])
        return {
            "messages": [response],
            "chitchat_count": count + 1,
        }

    def build(self):
        builder = StateGraph(ChitchatState)

        builder.add_node("chitchat", self.handle_chitchat)

        builder.set_entry_point("chitchat")  # START => chitchat
        builder.set_finish_point("chitchat")  # chitchat => END
        # builder.add_edge(START, "chitchat")
        # builder.add_edge("chitchat", END)

        return builder.compile(checkpointer=True)

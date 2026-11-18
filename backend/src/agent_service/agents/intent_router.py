# src/agent_service/agents/intent_router.py

"""意图识别路由（公共服务）"""

import re
from typing import Literal

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage

from agent_service.agents.schemas import RouteResult
from agent_service.core.configs.config import settings
from agent_service.core.logger.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """
你是保险商城智能客服的意图识别节点，请判断用户消息应该交给哪个工作流。

intent只能从以下选项中选择：
- recommendation_plan：保险产品咨询、产品条款、保险推荐、方案管理和投保咨询
- claim：报案、理赔责任、理赔材料、理赔流程和理赔进度
- human_handoff：投诉、高风险问题或用户明确要求人工服务
- chitchat：与保险业务无关的普通聊天
- fallback：无法判断用户意图
""".strip()


class IntentRouter:
    def __init__(self) -> None:
        model = init_chat_model(
            model=settings.llm.chat_model,
            api_key=settings.llm.api_key,
            extra_body={"thinking": {"type": "disabled"}},
        )
        self._model = model.with_structured_output(RouteResult).with_config(
            {"tags": ["nostream"]}
        )  # tags（标签）：为这次调用打上标签，常用于 LangSmith 监控、过滤和日志追踪。

    def route(
        self,
        message: str,  # 用户本轮提问
        context: str,  # 历史对话上下文（上一轮工作流名字、上一轮AI回复消息）
    ) -> RouteResult | str:
        """规则优先；其他消息异步交给模型识别。"""
        # 0.明确的转人工请求直接处理，减少对模型的依赖。
        normalized_message = normalize_message(message)
        if normalized_message in HumanHandoffFlags:
            return RouteResult(
                intent="human_handoff",
                reason="用户明确请求人工协助",
            )

        # 1.简单寒暄优先使用规则处理
        social_intent = match_social_intent(normalized_message)
        if social_intent:
            response = response_by_social_intent(social_intent)
            if response is not None:
                return response

        # 2.非寒暄消息，交给模型识别
        try:
            result = self._model.invoke(
                [
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(f"历史对话信息：{context}\n用户本轮消息：{message}\n"),
                ]
            )
            logger.debug("模型意图识别完成", route_result=result)
            return RouteResult.model_validate(result)
        except Exception:
            logger.exception("模型意图识别失败")
            return RouteResult(
                intent="fallback",
                reason="模型意图识别失败",
            )


# 人工转接
HumanHandoffFlags = {"转人工", "人工客服", "我要人工客服", "转接人工"}

# 基于规则的识别是否为寒暄
# 寒暄类型枚举
SocialIntent = Literal["greeting", "thanks", "goodbye"]
# 寒暄的匹配规则
SOCIAL_PATTERNS: dict[SocialIntent, tuple[str, ...]] = {
    "greeting": (
        r"(你|您)?好(呀|啊|哦)?",
        r"嗨",
        r"哈喽",
        r"hello",
        r"hi",
        r"在吗",
    ),
    "thanks": (
        r"谢谢(你|您)?",
        r"多谢(你|您)?",
        r"感谢(你|您)?",
        r"辛苦了",
    ),
    "goodbye": (
        r"再见",
        r"拜拜",
        r"先这样",
        r"没事了",
    ),
}
# 寒暄的固定回复
SOCIAL_RESPONSES = {
    "greeting": "您好，我是您的保险顾问，可以帮您咨询产品、推荐方案或办理理赔。",
    "thanks": "不客气，后续有保险问题可以随时问我。",
    "goodbye": "好的，后续需要帮助时随时联系我。",
}


def normalize_message(message: str) -> str:
    """格式化消息，去掉无效字符"""

    return re.sub(r"[\s，。！？、,.!?~～]", "", message).lower()


def match_social_intent(message: str) -> SocialIntent | None:
    """基于规则匹配的路由"""

    for intent, patterns in SOCIAL_PATTERNS.items():
        if any(re.fullmatch(pattern, message) for pattern in patterns):
            return intent
    return None


def response_by_social_intent(intent: SocialIntent):
    """根据规则识别出的意图返回固定回复"""

    return SOCIAL_RESPONSES.get(intent)


intent_router = IntentRouter()

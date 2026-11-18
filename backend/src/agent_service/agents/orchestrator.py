# src/agent_service/agents/orchestrator.py

"""【主编排器】负责顶层路由、多 Agent 调度图"""
from typing import Sequence, cast

from IPython.core.display import Image
from IPython.core.display_functions import display
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.runnables.graph import MermaidDrawMethod, CurveStyle, NodeStyles
from langchain_core.runnables.graph_mermaid import draw_mermaid_png
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.constants import END, START
from langgraph.graph import StateGraph
from langgraph.types import Command, Send

from agent_service.agents.chitchat import init_chitchat_workflow
from agent_service.agents.claim import init_claim_advisor
from agent_service.agents.intent_router import intent_router, logger
from agent_service.agents.recommendation import init_insurance_advisor
from agent_service.agents.schemas import InsuranceAgentState, Intent, InsuranceAgentContext
from agent_service.core.configs.config import APP_ROOT


def find_previous_ai_message(messages: Sequence[BaseMessage]) -> str:
    """查找本轮用户消息之前最近一条可展示的AI回复"""

    for message in reversed(messages[:-1]):
        # 跳过非AIMessage
        if not isinstance(message, AIMessage):
            continue
        # 跳过工具消息
        if message.tool_calls:
            continue
        # 如果是正常AIMessage，直接返回
        if message.text:
            return message.text
    # 如果是空消息
    return ""


# 一、定义节点
# 1.路由节点
async def route_node(state: InsuranceAgentState) -> Command[Intent]:
    """识别意图，并统一维护跨轮次的计数。"""

    # 1.获取active_workflow，也就是上一轮会话的工作流
    previous_workflow = state.get("active_workflow", "无")
    # 2.获取上轮AI消息
    previous_ai_message = find_previous_ai_message(state["messages"])
    # 3.拼接上下文
    context = (
        f"上轮对话工作流:{previous_workflow}\n"
        f"上轮对话AI回复:{previous_ai_message}"
    )
    # 4.意图识别
    result = intent_router.route(state["messages"][-1].text, context)
    # 4.1.返回str，说明是寒暄，直接返回固定回复，跳至END
    if isinstance(result, str):
        return Command[Intent](
            update={
                "messages": [AIMessage(content=result)],
                "previous_workflow": previous_workflow,
                "active_workflow": "chitchat",
            },
            goto=END,
        )
    # 4.2.返回RouteResult，记录上轮工作流、本轮工作流
    return Command[Intent](
        update={
            "active_workflow": result.intent,
            "previous_workflow": previous_workflow,
        },
        goto=result.intent,
    )


# # 2.闲聊节点
# async def chitchat_node(state: InsuranceAgentState) -> dict:
#       # 保留统一的节点参数签名，当前实现暂不读取会话状态。
#       _ = state
#     return {"messages": [AIMessage("你好，今天想聊点什么？")]}


# # 3.保险推荐节点
# async def recommendation_node(state: InsuranceAgentState) -> dict:
#       # 保留统一的节点参数签名，当前实现暂不读取会话状态。
#       _ = state
#     return {"messages": [AIMessage("保险推荐工作流暂未接入。")]}


# 4.理赔节点
# async def claim_node(state: InsuranceAgentState) -> dict:
#       # 保留统一的节点参数签名，当前实现暂不读取会话状态。
#       _ = state
#     return {"messages": [AIMessage("理赔工作流暂未接入。")]}


# 5.人工节点
def human_handoff_node(state: InsuranceAgentState) -> dict:
    """人工转接节点：响应用户转人工请求。"""

    # 保留统一的节点参数签名，当前实现暂不读取会话状态。
    _ = state
    return {"messages": [AIMessage("已记录转人工请求，后续可接入人工客服系统。")]}


# 6.fallback节点
def fallback_node(state: InsuranceAgentState) -> dict:
    _ = state
    return {
        "messages": [AIMessage("我还不能确定你的需求，请说明是想咨询保险、推荐方案还是办理理赔。")]
    }


# 二、定义主Graph
def init_insurance_agent(checkpointer: AsyncPostgresSaver):
    """初始化保险顾问主Graph"""
    builder = StateGraph(
        state_schema=InsuranceAgentState,
        # 明确主图上下文类型，保证各子图收到一致的用户上下文。
        # 为整个 Agent 图（Graph）或其节点（Nodes）/工具（Tools）注入全局的、只读的运行时上下文数据
        # （例如当前登录用户的 user_id、租户 ID、环境配置、数据库会话指针等）。
        context_schema=InsuranceAgentContext, # type: ignore[arg-type]
    )

    # 添加节点
    builder.add_node("route", route_node)
    builder.add_node("chitchat", init_chitchat_workflow())
    builder.add_node("recommendation_plan", init_insurance_advisor())
    builder.add_node("claim", init_claim_advisor())
    builder.add_node("human_handoff", human_handoff_node)
    builder.add_node("fallback", fallback_node)
    # 添加 Edge
    builder.add_edge(START, "route")
    builder.add_edge("chitchat", END)
    builder.add_edge("recommendation_plan", END)
    builder.add_edge("claim", END)
    builder.add_edge("human_handoff", END)
    builder.add_edge("fallback", END)

    graph= builder.compile(checkpointer=checkpointer)

    return graph





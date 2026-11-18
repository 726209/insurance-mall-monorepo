# src/agent_service/agents/chitchat/__init__.py

"""闲聊模块"""

from langgraph.graph.state import CompiledStateGraph

from agent_service.agents.chitchat.chitchat import ChitChatWorkflow


def init_chitchat_workflow() -> CompiledStateGraph:
    return ChitChatWorkflow().build_chitchat_graph()


__all__ = ["init_chitchat_workflow"]

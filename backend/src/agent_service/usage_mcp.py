# src/agent_service/usage_mcp.py

import asyncio
from typing import cast

from langchain.agents import create_agent
from langchain.agents.middleware import InputAgentState
from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import Connection
from rich import print as rich_print


async def main():
    connections:dict[str, Connection] = {
            "time-mcp": {"transport": "stdio", "command": "npx", "args": ["-y", "time-mcp"]},
            "12306-mcp": {
                "transport": "streamable_http",
                "url": "https://mcp.api-inference.modelscope.net/adce99251c7041/mcp",
            },
        }
    client = MultiServerMCPClient(connections)  # https://modelscope.cn/mcp/servers/zac2ma/Time-MCP
    tools = await client.get_tools()
    print(f"成功加载了 {len(tools)} 个 MCP 工具：")
    for tool in tools:
        print(f"- {tool.name}: {tool.description}")
    agent = create_agent(
        # model="ollama:qwen2.5:7b",
        model="deepseek:deepseek-flash",
        tools=tools,
    )

    # 4. 执行调用
    # response = await agent.ainvoke({"messages": [("user", "现在几点了？")]})
    # print(response)

    input_data = cast(
        InputAgentState,
        {
            "messages": [
                # HumanMessage(content="一句话介绍你自己？，顺便告诉我现在的北京时间是多少？"),
                HumanMessage(content="帮我查询一下下周四从北京到杭州的高铁？"),
            ]
        }
    )
    response = await agent.ainvoke(input_data)
    rich_print(response)


if __name__ == "__main__":
    asyncio.run(main())

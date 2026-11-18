# src/agent_service/agents/tools.py

import json

from langchain_core.tools import tool
from langgraph.config import get_stream_writer

# 【通过 RAG 检索保险条款】
# 根据用户的问题（query）、指定数量（k）和产品 ID（product_id），
# 去向量数据库（Milvus）中检索对应的保险产品条款
@tool
async def query_product_clause(
        query: str,
        k: int,
        product_id: int,
) -> str:
    """查询指定保险产品的条款内容。

    Args:
        query: 需要从保险条款中查询的问题。
        k: 返回的文档数量。
        product_id: 保险产品ID。
    """
    from agent_service.rag import retriever

    chunks = await retriever.retrieve(query, k, product_id)
    if not chunks:
        return "没有查询到相关保险条款。"

    sources = {
        f"ref-{i:03d}": {
            "product_id": chunk.product_id,
            "clause_name": chunk.clause_name,
            "section_path": chunk.section_path,
            "content": chunk.content,
        }
        for i, chunk in enumerate(chunks, start=1)
    }

    writer = get_stream_writer()
    writer({"type": "additional_info", "data": sources})

    return json.dumps(sources, ensure_ascii=False)
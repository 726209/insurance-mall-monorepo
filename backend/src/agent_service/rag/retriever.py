# src/agent_service/rag/retriever.py
import asyncio

from langchain_milvus import BM25BuiltInFunction, Milvus
from langchain_ollama import OllamaEmbeddings
from pymilvus import Function, FunctionType

from agent_service.core.configs.config import settings
from agent_service.core.logger.logger import get_logger
from agent_service.infra.database import AsyncSessionFactory
from agent_service.rag.models import ParentChunk
from agent_service.rag.repository import ParentChunkRepository

logger = get_logger(__name__)


def create_reranker(query: str) -> Function:
    """milvus的reranker function，这里采用ali的重排模型"""
    return Function(
        name="dashscope_semantic_ranker",
        input_field_names=["text"],
        function_type=FunctionType.RERANK,
        params={
            "reranker": "model",
            "provider": "ali",
            "model_name": "gte-rerank-v2",
            "queries": [query],
            "max_client_batch_size": 5,
        },
    )


class ParentChunkRetriever:
    def __init__(self, vector_store: Milvus):
        self.vector_store = vector_store
        logger.info("RAG Retriever 初始化完成✅️")

    async def retrieve(self, query: str, k: int, product_id: int) -> list[ParentChunk]:
        # 1.在指定产品内混合检索并重排，得到子块
        child_chunks = await self.vector_store.asimilarity_search(
            query,
            k=k,  # 返回得分最高的K条
            fetch_k=10,  # 初筛时返回文档的数量
            expr=f"product_id == {product_id}",
            reranker=create_reranker(query),
        )
        # 2.提取parent_id，并按照召回顺序去重
        parent_ids = list(dict.fromkeys(child.metadata["parent_id"] for child in child_chunks))
        if not parent_ids:
            return []
        # 3.根据parent_id批量查询父块
        async with AsyncSessionFactory() as session:
            repository = ParentChunkRepository(session)
            parent_chunks = await repository.query_by_ids(parent_ids)

        # 4.按照子块召回顺序组装父文档
        # 4.1.先组装dict[parent_id, parent_chunk]
        parent_chunk_map = {str(parent.id): parent for parent in parent_chunks}
        # 4.2.按照召回的parent_ids顺序遍历，再到dict中拿到parent
        return [
            parent_chunk_map[parent_id]  # 推导式的结果
            for parent_id in parent_ids  # 推导式数据来源
        ]


async def main():
    # 1.初始化向量模型
    embeddings = OllamaEmbeddings(
        model="qwen3-embedding:4b",  # 性价比高的模型
        dimensions=1024,  # 可选：减少维度以节省存储
    )

    # 2、初始化 VectorStore，会自动创建Collection
    vector_store = Milvus(
        embedding_function=embeddings,
        collection_name="insurance_collection",
        builtin_function=BM25BuiltInFunction(analyzer_params={"type": "chinese"}),
        vector_field=["dense", "sparse"],
        connection_args={"uri": settings.rag.milvus_url},
        auto_id=True,
    )

    retriever = ParentChunkRetriever(vector_store)
    parent_chunks = await retriever.retrieve(
        query="保险合同的等待期是多久？",
        k=5,
        product_id=1,
    )
    for parent_chunk in parent_chunks:
        print("=" * 80)
        print("product_id =", parent_chunk.product_id)
        print("clause_name =", parent_chunk.clause_name)
        print("section_path =", parent_chunk.section_path)
        print("content =", parent_chunk.content)


if __name__ == "__main__":
    asyncio.run(main())

# src/agent_service/rag/__init__.py
from langchain_milvus import BM25BuiltInFunction, Milvus
from langchain_ollama import OllamaEmbeddings

from agent_service.core.configs.config import settings
from agent_service.rag.pipeline import RAGPipeline
from agent_service.rag.retriever import ParentChunkRetriever

# 1.初始化向量模型
_embeddings = OllamaEmbeddings(
    model="qwen3-embedding:4b",  # 性价比高的模型
    dimensions=1024,  # 可选：减少维度以节省存储
)

# 2、初始化 VectorStore，会自动创建Collection
_vector_store = Milvus(
    embedding_function=_embeddings,
    collection_name="insurance_collection",
    builtin_function=BM25BuiltInFunction(analyzer_params={"type": "chinese"}),
    vector_field=["dense", "sparse"],
    connection_args={"uri": settings.rag.milvus_url},
    auto_id=True,
)

# 3.创建模块级Pipeline和Retriever
pipeline = RAGPipeline(_vector_store)
retriever = ParentChunkRetriever(_vector_store)


def close_rag() -> None:
    """关闭RAG组件"""
    pipeline.close()
    _vector_store.client.close()


__all__ = ["pipeline", "retriever", "close_rag"]

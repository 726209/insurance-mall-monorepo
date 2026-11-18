# scripts/ingest_rag.py

"""
初始化脚本包括：
- 初始化EmbeddingModel
- 初始化VectorStore
- 初始化Pipeline
- 查询保险条款信息
- 调用Pipeline，生成RAG知识库
"""

import asyncio
import time

from langchain_milvus import BM25BuiltInFunction, Milvus
from langchain_ollama import OllamaEmbeddings

from agent_service.core.configs.config import settings
from agent_service.core.logger.logger import get_logger
from agent_service.infra.database import AsyncSessionFactory, close_database
from agent_service.modules.product.models import Product
from agent_service.modules.product.repository import ProductRepository
from agent_service.rag.pipeline import RAGPipeline

logger = get_logger(__name__)


def create_vector_store() -> Milvus:
    # 1.初始化向量模型
    embeddings = OllamaEmbeddings(
        model="qwen3-embedding:4b",  # 性价比高的模型
        dimensions=1024,  # 可选：减少维度以节省存储
    )
    # 2、初始化 VectorStore，会自动创建Collection
    return Milvus(
        embedding_function=embeddings,
        collection_name="insurance_collection",
        builtin_function=BM25BuiltInFunction(analyzer_params={"type": "chinese"}),
        vector_field=["dense", "sparse"],
        connection_args={"uri": settings.rag.milvus_url},
        auto_id=True,
    )


async def find_all_products() -> list[Product]:
    async with AsyncSessionFactory() as session:
        repository = ProductRepository(session)
        return await repository.query_by_category()


async def main() -> None:
    start_time = time.perf_counter()  # 记录整体开始时间
    vector_store = create_vector_store()
    pipeline = RAGPipeline(vector_store)

    success_count = 0
    fail_count = 0

    try:
        products = await find_all_products()
        logger.info("开始构建RAG知识库", product_count=len(products))
        for index, product in enumerate(products, start=1):
            product_start_time = time.perf_counter()  # 记录单产品处理开始时间
            logger.info(
                "开始处理保险产品",
                progress=f"{index}/{len(products)}",
                product_id=product.id,
                product_name=product.name,
            )
            try:
                await pipeline.ingest(product)
                product_cost = time.perf_counter() - product_start_time
                success_count += 1
                logger.info(
                    "保险产品处理成功",
                    progress=f"{index}/{len(products)}",
                    product_id=product.id,
                    product_name=product.name,
                    cost_seconds=round(product_cost, 2),
                )
            except Exception as e:
                product_cost = time.perf_counter() - product_start_time
                fail_count += 1
                logger.error(
                    "保险产品处理失败",
                    progress=f"{index}/{len(products)}",
                    product_id=product.id,
                    product_name=product.name,
                    error=str(e),
                    cost_seconds=round(product_cost, 2),
                )
        total_cost = time.perf_counter() - start_time
        logger.info(
            "RAG知识库构建完成",
            total_products=len(products),
            success_count=success_count,
            fail_count=fail_count,
            total_cost_seconds=round(total_cost, 2),
        )
    finally:
        pipeline.close()
        vector_store.client.close()
        await close_database()


if __name__ == "__main__":
    asyncio.run(main())

# src/agent_service/infra/checkpointer.py


from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from agent_service.core.configs.config import settings
from agent_service.core.logger.logger import get_logger

logger = get_logger(__name__)

# 0.创建 checkpointer 专用连接池
checkpoint_pool = AsyncConnectionPool(
    conninfo=settings.db.checkpoint_url,
    min_size=1,  # 池最小连接数
    max_size=5,  # 池最大连接数
    kwargs={
        "autocommit": True,  # 自动提交事务
        "prepare_threshold": 0,  # 不做预准备sql
        "row_factory": dict_row,  # 查询结果以dict返回
    },
    open=False,  # 不自动创建连接
)


async def init_checkpointer():
    """初始化 checkpointer"""

    # 1.初始化连接池
    # 初始化连接
    await checkpoint_pool.open()
    # 等待连接池就绪
    await checkpoint_pool.wait()

    # 2.创建 checkpointer
    checkpointer = AsyncPostgresSaver(checkpoint_pool)

    # 自动建表（与checkpointer存储有关的表）
    await checkpointer.setup()
    logger.info("Checkpointer 连接池初始化成功~✅️")
    return checkpointer


# 3.关闭连接
async def close_checkpointer() -> None:
    """关闭 checkpointer 连接池"""
    await checkpoint_pool.close()
    logger.info("Checkpointer 连接池已关闭~")

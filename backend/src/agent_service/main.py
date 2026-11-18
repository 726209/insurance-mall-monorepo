# src/agent_service/main.py
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from starlette.responses import JSONResponse

from agent_service.agents.orchestrator import init_insurance_agent
from agent_service.core.configs.config import settings
from agent_service.core.exceptions import ApplicationError
from agent_service.core.logger.logger import configure_logging, get_logger
from agent_service.router import register_router

# 初始化日志系统
configure_logging(settings.logging.level)

logger = get_logger(__name__)


# 生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"【{settings.app.name}】应用启动中...")
    from agent_service.infra.checkpointer import close_checkpointer, init_checkpointer
    from agent_service.infra.database import check_database, close_database
    from agent_service.rag.rag import close_rag

    try:
        # 1.初始化数据库连接池
        await check_database()
        # 2.初始化Checkpointer
        checkpointer = await init_checkpointer()
        # 3.初始化Agent,并将其保存在FastAPI的全局State中，一切进入FastAPI的请求都共享这个State
        app.state.agent = init_insurance_agent(checkpointer)

        yield
    finally:
        logger.info("应用关闭中... ")
        # 4.关闭rag
        close_rag()
        # 5.关闭数据库连接池
        await close_database()
        # 6.关闭Checkpointer连接池
        await close_checkpointer()


# 初始化FastAPI
app = FastAPI(
    title=settings.app.name,
    debug=settings.app.debug,
    lifespan=lifespan,
)


@app.get("/health", summary="健康检测接口")
async def health_check() -> dict[str, str]:
    logger.info("执行健康检查")
    return {"status": "ok"}


# 统一处理异常信息，发现是ChatThreadNotFound，返回对应的错误状态码和错误信息
@app.exception_handler(ApplicationError)
def handle_exception(request: Request, exc: ApplicationError):
    logger.error(f"处理异常, 请求路径: {request.url}, 异常信息: {exc}")
    return JSONResponse(
        status_code=exc.status_code,  # http状态码
        content={
            "code": exc.code,  # 错误码， error_code
            "message": exc.message,  # 错误消息，error_message
        },
    )


register_router(app)

if __name__ == "__main__":
    uvicorn.run(
        "agent_service.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=False,
        loop="asyncio:SelectorEventLoop" if sys.platform == "win32" else "auto",
    )


"""
在实际项目开发中，业务会很复杂，业务领域也很多，为了方便管理，项目必须按照职责严格划分不同的包和模
块。而项目的职责主要可以分为：
• core：核心模块
• infra：基础设施模块
• common：通用模块
• modules：业务模块，主要是实现数据库的CRUD以及与前端对接。
业务模块再按照处理前端请求的流程划分，通常流程如下图所示：
schemas 请求、响应数据约束
models 数据库表映射类 前端
router 校验请求参数 返回响应结果
service 业务逻辑开发
→
repository 数据库的crud操作
数据库
"""

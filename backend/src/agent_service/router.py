# src/agent_service/router.py

from agent_service.modules.chat.router import router as chat_router
from agent_service.modules.chat_thread.router import router as chat_thread_router
from agent_service.modules.product.router import router as product_router


def register_router(app):
    app.include_router(chat_router)
    app.include_router(chat_thread_router)
    app.include_router(product_router)

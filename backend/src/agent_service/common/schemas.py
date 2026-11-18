# src/agent_service/common/schemas.py

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PageResult[T](BaseSchema):
    """通用分页结果"""

    items: list[T]
    page: int
    page_size: int
    total: int

# src/agent_service/modules/product/schemas.py

from decimal import Decimal

from pydantic import Field, field_validator

from agent_service.common.schemas import BaseSchema


class ProductResponse(BaseSchema):
    """保险产品响应结果"""

    id: int = Field(..., description="产品唯一标识 ID")
    name: str = Field(..., description="产品名称")
    clause_name: str = Field(..., description="主条款文件名（包含.pdf后缀）")
    category: str = Field(
        ...,
        description="险种分类（medical: 医疗险, critical_illness: 重疾险, accident: 意外险, life: 寿险）",
    )
    insurer: str = Field(..., description="承保保险公司")
    image_url: str = Field(..., description="产品图标或封面图片链接")
    description: str = Field(..., description="产品简介")

    # 对于可选字段（允许 None），可以加上默认值 None
    min_premium: Decimal | None = Field(None, description="产品公开的最低年缴保费参考")
    max_premium: Decimal | None = Field(None, description="产品公开的最高保费参考，可为空")
    target_group: str | None = Field(None, description="投保适用人群说明")

    highlights: list[str] = Field(default_factory=list, description="产品核心亮点标签列表")
    status: str = Field(..., description="产品状态（如：active-上架, inactive-下架）")

    @field_validator("highlights", mode="before")
    @classmethod
    def normalize_highlights(cls, value: list[str] | None) -> list[str]:
        return value or []

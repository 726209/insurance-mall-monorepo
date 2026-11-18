# src/agent_service/agents/claim/tools.py

"""保险理赔的专属工具"""

from datetime import datetime

# ==================== 一、 常量标签映射字典 ====================
# 用于将数据库中的英文状态码/类型码转换为前端或大模型易读的中文描述

CLAIM_STATUS_LABEL = {
    "submitted": "已提交",
    "reviewing": "审核中",
    "approved": "已通过",
    "rejected": "已拒赔",
    "paid": "已赔付",
}

POLICY_STATUS_LABEL = {
    "pending": "待生效",
    "active": "保障中",
    "expired": "已过期",
    "terminated": "已终止",
}

CLAIM_TYPE_LABEL = {
    "medical": "医疗",
    "accident": "意外",
    "critical_illness": "重疾",
    "life": "寿险",
}

# 各险种对应的理赔指引与材料要求文案
CLAIM_GUIDES = {
    "medical": (
        "住院医疗理赔一般需要：理赔申请书、身份证、银行卡、诊断证明、出院小结、费用清单和发票。"
        "先向医院开齐材料，再向承保公司提交；审核周期常见 5-15 个工作日。"
    ),
    "accident": (
        "意外医疗/伤残理赔一般需要：理赔申请书、身份证、事故说明、门急诊病历或鉴定报告、费用票据。"
        "若涉及交通事故，还需交警事故认定书。"
    ),
    "critical_illness": (
        "重疾理赔一般需要：理赔申请书、身份证、保单号、专科医生诊断证明、病理或影像学检查报告。"
        "以条款疾病定义为准，确诊后尽快报案。"
    ),
    "life": (
        "身故理赔一般需要：理赔申请书、被保人死亡证明、关系证明、受益人身份证件和保单。"
        "复杂案件建议转人工协助。"
    ),
    "general": (
        "理赔常见步骤：1. 出险后尽快报案；2. 按险种准备申请书和证明材料；"
        "3. 提交承保公司审核；4. 关注审核进度，补充材料后重新审核。"
        "下载申请书可使用链接 {{download_url}}。"
    ),
}


# ==================== 二、 数据序列化辅助函数 ====================
def _format_dt(value: datetime | None) -> str | None:
    """将 datetime 对象安全转换为 ISO 格式字符串，若为空则返回 None"""
    return value.isoformat() if value else None


# def serialize_policy(policy: Policy, product: Product | None) -> dict:
#     """将保单对象及关联的产品信息序列化为前端友好的标准字典结构"""
#     return {
#         "id": str(policy.id),
#         "user_id": policy.user_id,
#         "product_id": policy.product_id,
#         "policy_number": policy.policy_number,
#         "status": policy.status,
#         "effective_at": _format_dt(policy.effective_at),
#         "expires_at": _format_dt(policy.expires_at),
#         "application_no": policy.application_no,
#         "holder_name": policy.holder_name,
#         "insured_name": policy.insured_name,
#         "insured_phone": policy.insured_phone,
#         "insured_id_no_masked": policy.insured_id_no_masked,
#         "coverage_amount": policy.coverage_amount,
#         "premium_amount": policy.premium_amount,
#         "payment_frequency": policy.payment_frequency,
#         "policy_snapshot": policy.policy_snapshot,
#         "coverage_snapshot": policy.coverage_snapshot,
#         # 若关联了产品信息，一并序列化
#         "product": {
#             "id": product.id,
#             "name": product.name,
#             "category": product.category,
#             "image_url": product.image_url,
#             "insurer": product.insurer,
#         }
#         if product
#         else None,
#     }
#
#
# def serialize_claim(
#     claim: Claim,
#     policy: Policy | None,
#     product: Product | None,
# ) -> dict:
#     """将理赔案件对象、关联保单及产品信息序列化为标准字典结构"""
#     return {
#         "id": str(claim.id),
#         "claim_number": claim.claim_number,
#         "claim_type": claim.claim_type,
#         "claim_type_label": CLAIM_TYPE_LABEL.get(claim.claim_type, claim.claim_type),
#         "amount": claim.amount,
#         "description": claim.description,
#         "status": claim.status,
#         "status_label": CLAIM_STATUS_LABEL.get(claim.status, claim.status),
#         "submitted_at": _format_dt(claim.submitted_at),
#         "updated_at": _format_dt(claim.updated_at),
#         "policy_number": policy.policy_number if policy else None,
#         "product_name": product.name if product else None,
#         "product_id": claim.product_id,
#     }
#
#
# # ==================== 三、 Agent 工具定义 (Tools) ====================
#
# @tool
# async def query_user_policies(
#     runtime: ToolRuntime[InsuranceAgentContext],
#     policy_number: str | None = None,
# ) -> list[dict]:
#     """查询当前用户的保单列表或指定保单。用户询问我的保单、保障期间、保单号时使用。
#
#     Args:
#         policy_number: 可选，精确匹配保单号。
#     """
#     # 1. 使用异步会话从数据库中查询用户的保单数据
#     async with AsyncSessionFactory() as session:
#         repository = PolicyRepository(session)
#         if policy_number:
#             # 按指定的保单号精准查询
#             row = await repository.find_by_number(runtime.context.user_id, policy_number)
#             rows = [row] if row else []
#         else:
#             # 查询该用户旗下的所有保单
#             rows = await repository.list_by_user(runtime.context.user_id)
#
#     # 2. 序列化查询结果
#     policies = [serialize_policy(policy, product) for policy, product in rows]
#
#     # 3. 利用 LangGraph 的 stream writer 向外推送结构化的侧边栏/附加业务数据 (additional_info)
#     writer = get_stream_writer()
#     writer({"type": "additional_info", "data": {"policies": policies}})
#
#     # 4. 若无数据则返回空列表，否则使用 fastapi 编码器序列化后返回给大模型
#     if not policies:
#         return []
#     return jsonable_encoder(policies)
#
#
# @tool
# async def query_claim_progress(
#     runtime: ToolRuntime[InsuranceAgentContext],
#     claim_number: str | None = None,
#     policy_number: str | None = None,
# ) -> list[dict]:
#     """查询当前用户的理赔进度。用户问理赔到哪一步、案件号、审核结果时使用。
#
#     Args:
#         claim_number: 可选，理赔案件号，如 CLM-DEMO-2026-0001。
#         policy_number: 可选，按保单号筛选理赔记录。
#     """
#     # 1. 异步查询理赔记录
#     async with AsyncSessionFactory() as session:
#         repository = ClaimRepository(session)
#         rows = await repository.list_by_user(
#             runtime.context.user_id,
#             claim_number=claim_number,
#             policy_number=policy_number,
#         )
#
#     # 2. 序列化理赔案件列表
#     claims = [
#         serialize_claim(claim, policy, product)
#         for claim, policy, product in rows
#     ]
#
#     # 3. 提取理赔关联的保单，去重后同样通过 stream 推送给前端（方便前端在聊天气泡旁渲染保单卡片）
#     related_policies = []
#     seen: set[str] = set()
#     for claim, policy, product in rows:
#         if policy and str(policy.id) not in seen:
#             seen.add(str(policy.id))
#             related_policies.append(serialize_policy(policy, product))
#
#     if related_policies:
#         writer = get_stream_writer()
#         writer({"type": "additional_info", "data": {"policies": related_policies}})
#
#     return jsonable_encoder(claims)
#
#
# @tool
# def query_claim_guide(claim_type: str | None = None) -> str:
#     """说明理赔流程、所需材料和注意事项。用户问怎么报案、要准备什么材料时使用。
#
#     Args:
#         claim_type: 可选，medical / accident / critical_illness / life。
#     """
#     # 根据传入的险种类型匹配对应的理赔指南，未匹配到则退化为 general 通用指南
#     key = claim_type if claim_type in CLAIM_GUIDES else "general"
#     return CLAIM_GUIDES[key]

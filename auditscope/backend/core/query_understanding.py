"""查询理解（Qwen 编排）。

Seam: parse_query(text) -> StructuredQuery
- 有 Qwen key 时调用大模型做意图/实体解析；
- 无 key 时降级为本地关键词规则（保证演示可跑、可测）。
这是 deep module：调用方只关心结构化结果，不关心走模型还是规则。
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import httpx

from core.config import settings

# 实体类型 -> 关键词（降级规则）
ENTITY_HINTS = {
    "company": ["公司", "企业", "有限", "股份", "集团", "科技", "供应链", "数据"],
    "boss": ["老板", "法人", "股东", "实控", "董事长", "控股", "创始人"],
    "person": ["人员", "员工", "财务", "出纳", "经理", "总监", "任职", "个人"],
    "flow": ["流水", "转账", "公转私", "回款", "资金", "银行", "往来", "异常"],
    "social": ["社保", "缴费", "养老", "公积金", "参保", "五险"],
}
INTENT_HINTS = {
    "risk": ["风险", "异常", "失信", "涉诉", "高消费", "违规"],
    "relation": ["关系", "控股", "任职", "关联", "穿透", "图谱"],
    "detail": ["详情", "信息", "查询", "是什么"],
}


@dataclass
class StructuredQuery:
    raw: str
    entity_type: Optional[str] = None          # company/boss/person/flow/social
    intent: str = "detail"                      # risk/relation/detail
    keywords: list[str] = field(default_factory=list)
    confident: bool = False                     # True=模型解析, False=规则降级


def _rule_parse(text: str) -> StructuredQuery:
    t = text.lower()
    etype = None
    for k, hints in ENTITY_HINTS.items():
        if any(h in t for h in hints):
            etype = k
            break
    intent = "detail"
    for k, hints in INTENT_HINTS.items():
        if any(h in t for h in hints):
            intent = k
            break
    kws = [w for w in t.replace(" ", "").split("，") if w]
    return StructuredQuery(raw=text, entity_type=etype, intent=intent, keywords=kws)


async def parse_query(text: str) -> StructuredQuery:
    """解析自然语言查询为结构化查询（Qwen 优先，规则兜底）。"""
    if not settings.qwen_api_key:
        return _rule_parse(text)
    try:
        sys = ("你是审计信息查询的查询理解器。把用户输入解析为 JSON："
               '{"entity_type":"company|boss|person|flow|social|null",'
               '"intent":"risk|relation|detail","keywords":[...]}。只输出 JSON。')
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(
                f"{settings.qwen_base}/chat/completions",
                headers={"Authorization": f"Bearer {settings.qwen_api_key}"},
                json={"model": "qwen-plus", "messages": [
                    {"role": "system", "content": sys},
                    {"role": "user", "content": text},
                ]},
            )
            r.raise_for_status()
            import json
            content = r.json()["choices"][0]["message"]["content"]
            data = json.loads(content)
            return StructuredQuery(
                raw=text,
                entity_type=data.get("entity_type"),
                intent=data.get("intent", "detail"),
                keywords=data.get("keywords", []),
                confident=True,
            )
    except Exception:
        return _rule_parse(text)

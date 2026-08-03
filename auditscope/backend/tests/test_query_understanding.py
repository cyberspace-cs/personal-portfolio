"""TDD：查询理解 seam 测试（规则降级路径，独立真值）。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.query_understanding import _rule_parse, StructuredQuery


def test_rule_parse_company():
    sq = _rule_parse("星河智能科技有限公司 风险")
    assert sq.entity_type == "company"
    assert sq.intent == "risk"
    assert sq.confident is False


def test_rule_parse_boss():
    sq = _rule_parse("查老板 李文博 控股关系")
    assert sq.entity_type == "boss"
    assert sq.intent == "relation"


def test_rule_parse_flow_anomaly():
    sq = _rule_parse("公转私 资金异常")
    assert sq.entity_type == "flow"
    assert sq.intent == "risk"


def test_rule_parse_social():
    sq = _rule_parse("社保 缴费缺口")
    assert sq.entity_type == "social"


def test_rule_parse_default_detail():
    sq = _rule_parse("陈嘉禾")
    # 名字无实体关键词，退化为 detail
    assert sq.intent == "detail"

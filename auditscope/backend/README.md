# AuditScope 后端 — 微服务架构

面向「审计综合信息查询（审查查）」的后端。按 **deep module / 清晰 seam** 原则设计：
网关对外只暴露一个薄接口，复杂检索、向量、LLM 编排都藏在各子模块内部。

## 1. 架构总览

```
                ┌─────────────────────────────────────────┐
   浏览器/前端 ──▶│  gateway  (FastAPI :8000)  /api/v1       │  ← 唯一对外入口
                │   · 鉴权/限流 · 聚合 · 缓存命中 · 降级      │
                └───┬───────┬───────┬───────┬───────┬──────┘
                    │       │       │       │       │
            ┌───────▼┐ ┌────▼────┐ ┌▼──────┐ ┌▼─────┐ ┌▼──────┐
            │company │ │ person  │ │ flow  │ │social│ │  rag   │  子服务(进程内模块/可拆独立服务)
            │ -svc   │ │ -svc    │ │ -svc  │ │ -svc │ │ -svc   │
            └───┬────┘ └───┬─────┘ └──┬────┘ └──┬────┘ └──┬────┘
                │          │          │         │         │
            ┌───▼──────────▼──────────▼─────────▼─────────▼───┐
            │  PostgreSQL 16  │  Milvus 2.4  │  Redis 7        │   infra
            │  (结构化数据)    │  (向量/RAG)  │  (缓存/限流)    │
            └─────────────────┴──────────────┴─────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  LLM 编排层         │  Deepseek(问答/RAG) + Qwen(查询理解)
                    └───────────────────┘
```

> 说明：本仓库为 **单仓库多模块**（gateway 在进程内调用子服务模块），通过 `docker-compose`
> 可把每个 `*-svc` 拆成独立容器；当前为简化部署先以模块方式组织，seam 已预留。

## 2. 模块与 seam（对外接口）

| 模块 | 目录 | 对外 seam（接口） | 内部实现 |
|------|------|-------------------|----------|
| 网关 | `gateway/` | `POST /api/v1/search`、`POST /api/v1/rag/ask`、各资源路由 | 聚合 + 缓存 + 降级 |
| 查询理解 | `core/query_understanding.py` | `parse_query(text) -> StructuredQuery` | Qwen 调用 + 规则兜底 |
| 公司检索 | `services/company.py` | `search_companies(q) -> List[Company]` | PG 查询 |
| 人员/老板 | `services/person.py` | `search_persons`、`search_bosses` | PG 查询 |
| 流水 | `services/flow.py` | `search_flows`、`detect_anomalies` | PG + Milvus 相似 |
| 社保 | `services/social.py` | `search_social` | PG 查询 |
| 向量/RAG | `core/rag.py` | `retrieve(q)`、`answer(q)` | Milvus + Redis + Deepseek |
| 缓存 | `core/cache.py` | `get/set` | Redis（可内存兜底） |

## 3. 数据模型（PostgreSQL，SQLAlchemy 2.0）

- `companies`：id, name, credit_code, legal_person, reg_capital, established, industry, status, risk, score, tags(JSON), address
- `persons`：id, name, id_card_mask, title, company_id, social_connected, risk
- `bosses`：id, name, id_card_mask, held_count, total_capital, risk
- `holdings`：boss_id, company_id, role, ratio  （老板—公司控股关系）
- `employments`：person_id, company_id, role, start, end （任职）
- `flows`：id, company_id, date, counterparty, bank, amount, direction, abnormal, note, embedding_id
- `socials`：id, person_id/company_id, base, months, paid, gap_months, risk

Milvus collection `flow_embeddings`：存储流水文本向量，用于异常/相似检索。

## 4. 模型编排（Deepseek + Qwen）

- **查询理解（Qwen）**：自然语言 → `StructuredQuery{entity_type, intent, filters}`。
  无 key 时降级为本地关键词规则（保证可演示）。
- **证据问答（Deepseek）**：RAG = Milvus 检索片段 → 拼 prompt → Deepseek 生成，
  输出 `{answer, refs}`，引用来源可追溯（审计合规要求）。

## 5. 运行

```bash
pip install -r requirements.txt
# 本地 demo（无需 PG/Milvus/Redis，使用内存兜底 + mock 数据）
python -m gateway.app
# 完整（docker）
docker compose up --build
```

## 6. 测试（TDD）
见 `tests/`：查询理解解析、流水异常检测、RAG 召回评估、网关聚合降级。

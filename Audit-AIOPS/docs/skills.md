# Agent 技能中心（OpenSpace「skill 进化」哲学落地）

> 呼应港大黄超团队 HKUDS / OpenSpace 的核心思想：**Agent = Model + Harness（做薄）；能力以可演进的 skill 沉淀，编排层零改动即可增删/升级。**
> 本项目把「审计领域 Agent 的能力」从写死的编排逻辑里抽出来，落成**单一事实来源的技能注册表**。

---

## 1. 为什么需要技能中心

- **能力可演进**：新增/迭代一个能力 = 往 `app/skills/registry.py` 的 `SKILL_DEFS` 里加一条 / 升一版（改 `version` / `evolved_from`），编排层 (`AgentOrchestrator`) 与前端（技能中心面板）**零改动即可生效**——这正是 OpenSpace「skill 越用越聪明」在工程上的落地。
- **能力可解释**：每个技能自带触发意图、是否需审批、所用工具、版本与演进来源，面试可当场讲清「Agent 到底会什么、为什么安全」。
- **审批对齐**：`requires_approval=True` 的技能（审批路由、审计留痕）与项目既有的「双人审批 + Checkpoint」强一致，呼应 HKUDS 的 ToB 生产级稳定哲学。

---

## 2. 模块结构

```
app/skills/
├── __init__.py      # 导出 list_skills / get_skill / resolve_skills / approval_required_skills / to_payload
└── registry.py      # Skill 数据类 + SKILL_DEFS（8 个领域技能）+ 匹配/解析函数
```

核心 API：

| 函数 | 作用 |
|---|---|
| `list_skills()` | 全部技能 |
| `get_skill(id)` | 按 id 取单个技能 |
| `resolve_skills(text)` | 把用户输入映射为命中的技能列表（按 `triggers` 关键词匹配） |
| `approval_required_skills()` | 所有需审批的技能 |
| `to_payload(s)` | 转成可序列化 dict（供 `/api/skills` 返回） |

---

## 3. 技能清单（当前 8 个）

| 技能 id | 名称 | 类别 | 需审批 | 工具 |
|---|---|---|---|---|
| `approval_routing` | 审批路由 | 审批与合规 | ✅ | OA-MCP / 工单系统 / 服务目录 |
| `workorder_decompose` | 工单拆单 | 编排 | — | 服务目录 / 工单系统 / LLM 意图识别 |
| `knowledge_qa` | 知识问答（多路 RAG） | 知识 | — | 混合检索 / 图 RAG / 多模态 RAG / 知识库 |
| `monitor_alert` | 监控告警 | 运维 | — | 监控服务 / 时序数据库 |
| `catalog_nav` | 服务目录导航 | 导航 | — | 服务目录 |
| `workorder_advance` | 工单推进 / 催办 | 编排 | — | 工单系统 / OA-MCP |
| `audit_trail` | 审计留痕 | 审批与合规 | ✅ | 留痕服务 / 日志 |
| `voice_entry` | 语音入口 | 交互 | — | ASR 转写 |

> `knowledge_qa` 的 `evolved_from` 记录了演进来源：`关键词检索 v1.0 → 混合 RAG v1.1 → 图+多模态 RAG v1.3`——直观展示「skill 进化」。

---

## 4. 编排层如何消费技能

`app/agent/orchestrator.py` 的 `handle()` 在每次请求开头调用：

```python
skills = resolve_skills(message)
memory.remember_profile(session_id, "matched_skills", [s.id for s in skills])
needs_approval = any(s.requires_approval for s in skills)
```

- 把命中技能写入会话记忆（长期画像沉淀）；
- `needs_approval` 与工单审批链（`CATALOG` 中的 `approval_chain`）天然对齐：凡命中需审批技能，工单自动走双人审批 + Checkpoint。

---

## 5. 端点与演示

- `GET /api/skills`：返回技能清单（总量、需审批数、技能详情、OpenSpace 哲学说明）。
- `POST /api/skills/resolve`：把一句话解析为命中技能（供前端技能中心高亮）。
- 演示页 `/agent-demo.html` 底部「🧩 Agent 技能中心」面板：渲染每个技能的触发词、审批标记、工具、版本与演进来源。

复现：

```bash
curl http://127.0.0.1:8001/api/skills
curl -X POST http://127.0.0.1:8001/api/skills/resolve \
  -H "Content-Type: application/json" \
  -d '{"text":"我要申请 Ukey 制作并走审批"}'
```

---

## 6. 面试话术（可直接引用）

> 「我们吸收了黄超团队 OpenSpace 的『skill 进化』——Agent 的能力不是写死在编排逻辑里，而是沉淀为**可演进的 skill 注册表**。新增一个能力只需加一条/升一版，编排层和前端零改动生效；审批类 skill 与我们的双人审批+Checkpoint 对齐，保证 ToB 场景的安全。这比把逻辑硬编码进 if-else 更利于长期演进。」

---

## 7. 与 Prompt Cache 的关系

技能中心解决「**Agent 会什么、怎么安全执行**」，Prompt Cache（见 `sft/prompt_cache.py`）解决「**执行时怎么省算力**」——两者共同构成 HKUDS 迁移学习的收口：
**skill 沉淀（能力演进）× prompt cache 强化（成本控制）= 可演进、可量化、可私有化的生产级审计 Agent**。

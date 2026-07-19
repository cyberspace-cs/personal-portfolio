# CLI-native OA 工具层（HKUDS / CLI-Anything 迁移落地）

> 呼应港大黄超团队 HKUDS 的 **CLI-Anything** 思想：CLI 是 Agent 的「原生接口」。
> 把专业软件（此处为 OA / 审批 / 工单 / 目录 / 监控）包装成统一的 CLI 式命令，
> 让 Agent 像人在终端敲命令一样原生驱动外部系统，比 GUI 自动化更稳、更省 token、更可审计。

---

## 1. 为什么是 CLI-native（而非 GUI 自动化）

| 维度 | GUI 自动化 | CLI-native（本项目） |
|---|---|---|
| 稳定性 | 依赖 UI 元素定位，易随改版失效 | 命令接口契约稳定，不受前端改动影响 |
| token 成本 | 需描述屏幕/坐标，token 消耗大 | 命令即结构化指令，极省 token |
| 可审计 | 难回溯「点了什么」 | 每条命令天然可记录、可回放 |
| 可脚本化 | 难编排 | 命令可组合、可批量、可纳入编排层 |

这正是 CLI-Anything 的核心主张：**与其让 Agent 模仿人类操作 GUI，不如让软件原生说 Agent 的语言（CLI）**。

---

## 2. 落地实现：`app/services/oa_mcp.py`

在既有「OA-MCP 适配层（适配器模式）」之上，新增 **`OA_TOOLS` 工具注册表**，把 OA 内部操作暴露为 CLI 式工具：

| 工具名 | CLI 命令模板 | 说明 |
|---|---|---|
| `oa_approval_submit` | `oa approval submit --type <审批类型> --applicant <申请人> --owner <审批责任人> --due <YYYY-MM-DD>` | 提交审批节点 |
| `oa_approval_query` | `oa approval query --ticket <OA-xxxxx>` | 查询审批状态 |
| `oa_approval_approve` | `oa approval approve --ticket <OA-xxxxx> --approver <审批人> --decision <approve\|reject>` | 审批/驳回（双人审批第二人） |
| `oa_workorder_advance` | `oa workorder advance --id <WO-xxx> --step <步骤序号>` | 推进工单状态机 |
| `oa_catalog_list` | `oa catalog list` | 列出服务目录 |
| `oa_alert_raise` | `oa alert raise --level <warn\|crit> --msg <告警内容>` | 上报监控告警 |

每个工具同时携带：
- **结构化 schema**：`params`（名称 / 是否必填 / 说明），供编排层精确调用与参数校验；
- **`cli` 命令模板**：可直接拼成命令回显给用户，或作为 Agent 的「原生调用面」。

`call_oa_tool(name, args, oa)` 即一次 CLI 调用，按 `_handler` 分派到对应实现：
- 审批类（`submit` / `query` / `approve`）→ 走 `MockOAClient` / `McpOAClient`（OA-MCP 适配层）；
- `catalog` → 懒加载 `app.services.catalog.CATALOG`（兼容 dict / 对象两种形态）；
- `alert` / `advance` → 进程内轻量状态，零依赖可演示。

### 真实落地路径
`McpOAClient` 即这些命令背后的 **MCP server**：部署时绑定 OA 方提供的 MCP server（暴露同名 tools），
`_dispatch` 的 handler 改为 `session.call_tool(name, args)` 即可，业务代码与命令契约不变。
本层仅定义协议与骨架，不内置任何第三方 OA SDK，避免强耦合。

---

## 3. 编排消费：技能中心接入

`app/skills/registry.py` 新增技能 **`oa_cli`**（演进来源标 `CLI-Anything（HKUDS）`）：

```python
Skill(
    id="oa_cli", name="OA-CLI 原生工具", category="集成",
    description="把 OA 审批/工单/目录/监控操作封装为统一 CLI 式命令，Agent 像在终端敲命令一样原生驱动 OA。",
    triggers=["oa", "提交审批", "查审批", "推进工单", "服务目录", "告警", "命令", "cli"],
    tools=["oa_approval_submit", "oa_approval_query", "oa_approval_approve",
           "oa_workorder_advance", "oa_catalog_list", "oa_alert_raise"],
    version="1.0", evolved_from="CLI-Anything（HKUDS）",
)
```

编排层 `resolve_skills(text)` 命中 `oa_cli` 后，Agent 即可原生调用上述工具；新增工具 = 往 `OA_TOOLS` 加一条，
技能 `tools` 同步引用，**编排层零改动**。

---

## 4. 端点与演示

- `GET /api/tools`：返回工具清单（`name` / `summary` / `cli` / `params` / `backend`）。
- `POST /api/tools/invoke`：原生调用一个工具（`{name, args}`），背后由 OA-MCP 执行。
- 演示页 `/agent-demo.html`「⌨️ OA-CLI 原生工具」面板：渲染 6 个命令模板，并提供「▶ 试一试：oa catalog list」实时调用回显。

### 现场复现
```bash
# 工具清单（含 cli 命令模板）
curl http://127.0.0.1:8001/api/tools
# Agent 原生调用（name + args 即一次 CLI 调用）
curl -X POST http://127.0.0.1:8001/api/tools/invoke \
  -H "Content-Type: application/json" \
  -d '{"name":"oa_catalog_list","args":{}}'
# 浏览器：http://127.0.0.1:8001/agent-demo.html  →  ⌨️ OA-CLI 原生工具 面板
```

---

## 5. 面试怎么讲（一句话）

> 「我吸收黄超团队 CLI-Anything 的思想——CLI 才是 Agent 的原生接口。
> 我把 OA 的审批/工单/目录/告警都定义成一条条 CLI 命令（如 `oa approval submit --type ukey --applicant 张三`），
> 由 OA-MCP 适配层执行，比 GUI 自动化更稳、更省 token、每条都可审计；
> 这些命令同时进了技能中心（`oa_cli`），Agent 一句话就能原生调用。这是 ToB 场景里把外部系统接进 Agent 的正确姿势。」

# AuditScope — 审计综合信息查询工具（审查查）

> 对标企查查、天眼查的「审计/尽调」综合信息查询平台。面向审计师、尽调人员、合规与风控，
> 把「查老板 / 查人员 / 查公司 / 查流水 / 查社保」整合到一个搜索框驱动的智能查询工作台。

## 1. 产品定位与对标

| 维度 | 企查查 / 天眼查 | AuditScope（审查查） |
|------|----------------|----------------------|
| 核心用户 | 销售、商务、投资人 | 审计师、尽调、合规、风控 |
| 主场景 | 工商信息、股权、风险 | 审计证据链、资金流水、社保合规、人员关系 |
| 智能能力 | 基础搜索 + 图谱 | 搜索 + **LLM 查询理解** + **RAG 证据问答** + 向量检索 |
| 数据深度 | 公开工商 | 工商 + 流水 + 社保 + 人员任职（多源融合） |

## 2. 设计系统（UI/UX Pro Max 落地）

> UI/UX skill 的数据文件（search.py / csv）在本环境缺失，按其 SKILL.md 的准则手工落地：
> 专业数据平台 / fintech / 审计合规，深色为主、玻璃拟态卡片、清晰数据表格、SVG 图标（lucide，禁用 emoji）。

### 2.1 风格
- **Pattern**：Dashboard / 数据工作台（顶部全局搜索 + 左侧结果分类 + 右侧详情/图谱）
- **Style**：Professional Dark + Glassmorphism（深色玻璃卡片），适度发光描边，强调「可信、冷静、权威」
- **Effects**：`backdrop-blur` 玻璃卡、柔和阴影、`150–300ms` 过渡、骨架屏加载

### 2.2 配色（深色优先，审计蓝青主色）
```
--bg-900 #0B1220   主背景（深海军蓝）
--bg-800 #111a2e   面版/卡片底
--bg-700 #1a2740   悬浮/次级
--primary #2563EB  主色（审计蓝）
--accent #06B6D4   强调（青，用于数据高亮/图表）
--success #10B981  通过/正常
--warning #F59E0B  注意/待核
--danger  #EF4444  风险/拒绝
--text-100 #F1F5F9 主文字
--text-400 #94A3B8 次要文字（仅用于标签，正文用 text-200）
--border  #1E293B  描边
```
- 浅色模式：白底 + 同主色，玻璃卡 `bg-white/80`，正文 `slate-900`，次要 `slate-600`

### 2.3 字体
- 标题/数字：`"Inter"` / `"HarmonyOS Sans"`（数据用等宽数字 `font-variant-numeric: tabular-nums`）
- 正文：`"PingFang SC"` / `"Microsoft YaHei"` / system-ui

### 2.4 组件规范
- 圆角：`rounded-xl`（卡片）/`rounded-lg`（按钮/输入）
- 间距：8px 栅格，卡片内 padding `p-5`
- 图标：lucide-react，统一 `24x24` viewBox，`w-5 h-5`
- 可点击元素必须 `cursor-pointer` + hover 反馈（颜色/边框/阴影，禁止位移缩放）
- 触摸目标 ≥ 44px；表单有 `<label>`；图标按钮有 `aria-label`

### 2.5 可访问性
- 正文对比度 ≥ 4.5:1（深色下用 text-100/200，不用 text-400 作正文）
- `prefers-reduced-motion` 时关闭过渡
- 图表提供表格兜底

## 3. 前端页面（React + Vite + TS + Tailwind）

入口：`auditscope/web/`
- `index.html` + `vite.config.ts` + `tailwind.config.js` + `postcss.config.js`
- `src/main.tsx` `src/App.tsx`（路由：首页搜索 / 结果页 / 五个模块详情）
- `src/components/`：Navbar、GlobalSearch、ResultCard、DataTable、RiskBadge、Skeleton、Tabs
- `src/pages/`：Home、SearchResults、CompanyDetail、PersonDetail、BossDetail、FlowDetail、SocialDetail
- `src/api/`：`client.ts`（对接后端网关 `/api/v1/*`，带 mock 兜底）
- `src/mock/`：演示数据（公司/老板/人员/流水/社保）

## 4. 后端架构（微服务 + Docker）

见 `auditscope/backend/README.md` 与 `docker-compose.yml`。
- 网关 `gateway`（FastAPI）：统一 `/api/v1`，鉴权、限流、聚合、缓存命中
- 子服务：
  - `company-svc`：公司工商/股权（PostgreSQL）
  - `person-svc`：人员/任职/老板关系（PostgreSQL + 图查询）
  - `flow-svc`：银行流水（PostgreSQL + Milvus 向量相似/异常）
  - `social-svc`：社保缴费（PostgreSQL）
  - `rag-svc`：Deepseek + Qwen 编排，Milvus 向量库 + Redis 缓存，RAG 证据问答
-  infra：PostgreSQL 16、Milvus 2.4、Redis 7

## 5. 模型编排（Deepseek + Qwen）
- **查询理解（Qwen）**：把自然语言搜索框输入解析为结构化查询（实体类型 + 意图 + 过滤）
- **证据问答（Deepseek）**：基于检索到的公司/流水/社保片段做 RAG 回答，附引用
- **路由**：简单意图走精确检索；复杂/模糊/问答走 LLM+RAG

## 6. 测试（TDD）
- 网关聚合、查询理解解析、流水异常检测、RAG 检索召回评估（见 `backend/tests/`）

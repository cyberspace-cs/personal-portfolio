# CS 前沿 · 计算机 / Agent / LLM / AI 知识聚合平台

> 一个面向计算机、Agent、LLM 与 AI 前沿技术的**信息聚合平台**：聚合 GitHub 高星开源项目、前沿论文/文档、开源笔记（参考 [lvynote](https://github.com/lvy010/lvynote)）与前沿产品，覆盖 GPU 算子、Triton、推理引擎、Agent 框架、MCP、RAG、强化学习、混元 AI Infra、顶会（ICML/ICLR/NeurIPS/ACL/CVPR）等方向。

参考站点视觉风格：[heikesong.cn](https://heikesong.cn/)（赛博极客）、[jikezhen.com](https://jikezhen.com/)（极客小镇），并融合本作品集统一的深色玻璃拟态 + 科技网格设计语言。

---

## ✨ 功能特性

- **聚合展示**：首页卡片网格聚合所有前沿信息，含编辑精选、趋势标记、Star / 机构 / 语言 / 热度等元信息。
- **分类筛选**：20 个技术方向（LLM 架构、推理优化、推理引擎、Agent 框架、多智能体、MCP、RAG、GPU/Triton、上下文并行、预训练、微调、强化学习、Agent 评估、多模态、AI Infra、系统底层、顶会等），侧栏一键筛选。
- **关键词搜索**：标题 / 简介 / 正文 / 机构 / 标签全文检索。
- **类型筛选 & 排序**：仓库 / 论文 / 博客 / 框架 / 产品 / 顶会等类型过滤；按最新 / Star / 热度 / 名称排序。
- **详情页**：Markdown 正文渲染、标签、原始资源跳转、同分类推荐、阅读量统计。
- **收藏功能**：基于匿名会话的收藏（本机浏览器持久化），收藏页统一管理。
- **内容管理（增删改查）**：内置管理后台，支持前沿条目的创建 / 编辑 / 删除与分类管理，完整覆盖后端 CRUD API。
- **响应式 & 明暗主题**：移动端自适应，支持深色 / 浅色一键切换。

---

## 🧱 技术架构

```
┌─────────────────────────┐         ┌──────────────────────────┐
│  前端 (web/)            │         │  后端 (server/)          │
│  React 18 + Vite + TS   │  /api   │  FastAPI + SQLite        │
│  Tailwind CSS           │ <─────> │  - 分类 / 条目 CRUD       │
│  lucide-react 图标       │  JSON   │  - 搜索 / 筛选 / 排序      │
│  marked + DOMPurify     │         │  - 统计 / 收藏（会话）     │
│  Hash 路由              │         │  - 直接托管 web/dist       │
└─────────────────────────┘         └─────────────┬────────────┘
                                                    │ sqlite3
                                            ┌───────▼────────┐
                                            │  frontier.db   │
                                            │ categories     │
                                            │ items/tags     │
                                            │ favorites      │
                                            └────────────────┘
```

- **前端**：React + Vite + TypeScript + Tailwind CSS，参考上述站点的科技感视觉，构建产物 `web/dist` 由 FastAPI 直接托管（同源 `/api`）。
- **后端**：FastAPI（参考本仓库 `shuati-coach` 的 FastAPI + SQLite 模式），RESTful API + 静态托管。
- **数据库**：SQLite，零外部依赖，表结构见下文。

### 目录结构

```
cs-frontier-hub/
├── server/                 # FastAPI 后端
│   ├── main.py             # 应用入口：API 路由 + 静态托管
│   ├── database.py         # SQLite 连接 / Schema / 种子写入
│   ├── models.py           # Pydantic 模型
│   ├── seed_data.py        # 20 分类 + 64 条前沿信息种子数据
│   ├── requirements.txt
│   └── frontier.db         # 运行时自动生成（已 gitignore）
├── web/                    # React 前端
│   ├── src/
│   │   ├── App.tsx         # Hash 路由
│   │   ├── pages/          # Home / Detail / Favorites / Admin
│   │   ├── components/     # Navbar / Sidebar / ItemCard / FavButton ...
│   │   ├── lib/            # api.ts / types.ts / session.ts / icons.tsx
│   │   └── context/        # ThemeContext（明暗主题）
│   ├── index.html / vite.config.ts / tailwind.config.js
│   └── package.json
├── start.sh                # 一键启动脚本
└── README.md
```

---

## 🚀 快速开始

### 1. 后端

```bash
cd server
pip install -r requirements.txt
python seed_data.py        # 初始化并填充数据库（首次）
uvicorn main:app --reload --port 8000
```

或一键启动（自动装依赖 + 种子 + 运行）：

```bash
bash start.sh
```

访问：

- API 文档：http://localhost:8000/docs
- 前端页面：http://localhost:8000/ （生产构建后由 FastAPI 托管）

### 2. 前端（开发模式）

```bash
cd web
npm install
npm run dev                # http://localhost:5173 （/api 已代理到 :8000）
```

### 3. 生产构建

```bash
cd web
npm install
npm run build              # 产物输出到 web/dist，由 FastAPI 自动托管
```

> 部署时只需运行后端：`uvicorn main:app --port 8000`，前端 `dist` 会被同源托管。

---

## 🔌 API 参考

基础路径：`/api`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/health` | 健康检查 |
| GET | `/stats` | 概览统计（总数 / 分类数 / 趋势 / 按类型 / 按分类 / 热门） |
| GET | `/categories` | 分类列表（含每类条目数） |
| POST | `/categories` | 新建分类（管理写接口） |
| PUT | `/categories/{id}` | 更新分类 |
| DELETE | `/categories/{id}` | 删除分类（其下条目置为未分类） |
| GET | `/items` | 条目列表，支持 `q` / `category` / `source_type` / `tag` / `status` / `featured` / `sort` / `page` / `page_size` / `session_id` |
| GET | `/items/{id或slug}` | 条目详情（阅读量 +1） |
| POST | `/items` | 新建条目 |
| PUT | `/items/{id}` | 更新条目 |
| DELETE | `/items/{id}` | 删除条目 |
| POST | `/session` | 创建匿名收藏会话，返回 `session_id` |
| GET | `/favorites?session_id=` | 收藏列表 |
| POST | `/favorites` | 切换收藏（body: `session_id`, `item_id`） |
| DELETE | `/favorites/{item_id}?session_id=` | 取消收藏 |

> **写接口鉴权**：默认开放。设置环境变量 `ADMIN_KEY` 后，所有 POST/PUT/DELETE 需携带请求头 `X-Admin-Key: <key>`。

---

## 🗄️ 数据模型

- **categories**：`id, name, slug, icon, description, sort_order`
- **items**：`id, title, slug, summary, content, category_id, source_type, source_url, github_stars, author_org, language, status, featured, views, created_at, updated_at`
- **tags / item_tags**：标签多对多
- **sessions / favorites**：匿名收藏会话与收藏关系

---

## 📚 数据来源与覆盖方向

种子数据覆盖用户指定的全部方向，来源均为真实可访问的公开资料：

- **开源高星**：vLLM、SGLang、TensorRT-LLM、LangChain、LangGraph、LlamaIndex、AutoGen、CrewAI、Agents SDK、MCP、RAGFlow、GraphRAG、Triton、FlashAttention、Megatron-LM、Axolotl、LLaMA-Factory、VERL、SWE-bench、LLaVA、Qwen-VL、TiDB、DuckDB、Tokio、xv6、E2B 等
- **前沿模型 / 产品**：DeepSeek、Kimi、Claude Code、混元 hy3、WorkBuddy、Trae、nanobot
- **技术方向**：LLM 底层架构、推理优化、GPU 算子/Triton、上下文并行、预训练、SFT/后训练、强化学习/Agentic RL、Agent 评估/Harness、多智能体、MCP、RAG、多模态、AI Infra、系统底层、顶会前沿
- **参考聚合源**：[lvynote](https://github.com/lvy010/lvynote) 收录的计算机前沿信息

---

## 📌 说明

- 本目录为 [personal-portfolio](https://github.com/cyberspace-cs/personal-portfolio) 的子项目，沿用仓库既有的 `server/`（FastAPI）+ `web/`（React）结构。
- `github_stars` 为撰写时的近似值，仅用于演示排序。
- 收藏基于浏览器匿名会话，**清除浏览器存储会丢失收藏**。

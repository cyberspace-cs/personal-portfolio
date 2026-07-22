# CS 前沿 · 计算机 / Agent / LLM / AI 知识聚合平台

> 一个面向计算机、Agent、LLM 与 AI 前沿技术的**信息聚合平台**：聚合 GitHub 高星开源项目、前沿论文/文档、开源笔记（参考 [lvynote](https://github.com/lvy010/lvynote)）与前沿产品，覆盖 GPU 算子、Triton、推理引擎、Agent 框架、MCP、RAG、强化学习、混元 AI Infra、顶会（ICML/ICLR/NeurIPS/ACL/CVPR）等方向。

参考站点视觉风格：[heikesong.cn](https://heikesong.cn/)（赛博极客）、[jikezhen.com](https://jikezhen.com/)（极客小镇），并采用**蓝白酷炫 HUD 风格**——深蓝黑底 + 蓝/冰蓝/青色霓虹强调、科技网格、扫描线、终端 kicker 标签、英雄区辉光与标题渐变。

**技术栈**：后端 **Python FastAPI + SQLite**，前端 **Vite + Vue 3 + Tailwind CSS**，并内置一个**公开源爬虫**（`server/crawler.py`）自动聚合 GitHub / Gitee / HuggingFace Papers / arXiv / CSDN 博客 / AI 资讯 / Semantic Scholar 的最新前沿信息（部分来源自带真实封面图）。

---

## ✨ 功能特性

- **动态技术架构地图**：首页以交互式、带动画的 SVG 技术栈分层图呈现整体架构，点击任意节点即可按方向筛选信息（直接回应「看不到画像」——现在有了可视化架构中心 + 真实/生成封面图）。
- **聚合展示**：卡片网格聚合所有前沿信息，每卡带**封面图**（真实缩略图或按标题生成的渐变画像）、编辑精选、趋势标记、Star / 机构 / 语言 / 热度等元信息。
- **分类筛选**：20 个技术方向（LLM 架构、推理优化、推理引擎、Agent 框架、多智能体、MCP、RAG、GPU/Triton、上下文并行、预训练、微调、强化学习、Agent 评估、多模态、AI Infra、系统底层、顶会等），一键筛选。
- **关键词搜索**：标题 / 简介 / 正文 / 机构 / 标签全文检索。
- **类型筛选 & 排序**：仓库 / 论文 / 博客 / 资讯 / 框架 / 产品 / 顶会等类型过滤（首页顶部一键切换「全部 / 仓库 / 论文 / 博客 / 资讯 / 产品」）；按最新 / Star / 热度 / 名称排序。
- **详情页**：Markdown 正文渲染、标签、原始资源跳转、同分类推荐、阅读量统计。
- **收藏功能**：基于匿名会话的收藏（本机浏览器持久化），收藏页统一管理。
- **内容管理（增删改查）**：内置管理后台，支持前沿条目的创建 / 编辑 / 删除与分类管理，完整覆盖后端 CRUD API。
- **爬虫抓取**：后台一键「抓取最新前沿」，从 GitHub / Gitee / HuggingFace Papers / arXiv / CSDN 博客 / AI 资讯 / Semantic Scholar 拉取最新信息并写入数据库（自动去重、HuggingFace 自带真实封面图）。
- **响应式 & 明暗主题**：移动端自适应，支持深色 / 浅色一键切换。

---

## 🧱 技术架构

```
┌─────────────────────────┐         ┌──────────────────────────┐
│  前端 (web/)            │         │  后端 (server/)          │
│  Vue 3 + Vite + TS      │  /api   │  FastAPI + SQLite        │
│  Tailwind CSS           │ <─────> │  - 分类 / 条目 CRUD       │
│  lucide-vue-next 图标    │  JSON   │  - 搜索 / 筛选 / 排序      │
│  marked + DOMPurify     │         │  - 统计 / 收藏（会话）     │
│  Hash 路由              │         │  - 爬虫接口 /api/crawler   │
└─────────────────────────┘         └─────────────┬────────────┘
                                                    │ sqlite3
                                            ┌───────▼────────┐
                                            │  frontier.db   │
                                            │ categories     │
                                            │ items/tags     │
                                            │ favorites      │
                                            └────────────────┘
```

- **前端**：Vue 3 + Vite + Tailwind CSS，参考上述站点的科技感视觉，构建产物 `web/dist` 由 FastAPI 直接托管（同源 `/api`）。
- **后端**：FastAPI（参考本仓库 `shuati-coach` 的 FastAPI + SQLite 模式），RESTful API + 静态托管 + 爬虫模块。
- **数据库**：SQLite，零外部依赖，表结构见下文。
- **爬虫**：`server/crawler.py`，仅用标准库（urllib / xml.etree / json）聚合多源前沿信息（GitHub / Gitee / HuggingFace Papers / arXiv / CSDN 博客 / AI 资讯 / Semantic Scholar），无需鉴权、可离线安全降级。

### 目录结构

```
cs-frontier-hub/
├── server/                 # FastAPI 后端
│   ├── main.py             # 应用入口：API 路由 + 静态托管
│   ├── database.py         # SQLite 连接 / Schema / 种子写入
│   ├── models.py           # Pydantic 模型
│   ├── seed_data.py        # 20 分类 + 64 条前沿信息种子数据
│   ├── crawler.py          # 公开源爬虫（HuggingFace Papers / arXiv）
│   ├── requirements.txt
│   └── frontier.db         # 运行时自动生成（已 gitignore）
├── web/                    # Vue 3 前端
│   ├── src/
│   │   ├── App.vue         # 根组件
│   │   ├── router/         # Hash 路由
│   │   ├── views/          # Home / Detail / Favorites / Admin
│   │   ├── components/     # Navbar / ItemCard / TechArchitecture / Cover ...
│   │   └── lib/            # api.js / session.js / markdown.js
│   ├── index.html / vite.config.js / tailwind.config.js / postcss.config.js
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

## 🕷️ 爬虫

`server/crawler.py` 从公开、无需鉴权的来源聚合最新前沿信息并写入本地数据库，**每个来源独立容错**（某源不可达不会影响其他源）：

- **GitHub 仓库**（`api.github.com/search/repositories`）：按 `topic:llm / agent / rag / llm-inference / mcp-server` 多角度检索高星仓库，带 Star 数与作者头像（作封面）。
- **Gitee 仓库**（`gitee.com/api/v5/search/repositories`）：码云仓库，作为 GitHub 的**国内备源**（国内访问更稳）；仅用 `order` 参数避免 Gitee 对 `sort` 的校验报错，本地再按 Star 排序。
- **HuggingFace Papers**（`https://huggingface.co/api/papers`）：按热度排序的论文，**自带 `thumbnailUrl` 真实封面图**，直接解决「看不到画像」问题。
- **arXiv API**（`cs.CL / cs.LG / cs.AI / cs.CV` 最新论文）。
- **CSDN 博客**（`blog.csdn.net/<user>/rss/list`）：聚合技术博主 RSS，覆盖国内技术分享（博主列表 `CSDN_BLOGGERS` 可在 `crawler.py` 中扩展）。
- **AI 资讯**（多 RSS 源）：VentureBeat AI / Google AI Blog / Google Research Blog / MIT Tech Review / The Verge AI / BAIR Blog / Hugging Face Blog / Towards Data Science / Machine Learning Mastery。
- **Semantic Scholar 论文**（`api.semanticscholar.org`）：补充论文源，带 **429 退避重试**。

特性：按 `source_url` 去重、网络不可用时安全返回（不抛崩）、按关键词自动归类到 20 个方向之一、返回**各源抓取明细**（`by_source`）。

命令行：

```bash
cd server
python crawler.py                 # 抓取全部可用源，各 20 条
python crawler.py --source github # 仅 GitHub
python crawler.py --source gitee  # 仅 Gitee
python crawler.py --source csdn   # 仅 CSDN 博客
python crawler.py --source news   # 仅 AI 资讯
python crawler.py --source semantic # 仅 Semantic Scholar
python crawler.py --limit 40      # 控制每个源的数量
```

支持 `--source`：`github` / `gitee` / `hf` / `arxiv` / `csdn` / `news` / `semantic` / `all`。

或通过接口（管理写接口，未设 `ADMIN_KEY` 时开放）：

```bash
curl -X POST http://localhost:8000/api/crawler/run \
  -H "Content-Type: application/json" \
  -d '{"sources":["github","gitee","hf","arxiv","csdn","news","semantic"],"limit":20}'
```

前端首页也提供「抓取最新前沿」按钮，点按即触发全部来源的抓取流程，并展示各源新增明细。

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
| POST | `/crawler/run` | 触发爬虫抓取（管理写接口，body: `sources`, `limit`） |

> **写接口鉴权**：默认开放。设置环境变量 `ADMIN_KEY` 后，所有 POST/PUT/DELETE 需携带请求头 `X-Admin-Key: <key>`。

---

## 🗄️ 数据模型

- **categories**：`id, name, slug, icon, description, sort_order`
- **items**：`id, title, slug, summary, content, category_id, source_type, source_url, github_stars, author_org, language, status, featured, views, image_url, created_at, updated_at`
- **tags / item_tags**：标签多对多
- **sessions / favorites**：匿名收藏会话与收藏关系

---

## 📚 数据来源与覆盖方向

种子数据覆盖用户指定的全部方向，来源均为真实可访问的公开资料：

- **开源高星**：vLLM、SGLang、TensorRT-LLM、LangChain、LangGraph、LlamaIndex、AutoGen、CrewAI、Agents SDK、MCP、RAGFlow、GraphRAG、Triton、FlashAttention、Megatron-LM、Axolotl、LLaMA-Factory、VERL、SWE-bench、LLaVA、Qwen-VL、TiDB、DuckDB、Tokio、xv6、E2B 等
- **前沿模型 / 产品**：DeepSeek、Kimi、Claude Code、混元 hy3、WorkBuddy、Trae、nanobot
- **技术方向**：LLM 底层架构、推理优化、GPU 算子/Triton、上下文并行、预训练、SFT/后训练、强化学习/Agentic RL、Agent 评估/Harness、多智能体、MCP、RAG、多模态、AI Infra、系统底层、顶会前沿
- **参考聚合源**：[lvynote](https://github.com/lvy010/lvynote) 收录的计算机前沿信息
- **爬虫自动来源**：GitHub、Gitee（国内备源）、HuggingFace Papers、arXiv、CSDN 博客、AI 资讯（VentureBeat / Google AI / MIT TR / The Verge / BAIR / HuggingFace Blog / TDS / ML Mastery）、Semantic Scholar

---

## 📌 说明

- 本目录为 [personal-portfolio](https://github.com/cyberspace-cs/personal-portfolio) 的子项目，沿用仓库既有的 `server/`（FastAPI）+ `web/`（Vue）结构。
- `github_stars` 为撰写时的近似值，仅用于演示排序。
- 爬虫抓取项目的封面图版权归原作者所有，仅供学习研究。
- 收藏基于浏览器匿名会话，**清除浏览器存储会丢失收藏**。

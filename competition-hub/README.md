# 竞赛雷达 · 技术竞赛聚合平台

> 聚合 **黑客松 / Kaggle 数据竞赛 / 算法大赛 / CTF / AI 大模型 / 创新创业** 等全球技术竞赛信息的聚合展示平台。
> 参考 [heikesong.cn](https://heikesong.cn/)（天天黑客松）与 [jikezhen.com](https://jikezhen.com/)（极客镇）的赛博极客视觉风格与前后端架构思路。

![tech](https://img.shields.io/badge/stack-FastAPI%20%2B%20React-22d3ee) ![license](https://img.shields.io/badge/license-MIT-blue)

---

## ✨ 功能特性

- **竞赛聚合展示**：卡片化列表，聚合黑客松、Kaggle、算法、CTF、AI 大模型、创新创业等全品类技术竞赛。
- **竞赛详情页**：关键信息（主办方 / 地点 / 形式 / 奖金 / 时间线 / 官网）、详细描述、同类推荐。
- **多维筛选**：按分类、状态（即将开始 / 进行中 / 已结束）、形式（线上 / 线下 / 混合）组合筛选。
- **关键词搜索**：跨标题、简介、主办方、描述、标签的实时模糊搜索（防抖）。
- **排序**：最新发布 / 奖金最高 / 即将截止 / 最热门。
- **用户认证**：注册、登录、退出（基于 Bearer Token，PBKDF2 密码哈希，零额外依赖）。
- **收藏功能**：登录用户可收藏竞赛，在「我的收藏」中统一管理。
- **竞赛 CRUD**：登录用户可发布 / 编辑 / 删除赛事信息（管理后台形态）。
- **🔌 自动聚合（Auto-Collect）**：内置可插拔数据源适配器（`collector.py`），自动搜寻并入库赛事 —— 目前接入「天天黑客松 heikesong.cn」与一份多源聚合数据集（Kaggle / 天池 / 华为云 / 腾讯 / 字节 / 强网杯 / 天府杯 等 16+ 来源）。管理员点击导航栏「一键聚合」即可增量更新，幂等去重（按 `slug`），并自动归类。每张卡片标注「聚合自 {来源}」。
- **响应式 UI**：赛博极客风格（深空底色 + 霓虹高亮 + 玻璃拟态 + 网格背景），完美适配桌面与移动端。列表卡片支持交错入场动画、骨架屏加载与标签胶囊。

---

## 🧱 技术栈

| 层 | 技术 | 说明 |
| --- | --- | --- |
| 前端 | React 18 + TypeScript + Vite + Tailwind CSS | SPA，组件化、零运行时框架依赖 |
| 后端 | FastAPI + Uvicorn | 异步 API，自动生成 OpenAPI 文档 |
| 数据访问 | 原生 `sqlite3` | 零 ORM 依赖，轻量、易部署（与仓库内 shuati-coach 同架构） |
| 认证 | Bearer Token + `auth_tokens` 表 | PBKDF2-SHA256 密码哈希，无第三方鉴权库 |
| 部署 | Docker / Docker Compose | 一键容器化 |

---

## 🗂 目录结构

```
competition-hub/
├── server/                 # 后端（FastAPI + SQLite）
│   ├── main.py             # 应用入口与全部 API 路由
│   ├── database.py         # 数据库连接、表结构初始化、幂等导入
│   ├── collector.py        # 自动聚合引擎（数据源适配器 + 幂等入库）
│   ├── collector_sources.json  # 多源聚合数据集（可手动扩充）
│   ├── models.py           # Pydantic 请求/响应模型
│   ├── seed.py             # 示例数据种子 + 默认管理员（env 可覆盖）
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── start.sh            # 一键启动脚本（含建库与种子）
│   ├── .env.example
│   └── data/               # SQLite 数据库文件（运行时生成，已 gitignore）
├── web/                    # 前端（React + Vite + Tailwind）
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts      # 开发代理 /api -> :8000
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── public/favicon.svg
│   └── src/
│       ├── main.tsx
│       ├── App.tsx         # 路由与全局 Provider
│       ├── index.css       # 全局样式与赛博主题
│       ├── lib/            # api.ts / auth.tsx / ui.tsx / types.ts / format.ts
│       ├── components/     # Navbar / Footer / Hero / FilterBar / CompetitionCard / Pagination / AuthModal
│       └── pages/          # HomePage / CompetitionDetail / FavoritesPage / SubmitPage / NotFound
├── docs/
│   ├── 数据库设计.md        # 表结构与字段说明
│   └── API文档.md          # 接口清单与示例
├── deploy/
│   ├── docker-compose.yml  # 全栈编排（前端构建 + 后端服务）
│   └── nginx.conf          # 生产反向代理示例
└── README.md
```

---

## 🚀 快速开始

### 方式一：前后端分离开发（推荐）

**1. 启动后端（默认 8000 端口）**

```bash
cd competition-hub/server
python -m venv .venv && source .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python seed.py            # 首次写入示例数据（竞赛表为空时也会自动种子）
uvicorn main:app --reload --port 8000
# API 文档: http://localhost:8000/docs
```

**2. 启动前端（默认 5173 端口，自动代理 /api 到 8000）**

```bash
cd competition-hub/web
npm install
npm run dev
# 打开 http://localhost:5173
```

### 方式二：生产一体化（后端托管已构建的前端）

```bash
cd competition-hub/web && npm install && npm run build   # 生成 web/dist
cd ../server
pip install -r requirements.txt && python seed.py
uvicorn main:app --port 8000
# 直接访问 http://localhost:8000 即为完整站点（前端 + API 同源）
```

---

## 🔌 API 概览

基础路径 `/api`。完整字段与示例见 [docs/API文档.md](docs/API文档.md)。

| 方法 | 路径 | 说明 | 需登录 |
| --- | --- | --- | --- |
| GET | `/health` | 健康检查 | ❌ |
| GET | `/categories` | 分类列表（含数量） | ❌ |
| GET | `/competitions` | 竞赛列表（支持 `q/category/status/mode/tag/sort/page/page_size`） | ❌ |
| GET | `/competitions/{id}` | 竞赛详情（自动 +1 浏览量） | ❌* |
| POST | `/competitions` | 创建竞赛 | ✅ |
| PUT | `/competitions/{id}` | 更新竞赛 | ✅ |
| DELETE | `/competitions/{id}` | 删除竞赛 | ✅ |
| GET | `/stats` | 看板统计 | ❌ |
| GET | `/collect/sources` | 已配置的数据源清单（名称 / 主页） | ❌ |
| POST | `/collect` | 触发自动聚合（增量更新赛事库） | ✅ 管理员 |
| POST | `/auth/register` | 注册（返回 token） | ❌ |
| POST | `/auth/login` | 登录（返回 token） | ❌ |
| GET | `/auth/me` | 当前用户 | ✅ |
| POST | `/auth/logout` | 退出登录 | ✅ |
| GET | `/favorites` | 我的收藏列表 | ✅ |
| POST | `/favorites` | 添加收藏 `{competition_id}` | ✅ |
| DELETE | `/favorites/{id}` | 取消收藏 | ✅ |
| GET | `/favorites/check/{id}` | 是否已收藏 | ❌* |

> \* 传入 `Authorization: Bearer <token>` 时，列表/详情会返回该竞赛的 `is_favorited` 状态。

---

## 🗄 数据库设计

共 6 张表：`categories` / `competitions` / `tags` / `competition_tags` / `users` / `auth_tokens` / `favorites`。
完整 DDL 与字段说明见 [docs/数据库设计.md](docs/数据库设计.md)。

核心关系：

```
users ──< auth_tokens
users ──< favorites >─── competitions
categories ──< competitions
competitions ──< competition_tags >─── tags
```

---

## 🐳 Docker 部署

```bash
cd competition-hub/deploy
docker compose up -d --build
# 访问 http://localhost:8000
```

---

## 📌 说明

- 示例数据仅用于演示，来源为公开竞赛信息整理，链接为占位示例。
- 本项目为个人作品集项目，存放于 [personal-portfolio](https://github.com/cyberspace-cs/personal-portfolio) 仓库的 `competition-hub/` 目录。
- 认证为演示级（Token 30 天有效期），生产环境建议接入更严格的权限体系（如管理员角色、HTTPS、限流）。
- **默认管理员**：首次启动（`seed.ensure_admin`）自动创建 `admin / Admin@2026`，可用环境变量 `ADMIN_USERNAME` / `ADMIN_PASSWORD` 覆盖；生产环境务必修改。仅管理员可调用 `POST /collect` 一键聚合。

## 📄 License

MIT

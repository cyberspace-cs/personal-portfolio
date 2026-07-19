# 专属刷题教练 · 快速上手（运行 / 部署 / 学习）

> 一份给「刚拿到项目、想跑起来并搞懂核心」的人的操作手册。
> 后端 `server/`（FastAPI + SQLite），前端 `coach.html`（H5）。**不接 API Key 也能完整运行**（降级模式，前端功能不受影响）。

---

## 一、项目一句话

把复赛「带 AI 的刷题工具」升级成的**定制化备考 Agent**：用 LangGraph 同构编排 + 混元/通义基座 + RAG + 分层记忆 + 反思节点，完成「诊断 → 讲题 → 变式 → 排计划 → 主动预警」，并已落地推理优化、多厂商、Channel 接入层、三层记忆、MCP。设计全貌见 `刷题教练-Agent升级设计.md`（Phase A–H）。

---

## 二、本地运行（Windows / PowerShell，无需服务器）

```powershell
# 1) 进入后端目录
cd D:\download\project\TX-budddy\personal-portfolio\shuati-coach\server

# 2) （推荐）建虚拟环境并装依赖
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3) 启动（start.sh 用的就是这条）
python main.py
```

启动后看终端打印确认：
- 前端页面（复赛平台）：`http://localhost:8000/coach.html`
- **AI 助手前端（蓝白科技风 Agent 对话 + 渠道/MCP/记忆面板）**：`http://localhost:8000/agent.html`
- 健康检查：`http://localhost:8000/api/health`（返回 `{"ok":true,...}` 即成功）
- 接入渠道：`http://localhost:8000/api/agent/channels`

**接真实大模型**（讲题/变式/报告用真模型，否则走规则降级文案）：
```powershell
$env:LLM_PROVIDER="deepseek"
$env:DEEPSEEK_API_KEY="sk-你的key"
python main.py
```
> 多厂商注册表支持：智谱/GLM、Kimi/Moonshot、腾讯混元、字节豆包、阿里千问、DeepSeek、OpenAI。
> 用 `<PROVIDER>_API_KEY` 注入（如 `MOONSHOT_API_KEY`），`GET /api/agent/providers` 看各厂商配置态。

**无 Web 也能驱动 Agent**（最快看效果，验证 Channel 解耦）：
```powershell
python run_agent_cli.py 1
```
按提示输入「帮我诊断薄弱点」「给我排个计划」即可对话。

---

## 三、部署到服务器（公网 + 小程序可用）

完整文档在 `deploy/README.md`（Docker + nginx + 自动 HTTPS）。核心流程：

**前置**：域名（如 `taoxie.vip`）+ ICP 备案（仅大陆服务器可作备案接入商；没备案可先在本地用小程序开发者工具勾「不校验合法域名」联调）。

```bash
# 1) 买轻量应用服务器：Ubuntu 24.04 / 2核2G / 放行 80,443,22
# 2) 服务器初始化（2核2G 必加 1G swap 防 OOM）
sudo fallocate -l 1G /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
sudo apt update && sudo apt install -y docker.io docker-compose-plugin
sudo systemctl enable --now docker

# 3) 拉代码 + 配密钥
git clone <你的仓库> coach && cd coach/deploy
cp .env.example .env && cp hermes.env.example hermes.env
#   openssl rand -hex 32  生成强随机串填 HERMES_KEY / API_SERVER_KEY

# 4) 申请 HTTPS 证书
sudo apt install -y certbot
sudo certbot certonly --webroot -w ./certbot/www -d taoxie.vip

# 5) 启动
docker compose up -d --build
curl https://taoxie.vip/api/health
```

**小程序接入**：把 `miniprogram/app.js` 的 `baseUrl` 改成 `https://taoxie.vip`，微信后台加 request 合法域名，开发者工具导入 `miniprogram/` 即可。

**日常运维**：
```bash
docker compose logs -f coach      # 看后端日志
docker compose restart coach        # 重启后端
```
> 数据库持久化在 `deploy/data/`（SQLite + WAL），重装容器不丢题。

---

## 四、如何学习项目核心

**策略：先读设计稿建立全景 → 由外到内读代码 → 跑起来对照。**

### 4.1 先读设计稿
`刷题教练-Agent升级设计.md` 是项目地图，按 Phase A→H 记录每阶段改动、命中面试点、踩坑与验证。重点看：
- §4 四层架构图
- §6 技术栈映射表（岗位要求 → 模块）
- §16–§18 Channel 接入层 / 三层记忆 / MCP

### 4.2 由外到内读代码（推荐顺序）

| 顺序 | 文件 | 看什么 |
|---|---|---|
| 1 | `server/main.py` | 入口：路由注册、lifespan 建表、`/api/health`、渠道/MCP 启动打印 |
| 2 | `server/agent/router.py` | HTTP 入口 `/api/agent/chat` → 分发到 Channel |
| 3 | `server/agent/channel.py` | **接入层解耦**：Inbound/Outbound/AgentHub（一个 core 多源） |
| 4 | `server/agent/orchestrator.py` | **CoachAgent**：六节点 `classify→子Agent→reflect` 编排 |
| 5 | `server/agent/supervisor.py` | **StateGraph 引擎**（LangGraph 同构，编排即代码） |
| 6 | `server/agent/tools.py` | 工具集：diagnose/wrongbook/plan/rag_qa/mcp_call |
| 7 | `server/agent/memory.py` | 三层记忆（长/短/中长期）+ 六段式上下文预算 |
| 8 | `server/agent/retriever.py` | RAG：TF-IDF + 中文 2-gram + RRF 重排 + 引用溯源 + 防幻觉 |
| 9 | `server/agent/llm.py` | 多厂商注册表 + 虚拟工具范式（替代脆弱 json_object） |
| 10 | `server/agent/inference.py` | 推理优化 7 项（KV缓存/压缩/投机解码/蒸馏/批处理/工具替代/量化） |
| 11 | `server/agent/anomaly.py` + `eval.py` | 学习异常检测（AIOps 迁移）+ 评测闭环 |

### 4.3 边跑边学
1. 启动后访问 `/api/health` 看能力开关（channels / mcp / infer_opt）。
2. 用 `python run_agent_cli.py 1` 实际对话，对照代码看每次调用走了哪个节点、落了什么记忆（`agent_history` 表）。
3. 调接口验证：`GET /api/agent/channels`、`POST /api/agent/history`、`GET /api/agent/mcp/tools`、`POST /api/agent/infer/optimize`。
4. 用设计稿每节「命中面试点」反推「为什么这么写」。

**一句话学习策略**：先抓主干（Channel → Orchestrator → Tools → Memory），再啃两个亮点（RAG 防幻觉、推理优化实测），最后看复用层（MCP / 多厂商）。

---

## 五、常见问题

- **启动报缺依赖**：`pip install -r requirements.txt`（或先建 `.venv`）。
- **没 Key 能跑吗**：能。`HAS_KEY=False` 时走规则降级，前端与 Agent 对话均可用，便于离线演示与评测。
- **想接真实模型但懒得配**：设 `LLM_PROVIDER` + `<PROVIDER>_API_KEY` 即可，运行期还能 `POST /api/agent/providers/switch` 切换。
- **数据库在哪**：默认 `server/coach.db`（SQLite）；Agent 记忆表由 `lifespan` 自动建。
- **完整部署细节**：见 `deploy/README.md`（含 Hermes Agent 接入与小程序联调）。

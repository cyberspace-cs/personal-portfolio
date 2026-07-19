# 审计智能一体化运维平台 · 部署与运行手册

> 覆盖三类使用场景：**本地开发运行**、**生产服务器部署（Docker）**、**服务器选购与上线流程**。
> 平台核心能力：大模型智能助手（混元/千问可插拔）+ Agent 编排（意图识别→拆单→审批路由→记忆）+ 混合检索 RAG + 语音入口 + OA 审批流对接。

---

## 一、本地运行方法（开发 / 演示）

### 1. 环境准备
- Python 3.13+（推荐用本项目隔离 venv，避免污染系统）
- 操作系统：Windows / macOS / Linux 均可

### 2. 安装与启动
```bash
# 进入项目目录
cd Audit-AIOPS

# 创建隔离环境（可选但推荐）
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 一键启动（自动生成 SFT 冷启动数据 + 拉起服务）
bash scripts/start.sh
# 或手动：
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. 访问
| 页面 / 接口 | 地址 | 说明 |
|---|---|---|
| 工作台（PC 原型） | http://127.0.0.1:8000/ | 统一入口、AI 对话直达、工单进度卡片、RAG 问答 |
| 监控大屏 | http://127.0.0.1:8000/monitor.html | KPI + 趋势 + 异常列表 |
| 服务目录 | http://127.0.0.1:8000/service-catalog.html | 13 项点选式提交 |
| 混合检索演示 | http://127.0.0.1:8000/knowledge-hybrid.html | 关键词+向量+RRF 融合对比 |
| 语音入口 | http://127.0.0.1:8000/voice.html | 录音→ASR→工单 |
| 健康检查 | GET /api/health | 状态探针 |

### 4. 配置真实大模型（可选）
复制 `.env.example` 为 `.env`，填入其一即可切换真实基座（不填则用离线 Mock，完整演示编排链路）：
```env
LLM_PROVIDER=hunyuan        # 或 qwen
HUNYUAN_API_KEY=你的密钥
# QWEN_API_KEY=你的密钥
```
支持**腾讯混元 / 阿里通义千问**双基座（OpenAI 兼容接口），详见 `app/llm/client.py`。

---

## 二、服务器选购建议（生产上线）

### 1. 云厂商
优先同生态：**腾讯云**（与混元同源，内网调用延迟低）/ **阿里云**（与通义千问同源）。
其他可选：华为云、火山引擎、AWS（海外）。

### 2. 配置基线
| 场景 | CPU | 内存 | 带宽 | 系统盘 | 预估月费 |
|---|---|---|---|---|---|
| 演示 / 内部小团队 | 2 核 | 4 GB | 3 Mbps | 40 GB SSD | ¥60–120 |
| 中等团队（含真实 LLM 推理） | 4 核 | 8–16 GB | 5–10 Mbps | 100 GB SSD | ¥300–800 |
| 全量私有化推理（7B+ 模型） | 8 核+GPU | 32 GB+ | 10 Mbps+ | 200 GB+ | ¥2000+ |

> 说明：本项目后端（FastAPI + 检索）极轻量，2C4G 即可流畅运行；若要把**大模型私有化推理**也部署到同一台，需 GPU 机型或单独部署推理服务（vLLM/SGLang），平台通过 `LLM_PROVIDER` 指向该服务即可。

### 3. 必须购买项
- 云服务器实例（按上表）
- 公网 IP（自带）+ 安全组（放通 80/443/8000，生产建议只放 80/443，8000 经反代）
- 域名（可选，但推荐，便于 HTTPS 与对外访问）
- SSL 证书（免费：Let's Encrypt / 云厂商免费证书）

---

## 三、服务器部署流程（Docker 一键上线）

### 步骤 1：登录服务器
```bash
ssh root@你的服务器公网IP
# 初始改密、新建非 root 用户、配置 ssh key（安全基线，略）
```

### 步骤 2：安装 Docker
```bash
# Ubuntu / Debian
curl -fsSL https://get.daocloud.io/docker | bash -s docker --mirror Aliyun
systemctl enable --now docker
# 验证
docker --version && docker compose version
```

### 步骤 3：上传代码
```bash
# 方式 A：git 拉取（推荐）
git clone <你的仓库> && cd Audit-AIOPS

# 方式 B：本地 scp
scp -r ./Audit-AIOPS root@服务器IP:/opt/Audit-AIOPS
```

### 步骤 4：配置环境变量
```bash
cp .env.example .env
vim .env            # 填入 HUNYUAN_API_KEY / QWEN_API_KEY 等
```

### 步骤 5：构建并启动
```bash
docker compose up -d --build
docker compose ps                 # 确认 healthy
curl http://localhost:8000/api/health
```

### 步骤 6：反向代理 + HTTPS（生产必做）
用 Nginx 反代 8000，并申请免费证书：
```nginx
server {
    listen 443 ssl;
    server_name ops.your-domain.com;
    ssl_certificate     /etc/nginx/certs/fullchain.pem;
    ssl_certificate_key /etc/nginx/certs/privkey.pem;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```
证书申请：`certbot --nginx -d ops.your-domain.com`（Let's Encrypt，免费自动续期）。

### 步骤 7：数据与持久化
- 当前演示用内存存储；生产请将 `app/store` 替换为 MySQL/Redis/ES（见 `README.md` 架构图）。
- 挂载卷：把 `sft/data`、`logs` 挂到宿主机或对象存储，避免容器重建丢数据。

---

## 四、运维与监控
- 健康检查：`/api/health`（已配 Docker HEALTHCHECK）
- 日志：`docker compose logs -f`
- 升级：`git pull && docker compose up -d --build`
- 密钥管理：生产用 **密钥管理服务（KMS）/ 环境变量注入**，勿硬编码进镜像
- 审计留痕：所有工单/审批/问答操作建议写入审计日志表（强监管场景必含）

---

## 五、常见问题
| 现象 | 排查 |
|---|---|
| 启动报 `python-multipart` 缺失 | `pip install python-multipart`（已写入 requirements） |
| 混合检索无结果 | 检查 `KB.docs` 是否加载；embedding_backend=local 离线可用 |
| 语音识别返回固定话术 | ASR_BACKEND=mock 为离线回显；接真实语音需 `funasr`（部署机安装） |
| 想接真实 OA | `OA_BACKEND=mcp` + `MCP_OA_SERVER=...`，由对方提供 MCP server |
| 真实大模型不生效 | 确认 `LLM_PROVIDER` 与对应 `*_API_KEY` 已设置，网络可达 |

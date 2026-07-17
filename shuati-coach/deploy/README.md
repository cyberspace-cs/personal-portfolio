# 专属刷题教练 · 生产部署（含 Hermes Agent 接入）

把项目跑在公网，并让小程序里的「问教练」智能答疑由 **Hermes Agent** 驱动。

## 架构总览

```
                          ┌──────────────┐
   手机/浏览器 ─HTTPS──▶ │   nginx:443  │  （唯一公网入口，Let's Encrypt）
                          └──────┬───────┘
                                 │ 代理全部流量
                          ┌──────▼───────┐
                          │  coach:8000  │  FastAPI 后端 + 静态 H5
                          │  (小程序后端) │
                          └──────┬───────┘
                     /api/chat 内网转发（带 Bearer 鉴权）
                          ┌──────▼───────┐
                          │ hermes:8642  │  Hermes Agent OpenAI 兼容 API
                          │ （仅内网）    │  暴露完整工具权限，严禁公网直连
                          └──────────────┘
```

关键点：**Hermes 只活在 Docker 内网，端口不映射到宿主机**；公网只看到 nginx。
「问教练」由教练后端代为转发并鉴权，前端永远拿不到 Agent 的工具端口。

---

## 一、前置：域名 + ICP 备案

微信小程序要求 `request` 域名必须 **HTTPS 且已 ICP 备案**，且不能用纯 IP。

1. 你已有 `taoxie.vip`。若尚未备案：登录域名所在云厂商（腾讯云/阿里云）控制台提交 **ICP 备案**，
   接入者（接入商）选你即将购买的**大陆地域**服务器。备案周期约 7–20 个工作日。
2. 备案通过、且域名解析（A 记录）指向服务器公网 IP 后，才能进行下一步。

> 没备案也能先在本地联调：小程序开发者工具勾选「不校验合法域名」，后端用局域网 IP 即可。

---

## 二、购买轻量应用服务器（试水版）

先买台便宜的轻量应用服务器玩一玩，**不必上 CVM 新客专享**（轻量无新人折扣，但本身便宜、85 折也差不了几十块）。轻量同样支持 ICP 备案，以后转正不用换机器。

1. 地域：**中国大陆**（只有大陆服务器才能作为 ICP 备案接入商；城市就近即可，不影响部署）。
2. 镜像：**系统镜像 → Ubuntu 24.04 LTS**（不要选 OpenClaw / WordPress 等应用模板，
   我们要自己跑 Docker，系统镜像最干净）。
3. 配置：**2 核 2G 足够试水**（Hermes 及上游模型都在云端，本机只跑网关）。已通过 `docker-compose.yml` 的
   `mem_limit` 锁定 coach 512m / hermes 768m，并需按第三步开 1G swap，**不会 OOM**。
   - 注意轻量有**每月流量包**（如 200GB），试水够用；别把大文件/视频挂在 nginx 下白耗流量。
4. 轻量控制台叫「防火墙」（不是安全组），开通后放行 **80、443**，以及临时 **22** 用于 SSH。
5. 买 1 年更划算（试水也可按月，反正轻量本身便宜）。

> 想长期/有用户再升级到 2 核 4G 或 CVM 即可，部署方式完全一样。

---

## 三、服务器初始化（一次性）

```bash
# 0) 2核2G 必加 1G swap（防 Hermes 抖动 OOM；4G 以上可跳过）
sudo fallocate -l 1G /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 1) 装 Docker + compose 插件
sudo apt update && sudo apt install -y docker.io docker-compose-plugin
sudo systemctl enable --now docker

# 2) 拉代码
git clone <你的仓库> coach && cd coach/deploy

# 3) 准备配置（都从 .example 复制后改值）
cp .env.example .env
cp hermes.env.example hermes.env
cp hermes.config.yaml.example hermes.config.yaml
#   - 在 .env / hermes.env 里把 HERMES_KEY 与 API_SERVER_KEY 设成同一段强随机串：
#     openssl rand -hex 32
#   - 在 hermes.env / hermes.config.yaml 里填上游模型 Key（OpenRouter / DeepSeek 等）

# 4) 申请 HTTPS 证书（certbot，需域名已解析且 80 端口通）
sudo apt install -y certbot
sudo certbot certonly --webroot -w ./certbot/www -d taoxie.vip
#   证书会落在 /etc/letsencrypt/live/taoxie.vip/，nginx.conf 已指向该路径
```

---

## 四、启动

```bash
# 在 coach/deploy 目录
docker compose up -d --build

# 健康检查
curl https://taoxie.vip/api/health
# 期望：{"ok":true,"ai":"fallback"|"enabled","hermes":"enabled"|"off"}
```

- `ai: enabled` 说明你填了 `API_BASE`+`API_KEY`（讲题/变式/报告用真实大模型）。
- `hermes: enabled` 说明 `/api/chat` 已连上 Hermes，小程序「问教练」可用。

---

## 五、小程序接入

1. 打开 `miniprogram/app.js`，把：
   ```js
   baseUrl: 'https://YOUR_SERVER_DOMAIN'
   ```
   改成 `https://taoxie.vip`。
2. 微信公众平台 → 你的小程序 → **开发管理 → 开发设置**：
   - **request 合法域名** 加 `https://taoxie.vip`
   - **业务域名**（web-view 用）加 `taoxie.vip`
   - **downloadFile 合法域名** 如需也加上。
3. 微信开发者工具导入 `miniprogram/`，用自己的 **AppID**（测试号仅限本地预览）。
4. 首页「问教练 · Hermes 智能体」卡片 → 进入 `pages/chat`，即可多轮提问，请求走 `/api/chat` → 后端 → Hermes。

---

## 六、Hermes 进阶（可选）

- **换模型 / 加提供商**：编辑 `hermes.config.yaml`（如切到 `provider: openai-api` 或 `custom` 指向本地 vLLM），
  重启 `docker compose restart hermes`。
- **Nous Portal（一个 Key 用 300+ 模型 + 工具网关）**：先在有桌面的机器跑 `hermes setup --portal` 完成 OAuth，
  把生成的 `~/.hermes/{.env,config.yaml}` 拷到 `deploy/` 替换挂载文件。
- **本地大模型**：在 `hermes.config.yaml` 设 `provider: custom` + `base_url: http://<host>:11434/v1`（Ollama），
  Hermes 即为完全私有的教练大脑（注意 Ollama 需 `OLLAMA_CONTEXT_LENGTH>=64000`）。

---

## 七、日常运维

```bash
docker compose logs -f coach      # 看后端日志
docker compose logs -f hermes     # 看 Hermes 日志
docker compose restart coach        # 重启后端
# 证书续期（crontab 加：0 3 * * 1 certbot renew --quiet）
```

> 数据库持久化在 `deploy/data/`（SQLite + WAL），重装容器不会丢题。

---

## 八、推送到 GitHub / Gitee（代码托管）

### 当前环境限制（重要）
本机部署/开发环境**无法直连 github.com**（443 超时）且无 SSH key，因此**不能从此环境直接 push GitHub**。
代码已在本地 `git init` 并提交（含 `.gitignore`，已忽略 `.env` / `*.db` / `certbot/` / `data/` 等密钥与生成物）。
推送请在**能联网的机器（如你回家后的 Windows）** 执行。

### 方式 A：personal-portfolio 仓库根目录即本项目
```powershell
cd coach
git remote add origin https://github.com/cyberspace-cs/personal-portfolio.git
git branch -M main
git push -u origin main
```
> 若远程已有提交，先 `git pull origin main --allow-unrelated-histories` 再 push，避免被拒。

### 方式 B（最稳，coach 是仓库内子目录也适用）
```powershell
git clone https://github.com/cyberspace-cs/personal-portfolio.git
cd personal-portfolio
# 把本地 coach 目录内容复制进 coach 所在位置（根目录或某子文件夹）
xcopy /E /Y "C:\path\to\coach\*" .
git add -A
git commit -m "update: 刷题教练 Hermes 接入"
git push
```

### 认证（GitHub 已禁用密码登录）
- **HTTPS**：用户名 = GitHub 账号，密码 = **Personal Access Token**（Settings → Developer settings → PAT，勾 `repo`）。
- **SSH**：`ssh-keygen` 生成密钥，公钥加到 GitHub → SSH keys；remote 改用 `git@github.com:cyberspace-cs/personal-portfolio.git`。

### Gitee（码云）备选
Gitee 国内通常可达，可作为镜像（本环境若通也可直接推）：
```powershell
git remote add gitee https://gitee.com/<你的账号>/personal-portfolio.git
git push -u gitee main
```


# 审计智能一体化运维平台 · 最终交付总览

> 你醒来直接看这一篇即可。平台已**完整跑通**，地址：http://127.0.0.1:8000
> 核心：**大模型智能助手（混元/千问可插拔）+ Agent 编排（意图识别→拆单→审批路由→记忆）**。

---

## 一、已交付成果（按你的四方向 + 前期六步）

| 模块 | 交付物 | 状态 |
|---|---|---|
| 岗位调研 | `step1-岗位调研.md`（四厂+混元/千问，三类岗） | ✅ |
| 项目-岗位匹配 | `step2-项目岗位匹配.md` | ✅ |
| 技术提取 | `step3-技术提取.md`（三份 PDF 核心点） | ✅ |
| 产品原型 | `step4-产品原型设计.md` + 政务蓝白高保真原型 | ✅ |
| 架构设计 | `step5-架构设计.md` + 四层架构图 | ✅ |
| 简历话术 | `step6-简历亮点.md` + `demo-script.md` | ✅ |
| **方向1 真实基座+SFT** | `app/llm/client.py`（混元/千问/Mock 可插拔）+ `sft/`（数据生成+LoRA训练+评测闭环） | ✅ 离线可跑 |
| **方向2 混合检索** | `app/services/retrieval_hybrid.py`（FAISS+TF-IDF+RRF） | ✅ 已验证 |
| **方向3 语音+OA** | `app/services/asr.py`（语音入口）+ `app/services/oa_mcp.py`（MCP 适配） | ✅ 已验证 |
| **方向4 一键部署** | `Dockerfile`+`docker-compose.yml`+`scripts/start.sh`+`deploy-guide.md` | ✅ |
| 部署与运行手册 | `deploy-guide.md`（含**服务器购买流程**） | ✅ |
| 演示页面 ×6 | 工作台/监控/目录/混合检索/语音/Agent编排 | ✅ 已验证 |

---

## 二、立即运行（3 步）

```bash
cd Audit-AIOPS
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
浏览器打开 http://127.0.0.1:8000 —— **无需任何 Key 即可演示全部编排/检索链路**（默认 Mock 基座）。

---

## 三、接入真实大模型（腾讯混元 / 阿里通义千问）

```bash
cp .env.example .env
# 编辑 .env，填入其一：
LLM_PROVIDER=hunyuan
HUNYUAN_API_KEY=你的密钥
# 或 QWEN_API_KEY=你的密钥 且 LLM_PROVIDER=qwen
```
重启服务即生效，无需改代码。双基座均通过 OpenAI 兼容接口接入。

---

## 四、服务器购买与部署（上线到公网）

完整流程在 **[`deploy-guide.md`](deploy-guide.md)**，要点：

1. **选购**：腾讯云/阿里云 2C4G 起（¥60–120/月）即可跑后端；私有化推理需 GPU 机型。
2. **部署**：服务器装 Docker → 上传代码 → `docker compose up -d --build` → Nginx 反代 + HTTPS。
3. **密钥**：用环境变量/密钥管理服务注入 `HUNYUAN_API_KEY` 等，勿硬编码。
4. **数据**：演示用内存，生产把 `app/store` 换 MySQL/Redis/ES。

---

## 五、面试如何使用

- **讲项目**：`step5-架构设计.md` + `step6-简历亮点.md`（STAR 话术 + 简历条目）。
- **现场演示**：`demo-script.md`（5–8 分钟脚本）→ 打开工作台/监控/混合检索/Agent编排页。
- **亮点叙事**：AI Agent 应用开发（主轴）+ LLM 推理（RAG/FAISS）+ LLM 算法优化（SFT 数据飞轮）。

---

## 六、演示页面入口

| 页面 | 地址 |
|---|---|
| 工作台（主界面） | http://127.0.0.1:8000/ |
| Agent 编排可视化 | http://127.0.0.1:8000/agent-demo.html |
| 混合检索对比 | http://127.0.0.1:8000/knowledge-hybrid.html |
| 语音入口 | http://127.0.0.1:8000/voice.html |
| 监控大屏 | http://127.0.0.1:8000/monitor.html |
| 服务目录 | http://127.0.0.1:8000/service-catalog.html |

---

## 七、待你提供/决策（不影响当前演示）

1. **真实 API Key**：混元/千问，填入即切真实生成。
2. **服务器**：要不要我直接帮你出一份「阿里云/腾讯云具体机型+下单链接」清单？
3. **真实 OA 的 MCP server**：对接审批流时需对方提供。
4. **语音模型权重**：生产启用 FunASR 需联网拉取模型（演示用 Mock 即可）。

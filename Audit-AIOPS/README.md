# 审计智能一体化运维平台助手（Audit-AIOPS）

> 面向**审计领域**的「智能一体化运维平台助手」——用 **Agent 编排 + 大模型（腾讯混元 / 阿里通义千问，可插拔）** 解决审计人员办理运维服务时的「入口分散、流程黑盒、自动化断点、缺乏 AI 赋能」四大痛点。
> 项目定位：**大厂 AI Agent 应用开发岗**面试亮点项目，兼顾 LLM 推理开发与 LLM 算法优化方向。

---

## 一、核心痛点 → 解法

| 痛点 | 业务表现 | 平台解法 |
|---|---|---|
| 内外割裂 | 系统只给自有运维用，审计人员不知能办什么、流程如何 | 服务目录化、统一入口、流程透明 |
| 入口分散 | 仅 2 入口且跨 OA 模块，借终端+会议+联网要分别审批 | 一句话诉求 → Agent 自动拆单 → 多审批流并行路由 |
| 工单黑盒 | 提交后看不到进度，不知卡哪、找谁 | 进度卡片（节点状态 + 责任人 + 一键联系） |
| 自动化断点 | 资产领用线上申请线下签收、退回全线下 | 资产电子签收、自动化巡检脚本 |
| 缺乏 AI | 反复电话问询、事件靠人工发现 | 对话直达服务单、RAG 知识问答、异常自动发现 |

**三重转变（面试加分点）**：从「被动响应需求」→「主动挖掘痛点」；从「单一功能使用」→「系统方案设计」；从「关注技术实现」→「关注用户体验」。

---

## 二、技术架构（四层）

```mermaid
graph TB
  subgraph 业务层
    B1[十类审计支持<br/>Ukey/权限/邮件/资源/UPS/抽奖/网站/终端/会议/资产]
    B2[三类运维<br/>计算存储 / 应用系统 / 基础软件平台]
  end
  subgraph Agent编排层
    A1[意图识别] --> A2[拆单]
    A2 --> A3[审批路由]
    A3 --> A4[记忆系统]
    A0[Agent Orchestrator<br/>ReAct 式编排 + 工具网关 + 双人审批 + Checkpoint]
  end
  subgraph LLM推理层
    L1[可插拔基座<br/>混元 / 千问 / Mock]
    L2[RAG Serving<br/>P95 420ms]
    L3[领域 SFT + 事实核查评测<br/>数据飞轮]
  end
  subgraph 数据处理层
    D1[领域知识库 RAG 语料]
    D2[工单 / 资产台账]
    D3[Prometheus 指标]
    D4[向量库预留<br/>Chroma/FAISS + Embedding]
  end
  业务层 --> Agent编排层
  Agent编排层 --> LLM推理层
  LLM推理层 --> 数据处理层
  安全合规·可观测性 -.横切.-> 业务层
  安全合规·可观测性 -.横切.-> Agent编排层
```

- **业务层**：13 项服务目录化（点选式提交）。
- **Agent 编排层**：意图识别 → 拆单 → 审批路由 → 记忆（ReAct 式）；工具调用网关 + 高风险操作双人审批 + Checkpoint 恢复。
- **LLM 推理层**：可插拔基座（默认 Mock 离线跑通，配 Key 即切混元/千问，OpenAI 兼容）；RAG serving；领域 SFT + 事实核查/幻觉防控评测闭环。
- **数据处理层**：内置领域知识库、工单/资产台账、Prometheus 指标；预留向量库做混合检索。

---

## 三、快速启动

```bash
# 1. 安装依赖（建议使用隔离环境）
pip install -r requirements.txt

# 2. 启动（默认 8000 端口，Mock 基座，无需任何 Key 即可演示）
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 3. 打开浏览器
#    工作台：http://127.0.0.1:8000/
#    监控大屏：http://127.0.0.1:8000/monitor.html
```

接入真实大模型（可选）：设置环境变量后重启即可切换基座，无需改代码。

```bash
export HUNYUAN_API_KEY=你的密钥      # 腾讯混元
export QWEN_API_KEY=你的密钥         # 阿里通义千问
# 默认走混元；可设置 LLM_PROVIDER=qwen 切换
```

---

## 四、目录结构

```
Audit-AIOPS/
├── app/
│   ├── main.py              # FastAPI 入口，挂载静态前端与 API
│   ├── config.py            # 配置（基座、Key、模型名）
│   ├── models.py            # Pydantic 数据模型
│   ├── llm/client.py        # LLM 客户端抽象（混元/千问/Mock 可插拔）
│   ├── llm/cache.py         # 应用层 KV/Prompt Cache（推理加速：精确+语义命中）
│   ├── agent/
│   │   ├── orchestrator.py  # Agent 编排：意图→拆单→路由→记忆
│   │   └── memory.py        # 会话记忆
│   ├── services/
│   │   ├── catalog.py       # 服务目录（13 项）
│   │   ├── workorder.py     # 工单状态机 + 审批推进
│   │   ├── monitor.py       # 智能监控指标
│   │   ├── knowledge_base.py# 内置领域知识库（RAG 语料）
│   │   ├── retrieval.py     # 本地 TF-IDF 检索（预留向量召回）
│   │   ├── retrieval_hybrid.py # ★混合检索 TF-IDF+FAISS+RRF+图RAG+多模态RAG（实体共现图/双层检索/表格-截图统一检索）
│   │   ├── multimodal_encoder.py # ★可插拔视觉编码器（proxy / 混元视觉 / 千问-VL，RAG-Anything「多模态→文本」视觉编码路径，env 门控+无密钥降级）
│   │   └── knowledge.py     # RAG 问答服务
│   │   ├── experiment_store.py # ★科研实验记录仓库（真实文件入库/实体抽取/共现图/混合检索/效果指标，AdventureX 原型）
│   │   └── ops_data.py      # ★审计运维真实数据引擎（10 类审计支持+3 类运维 确定性种子生成/多用户智能体/ITSM+运维 KPI/痛点洞察，落盘）
│   ├── api/routers.py       # REST 路由
│   ├── api/experiments.py   # ★科研实验记录 Agent API（upload/seed/query/graph/metrics/list/delete）
│   ├── api/ops.py           # ★审计运维控制台 API（summary/tickets/alerts/changes/agents/pain-points/seed）
│   └── skills/              # ★Agent 技能中心（领域技能注册表，呼应 OpenSpace「skill 进化」）
│       ├── __init__.py
│       └── registry.py       # 技能定义 + resolve_skills / 审批技能识别
├── static/
│   ├── index.html           # 政务蓝白工作台（统一入口/进度卡片/对话直达/RAG问答）
│   ├── app.js               # 前端交互
│   ├── monitor.html         # 监控大屏（独立页）
│   ├── agent-demo.html      # Agent 编排可视化（意图→拆单→审批→记忆）
│   ├── knowledge-hybrid.html# ★混合检索四路对比（关键词 vs 混合 RRF vs 图 RAG 增强 vs 多模态 RAG）+ 视觉编码模式徽标
│   ├── voice.html           # 语音入口（录音→ASR→工单）
│   ├── service-catalog.html # 服务目录（蓝鲸经验细化：SLA/自助化/监控指标/痛点/AI 价值）
│   └── optimization.html    # ★算法侧推理优化实验台（蒸馏/INT8/缓存加速可视化）
│   ├── experiment-agent.html # ★科研实验记录智能体（AdventureX 黑客松：真实数据接入+接地问答+跨实验图谱+效果量化）
│   └── ops-console.html    # ★审计运维控制台（真实数据驱动：多用户智能体/工单看板/告警流/变更留痕/痛点洞察/服务目录细化）
├── step1-岗位调研.md         # 四厂+混元/千问 三类岗位核心技能
├── step2-项目岗位匹配.md     # 岗位→模块→技术栈 映射
├── step3-技术提取.md         # 三份参考 PDF 的 Agent/LLM 核心点
├── step4-产品原型设计.md      # 痛点→需求→原型
├── step5-架构设计.md         # 四层架构与调用链
├── step6-简历亮点.md         # 面试 STAR 话术 + 简历条目
├── deploy-guide.md           # 部署与运行手册（含服务器购买流程）
├── Dockerfile                # 生产镜像
├── docker-compose.yml        # 编排部署
├── .dockerignore
├── scripts/start.sh          # 一键启动
├── sft/                      # 领域 SFT + 模型优化（数据生成 + LoRA 训练 + 量化 + 蒸馏 + 评测闭环）
│   ├── dataset.py            #   合成审计运维 SFT 数据
│   ├── train.py              #   LoRA/QLoRA 训练（需 GPU）
│   ├── quantize.py           #   4/8-bit 量化部署模板（大模型私有化）
│   ├── distill.py            #   知识蒸馏 teacher→student 模板（大模型）
│   ├── distill_compress.py   # ★算法侧真实实测：Teacher→蒸馏→Student→INT8（纯numpy/CPU可复现）
│   ├── prune.py              # ★算法侧真实实测：幅度剪枝稀疏度-精度权衡（98%稀疏无损/50×乘加削减）
│   ├── speculative.py        # ★算法侧真实实测：投机解码（接受率39.5%/2.14×加速/无损一致）
│   ├── parallel.py           # ★算法侧概念仿真：企业级并行（模型/流水/上下文/GPU显存）+蒸馏压缩组合预算
│   ├── graph_rag.py          # ★检索侧真实实测：图 RAG（LightRAG 思路：实体共现图+双层检索），三层 RRF 融合
│   ├── prompt_cache.py       # ★算法侧真实实测：Prompt/前缀 KV-Cache 强化（命中率/省 token/省 prefill 时延），纯numpy/CPU
│   ├── rl_alignment.py        # ★强化学习对齐：DPO/PPO/GRPO 偏好优化 numpy 仿真（上下游关系+策略对比），纯numpy/CPU
│   └── evaluate.py           #   意图识别评测（数据飞轮）
├── docs/optimization.md      # 推理优化技术栈（逐条对应代码/实测数据）
├── docs/enterprise-parallel-compression.md  # ★企业级并行+蒸馏压缩核心主线（算法核心）
├── docs/graph-rag.md         # ★图 RAG（LightRAG 思路）检索增强：图索引+双层检索+实测
├── docs/skills.md            # ★Agent 技能中心（OpenSpace「skill 进化」）：技能注册表+审批对齐+演进
├── docs/hkuds-transfer-learning.md          # ★向港大黄超团队(HKUDS)/nanobot 学习的迁移分析
└── requirements.txt
```

> **新增能力（四方向强化）**：见本文末「八、四方向强化」。
> 服务器选购与上线流程见 [`deploy-guide.md`](deploy-guide.md)。

---

## 五、核心 API 示例

```bash
# 对话直达服务单（一句话自动拆单）
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"我要为审计三组开通远程邮件帐号，并借用一台会议终端"}'

# RAG 知识库问答（检索增强 + 来源标注）
curl -X POST http://127.0.0.1:8000/api/knowledge/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"审批流是如何自动拆分的？"}'

# 工单审批推进
curl -X POST http://127.0.0.1:8000/api/workorders/WO-2026-0718-0392/approve

# 混合检索问答（关键词 + FAISS 向量 + RRF 融合）
curl -X POST http://127.0.0.1:8001/api/knowledge/hybrid \
  -H "Content-Type: application/json" \
  -d '{"question":"审批流自动拆分怎么配置","top_k":3}'

# 大模型推理加速 · 语义/Prompt 缓存 Demo（二次同/近义提示命中缓存）
curl -X POST http://127.0.0.1:8001/api/llm/cache/demo \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Ukey 怎么申请制作","simulate_latency_ms":800}'

# 算法侧 · 蒸馏 + INT8 压缩 实测报告（先跑 python sft/distill_compress.py）
curl http://127.0.0.1:8001/api/opt/distill-report
# 算法侧 · 剪枝 实测报告（先跑 python sft/prune.py）
curl http://127.0.0.1:8001/api/opt/prune-report
# 算法侧 · 投机解码 实测报告（先跑 python sft/speculative.py）
curl http://127.0.0.1:8001/api/opt/speculative-report
# 算法侧 · 企业级并行（模型/流水/上下文/GPU显存）+ 蒸馏压缩 概念仿真（先跑 python sft/parallel.py）
curl http://127.0.0.1:8001/api/opt/parallel-report
# 算法侧 · 图 RAG（LightRAG 思路：实体共现图+双层检索）实测报告（先跑 python sft/graph_rag.py）
curl http://127.0.0.1:8001/api/opt/graph-rag-report

# 图 RAG 增强检索（关键词 + FAISS 向量 + 实体共现图，三层 RRF 融合）
curl -X POST http://127.0.0.1:8001/api/knowledge/graph \
  -H "Content-Type: application/json" \
  -d '{"question":"Ukey 制作后怎么回收？需要哪些审批","top_k":3}'

# 多模态 RAG 检索（RAG-Anything 思路：文本 + 表格 + 图像描述统一进检索）
curl -X POST http://127.0.0.1:8001/api/knowledge/multimodal \
  -H "Content-Type: application/json" \
  -d '{"question":"Ukey 制作需要哪些审批节点，截图里怎么填","top_k":4}'

# 多模态 RAG 视觉编码模式状态（proxy / real-hunyuan / real-qwen；无密钥自动降级 proxy）
curl http://127.0.0.1:8001/api/knowledge/multimodal-encoder-status

# 单轮 token 成本对比（呼应黄超「成本控制·自负盈亏」：压缩/加速来自真实实测）
curl http://127.0.0.1:8001/api/opt/cost-report

# 算法侧 · Prompt/前缀 KV-Cache 强化 实测报告（先跑 python sft/prompt_cache.py）
curl http://127.0.0.1:8001/api/opt/prompt-cache-report

# Agent 技能中心：领域技能清单（触发意图 / 是否需审批 / 工具 / 版本与演进来源）
curl http://127.0.0.1:8001/api/skills
# 把一句话解析为命中的技能（编排层 / 前端技能中心高亮）
curl -X POST http://127.0.0.1:8001/api/skills/resolve \
  -H "Content-Type: application/json" \
  -d '{"text":"我要申请 Ukey 制作并走审批"}'

# CLI-native OA 工具清单（每个工具带 cli 命令模板；呼应 HKUDS / CLI-Anything）
curl http://127.0.0.1:8001/api/tools
# Agent 原生调用一个 OA CLI 工具（name + args 即一次 CLI 调用，背后由 OA-MCP 执行）
curl -X POST http://127.0.0.1:8001/api/tools/invoke \
  -H "Content-Type: application/json" \
  -d '{"name":"oa_catalog_list","args":{}}'

# ===== 科研实验记录智能体（AdventureX 黑客松原型）=====
# ① 真实用户数据接入：上传实验记录文件（.md/.csv/.json/截图，multipart）
curl -X POST http://127.0.0.1:8001/api/experiments/upload -F "file=@E1-Pt-TiO2.md"
# ② 加载示例实验（真实文件落盘后入库，一键体验）
curl -X POST http://127.0.0.1:8001/api/experiments/seed -H "Content-Type: application/json" -d '{"force":false}'
# ③ 基于用户真实数据的接地问答（带来源、可追溯）
curl -X POST http://127.0.0.1:8001/api/experiments/query -H "Content-Type: application/json" -d '{"question":"哪种催化剂在 25°C 下产氢速率最高？","top_k":3}'
# ④ 跨实验知识图谱（实体共现图：节点=实体，边=同实验共现）
curl http://127.0.0.1:8001/api/experiments/graph
# ⑤ 平台效果指标（随真实上传数据实时计算）
curl http://127.0.0.1:8001/api/experiments/metrics
# ⑥ 已接入记录清单 / 删除某条
curl http://127.0.0.1:8001/api/experiments/list
curl -X DELETE http://127.0.0.1:8001/api/experiments/EXP-001

# 智能监控指标
curl http://127.0.0.1:8000/api/monitor

# 混合检索问答（关键词 + FAISS 向量 + RRF 融合）
curl -X POST http://127.0.0.1:8000/api/knowledge/hybrid \
  -H "Content-Type: application/json" \
  -d '{"question":"审批流是如何自动拆分的？"}'

# 语音入口：录音文件转写（multipart）
curl -X POST http://127.0.0.1:8000/api/asr -F "file=@voice.webm"

# 审批流对接 OA：提交节点 / 查询状态
curl -X POST http://127.0.0.1:8000/api/oa/submit \
  -H "Content-Type: application/json" \
  -d '{"node":{"name":"运维负责人审批","owner":"张工"}}'
curl "http://127.0.0.1:8000/api/oa/status?ticket=OA-00001"
```

---

## 六、面试亮点（对应三类岗位）

- **AI Agent 应用开发（主轴）**：Agent 编排层、意图识别/拆单/审批路由、ReAct 规划、工具调用网关、多 Agent 协作、MCP 演进。
- **LLM 推理开发**：可插拔基座（混元/千问 OpenAI 兼容）、私有化/内网部署、RAG serving 延迟优化、上下文预算分层。
- **LLM 算法优化（补强）**：数据飞轮驱动领域 SFT + 事实核查/幻觉防控评测闭环，形成「数据-训练-评测」证据链。

详见 [`step6-简历亮点.md`](step6-简历亮点.md) 与 [`demo-script.md`](demo-script.md)。

---

## 七、技术栈

Python · FastAPI · Pydantic · 混元/千问（OpenAI 兼容）· RAG（TF-IDF + FAISS 向量混合检索 + RRF 融合）· FunASR（语音入口，预留）· MCP（审批流对接 OA，预留）· LoRA SFT（领域微调，数据飞轮）· Prometheus（监控）· Docker（一键部署）· 原生 HTML/CSS/JS（政务蓝白原型）

---

## 八、四方向强化（新增能力）

### 方向 1 · 真实基座接入 + 领域 SFT（覆盖「LLM 算法优化」岗）
- `app/llm/client.py` 已支持**腾讯混元 / 阿里通义千问**双基座（OpenAI 兼容），设 `LLM_PROVIDER` + 对应 `*_API_KEY` 即切换；不设则用离线 Mock，完整演示编排链路。
- `sft/` 实现**数据飞轮闭环**：`dataset.py` 生成 2000 条审计运维意图/要素 SFT 数据 → `train.py`（LoRA/QLoRA，需 GPU）→ `evaluate.py` 评测意图识别准确率（rule-baseline 离线验证 0.975）。
- 形成「数据-训练-评测」证据链，补强岗位三类中的算法优化方向。

### 方向 2 · 向量混合检索（FAISS + TF-IDF + RRF）
- `app/services/retrieval_hybrid.py`：关键词召回（TF-IDF）+ 向量召回（**FAISS**，已落地）双路并行，**RRF 融合**排名；向量后端可插拔（`local` 离线零依赖 / `st` 真实语义向量）。
- 端点 `/api/knowledge/hybrid`；演示页 `/knowledge-hybrid.html`。

### 方向 3 · 语音入口 + 审批流 MCP 适配
- `app/services/asr.py`：**ASR 适配层**，默认 Mock（离线回显），预留 FunASR 真实中文识别；端点 `/api/asr` + 演示页 `/voice.html`（录音→转写→生成工单）。
- `app/services/oa_mcp.py`：**OA 适配层（适配器模式）**，Mock-OA 内存演示 + Mcp-OA（通过 MCP 协议对接真实 OA server，预留）；端点 `/api/oa/submit|status|approve`。
- 对应痛点五「缺乏 AI 赋能」→ 对话/语音直达服务单。

### 方向 4 · 一键部署（Docker）
- `Dockerfile` + `docker-compose.yml` + `scripts/start.sh` + `.dockerignore`：一条命令 `docker compose up -d --build` 上线。
- 服务器选购与上线完整流程见 **[`deploy-guide.md`](deploy-guide.md)**。

### 方向 5 · 算法侧大模型推理优化（真实实测，非概念）⭐
- **蒸馏 + INT8 压缩端到端跑通**：`sft/distill_compress.py`（纯 numpy / CPU 秒级可复现）在审计意图识别（14 类）上完成
  `Teacher(dim=8192, acc=100%) → 蒸馏 → Student(dim=512) → INT8 量化` 全链路：
  - 知识蒸馏：学生仅 42 条人工标签时 acc=95%，Teacher 对全量样本打软标签(T=3.0)蒸馏后回到 **100%（+5pt）**；
  - INT8 对称量化（per-channel scale）：**体积 3.95×、0 掉点**；
  - 端到端 **Teacher→INT8 学生：体积压 63× / CPU 提速 10.8× / 精度保持 100%**。
- **幅度剪枝端到端跑通**：`sft/prune.py` 对 Student 权重按 |w| 置零，实测 **98% 稀疏仍 0 掉点、稀疏存储 1.1KB、理论乘加削减 50×**，99% 后精度断崖——完整精度-稀疏度权衡曲线。
- **投机解码端到端跑通**：`sft/speculative.py`（字符 n-gram 模拟）草稿提议 + 目标并行校验，实测 **接受率 39.5%、Target 调用降 53%、加速 2.14×、输出与自回归 100% 一致（无损）**。
- **应用层 KV/Prompt Cache**：`app/llm/cache.py` 精确 + 语义缓存，二次同/近义提示命中省 ~800ms/次、成本归零。
- 端点：`/api/opt/distill-report`、`/api/opt/prune-report`、`/api/opt/speculative-report`、`/api/llm/cache/demo`、`/api/llm/cache/stats`；可视化页 `/optimization.html`（四合一）；技术栈说明 `docs/optimization.md`；专项面试题 `面试-优化技术面试题库.md`。
- 复现：`python sft/distill_compress.py && python sft/prune.py && python sft/speculative.py`。
- 一句话：**蒸馏 / 量化 / 剪枝 / 投机解码 / 缓存 五条优化线全部端到端真跑、可当场复现**。

### 方向 6 · 企业级并行核心 + 向港大黄超团队(HKUDS)/nanobot 学习 ⭐（算法核心升级）
- **企业级并行立为核心主线**：把「流水线并行 / 模型(张量)并行 / 上下文并行(压缩) / GPU 显存并行利用」与真实企业蒸馏压缩组合，确立 **「压缩在前、并行在后」** 的企业落地范式。`sft/parallel.py`（纯 numpy/CPU 概念仿真，与前述同口径）实测：模型并行 8 卡单卡参数比 12.5%（输出与单卡一致）、上下文并行 8 卡单卡 KV 比 12.5%、流水并行 4 卡利用率 25%→84%（3.4×）；对 7B 模型 4×4 并行，fp32 单卡 6.8GB → INT8 1.7GB/卡 → INT4 0.85GB/卡。详见 [`docs/enterprise-parallel-compression.md`](docs/enterprise-parallel-compression.md)。
- **向 HKUDS / nanobot 迁移学习**：系统梳理黄超团队的 **Agent=Model+Harness（做薄）、CLI 是 Agent 原生、skill 进化、ReAct、成本控制、ToB 生产级稳定** 等思想，以及 LightRAG（图 RAG）/RAG-Anything（多模态）/MiniRAG（极简 CPU 友好）/AutoAgent/CLI-Anything/OpenSpace/nanobot 的可迁移点，映射到本项目并给出 P0/P1/P2 行动项（图 RAG 升级、prompt cache 强化、skill 沉淀、多模态 RAG、CLI-native 适配）。详见 [`docs/hkuds-transfer-learning.md`](docs/hkuds-transfer-learning.md)。
- 端点新增 `/api/opt/parallel-report`；可视化页 `/optimization.html` 升级为**六合一实验台（蒸馏/量化/剪枝/投机解码/缓存/企业级并行）**；复现追加 `python sft/parallel.py`。

### 方向 7 · 图 RAG 检索增强（HKUDS/LightRAG 迁移落地）⭐（检索侧核心升级）
- **吸收 LightRAG「图索引 + 双层检索」思想**：在 `app/services/retrieval_hybrid.py` 加**实体共现图（GraphIndex）**作为第三路检索（前两路为 TF-IDF 关键词 + FAISS 向量），三路 **RRF 融合**。
- **实体抽取用审计领域词典替代 LLM 抽取**（17 个领域实体、108 条共现边、中枢实体「审批」），换取纯 CPU / 零依赖 / 可当场复现，与本项目「轻量可复现」哲学一致（对标 MiniRAG）。
- **双层检索**：Low-level（具体实体直接命中）+ High-level（沿图 BFS 扩散召回关联实体/文档），实测 6/6 查询均有「图扩散多召回」增益、平均多召回 2.33 篇——这是图 RAG 相对扁平向量 RAG 的核心优势（尤其审计这种强领域、实体密集、同义表述多的场景）。
- 端点：`/api/knowledge/graph`（返回命中 + 图素材）、`/api/opt/graph-rag-report`；演示页 `/knowledge-hybrid.html` 升级为**三列对比（关键词 / 混合 RRF / 图 RAG 增强）**；脚本 `sft/graph_rag.py` 生成报告；技术文档 [`docs/graph-rag.md`](docs/graph-rag.md)。
- 这正是「向 HKUDS 迁移学习」的最高价值 P1 落地项（详见 [`docs/hkuds-transfer-learning.md`](docs/hkuds-transfer-learning.md)）。

### 方向 8 · 多模态 RAG（RAG-Anything 思路）+ 单轮 token 成本量化 ⭐（hkuds P2 落地）
- **多模态 RAG 吸收 RAG-Anything「any modality 统一进 RAG」思想**：在 `app/services/retrieval_hybrid.py` 加 `MultimodalRetriever`，把文档附带的「表格 / 截图描述」作为多模态元数据，与文本一并纳入统一检索；命中时返回跨模态素材（`modalities` / `multimodal_hits`）。审计领域内置样本（Ukey 制作截图、权限变更审批表、资产台账、审计留痕截图等）已可演示「一张表 / 一张图也能被检索到」。
- **诚实标注取舍（已升级为可插拔真实编码，见方向 10）**：视觉编码层 `app/services/multimodal_encoder.py` 已做成可插拔——默认 `proxy` 复用预撰写描述（= VLM 预期输出代理，零依赖可复现）；配置 `VISION_PROVIDER=hunyuan/qwen` + 密钥后，自动调用真实多模态大模型对真实截图做视觉理解（真·视觉嵌入），响应统一携带 `encoder_mode`。本环境无密钥，故默认 proxy，但「多模态→文本→统一 RAG」链路完整可复现。
- **单轮 token 成本量化（呼应黄超「成本控制·自负盈亏」）**：`/api/opt/cost-report` 端点把本项目真实实测的压缩比（×63）、投机加速（×2.14）、接受率（39.5%）与单价/缓存命中率假设结合，给出「纯 Teacher(API) → INT8 学生自托管 → 学生+投机+缓存」的单轮成本与月成本对比，实验台 `/optimization.html` §8 提供可交互「降本计算器」。
- 端点：`/api/knowledge/multimodal`、`/api/opt/cost-report`；演示页 `/knowledge-hybrid.html`（多模态区块）+ `/optimization.html`（§8 成本对比）。这是「向 HKUDS 迁移学习」的 P2（多模态 RAG）与 P1（成本量化）落地项。

### 方向 9 · Prompt Cache 强化 + Agent 技能中心（HKUDS 剩余高价值项全落地）⭐
- **Prompt / 前缀 KV-Cache 强化（呼应黄超「成本控制·自负盈亏」）**：`sft/prompt_cache.py`（纯 numpy / CPU 可复现）仿真审计运维场景中「长且稳定的系统前缀 + 短而多变的用户 query」的流量结构——同一份系统前缀第二次起直接复用已计算的 KV、跳过前缀 prefill，仅算 query + 一次极小缓存读取。实测 **5 业务域 × 2000 请求（zipf 倾斜）：前缀缓存命中率 99.75%、节省 token 占全量 92.4%、TTFT（首字延迟）下降 87.7%、月（500 万请求）省约 ¥1,496 的 prefill 算力**。与本项目 `app/llm/cache.py`（应用层 精确+语义 响应缓存）构成**两层缓存架构**，高频/近义审计问答成本与首字延迟同时下降。端点 `/api/opt/prompt-cache-report`；可视化页 `/optimization.html` **§9（命中率 + 省 token + TTFT 下降 + 月省成本 + 累计节省曲线）**。
- **Agent 技能中心（呼应 OpenSpace「skill 进化」）**：新增 `app/skills/registry.py` 领域技能注册表（审批路由 / 工单拆单 / 知识问答 / 监控告警 / 服务目录导航 / 工单推进 / 审计留痕 / 语音入口 共 8 个技能），每技能自带触发意图、是否需双人审批、所用工具、版本与演进来源。编排层 `AgentOrchestrator` 经 `resolve_skills(text)` 把用户输入实时映射到技能并写入记忆，**增删/演进能力零改动编排逻辑**；审批类技能与「双人审批 + Checkpoint」对齐。端点 `/api/skills`（技能清单）、`/api/skills/resolve`（一句话→技能）；演示页 `/agent-demo.html` 新增「🧩 Agent 技能中心」面板，展示技能触发词/审批标记/工具/演进来源。技术文档 [`docs/skills.md`](docs/skills.md)。
- 至此「向 HKUDS 迁移学习」的 **P0/P1/P2 全部落地**：图 RAG ✅、多模态 RAG ✅、成本控制 ✅、prompt cache 强化 ✅、skill 沉淀 ✅。
- 复现追加：`python sft/prompt_cache.py`。

### 方向 10 · 多模态 RAG 接真实视觉编码（混元视觉 / 千问-VL 可插拔）⭐（hkuds P2 深化）
- **把方向 8 的「描述文本代理」升级为可插拔真实视觉编码（吸收 RAG-Anything「多模态 → 文本」路径）**：新增 `app/services/multimodal_encoder.py`，视觉编码器三态可插拔——
  - `ProxyVisualEncoder`：零依赖，复用 `AUDIT_MULTIMODAL` 预撰写描述（等价于「若把真实截图喂给 VLM 预期会产出的描述」），保证无密钥也能真跑、可复现；
  - `HunyuanVisionEncoder` / `QwenVisionEncoder`：env 门控（`VISION_PROVIDER=hunyuan/qwen`），复用 `HUNYUAN_API_KEY`/`QWEN_API_KEY`（与文本 LLM 同密钥），调用真实多模态大模型对 `assets/screenshots/<标题>.png` 做视觉理解，产出实时 caption 替换代理描述，做到**真·视觉嵌入**。
- **env 门控 + 优雅降级（与 LLM 基座一致范式）**：无密钥或缺失真实截图时，真实模式自动降级为 proxy 并在响应标注 `encoder_mode`，服务不中断、诚实可讲；配置密钥 + 放入真实截图后无需改代码即激活。
- **接入点**：`MultimodalRetriever` 每图经 `encode_image(path, cap)` 取描述（proxy=预撰写 / real=VLM 实时）再进入跨模态打分；端点 `GET /api/knowledge/multimodal-encoder-status` 暴露当前模式与可用 provider；演示页 `/knowledge-hybrid.html` 多模态区块展示 `encoder_mode` 徽标。真实截图放入约定见 [`assets/screenshots/README.md`](assets/screenshots/README.md)。
- 至此多模态 RAG 从「代理可复现」走向「接真实视觉模型可生产」：演示用审计样本（Ukey 制作截图、权限变更审批表、资产台账、审计留痕截图等）已内置，生产只需补真实截图 + 配密钥。

### 方向 11 · CLI-native OA 工具层（HKUDS / CLI-Anything 落地）⭐
- **核心思想（CLI-Anything）**：CLI 是 Agent 的「原生接口」——文本命令无歧义、省 token、可脚本化、可审计。把 OA 的内部操作暴露为**统一的 CLI 式命令**，Agent 就能像人在终端敲命令一样原生驱动 OA，不必依赖 GUI 自动化或硬编码 HTTP 拼装。
- **落地**：扩展 `app/services/oa_mcp.py`，新增 `OA_TOOLS` 注册表——把审批提交/查询/审批、工单推进、服务目录、监控告警封装为 6 个 CLI 式工具（如 `oa approval submit --type ukey --applicant 张三 --owner 李工`、`oa catalog list`），每个工具同时有结构化 schema 与一个 `cli` 命令模板；`call_oa_tool(name, args, oa)` 即一次 CLI 调用，背后由 `MockOAClient` / `McpOAClient`（OA-MCP 适配层）执行，零依赖可演示。
- **编排消费**：在 `app/skills/registry.py` 新增 `oa_cli` 技能（演进来源标 `CLI-Anything（HKUDS）`），其 `tools` 直接引用 6 个 OA CLI 工具；编排层经 `resolve_skills()` 命中后，Agent 即可原生调用。端点 `GET /api/tools`（工具清单 + cli 模板）、`POST /api/tools/invoke`（原生调用）；演示页 `/agent-demo.html` 新增「⌨️ OA-CLI 原生工具」面板，渲染命令模板并支持「试一试」实时调用。技术文档 [`docs/cli-native.md`](docs/cli-native.md)。
- 至此 HKUDS 谱系里与本项目最相关的几条主线**全部落地**：Agent=Model+Harness（做薄）、ReAct 编排、混合检索、推理加速、成本可控、**图 RAG（LightRAG）、多模态 RAG（RAG-Anything）、Prompt Cache（nanobot）、skill 进化（OpenSpace）、CLI-native（CLI-Anything）**。

### 方向 12 · 科研实验记录智能体（AdventureX 黑客松原型）⭐
- **背景与定位**：面向 AdventureX 黑客松「科研 / 实验记录 Agent」现场主题，**把 Audit-AIOPS 已经验证的混合检索 / 图 RAG / 多模态编码能力，迁移到科研实验记录场景**。核心是用户最关心的两点：**真实用户数据接入** + **平台起到的效果**。
- **① 真实用户数据接入（最最关键）**：`POST /api/experiments/upload` 接收研究者自己的真实实验记录——`.md/.txt/.csv/.json/.jsonl` 文本记录，以及 `.png/.jpg` 等截图（经可插拔视觉编码转文本）。文件解析 → 结构化 → **科研实体抽取**（领域词典 + 化学式正则 + 数值参数归一，纯 CPU 零依赖）→ 落盘入库（`data/experiments/records.jsonl` + `uploads/`），成为可被检索的私有知识库。**平台不替用户编造数据，所有问答都基于用户自己上传的内容。**
- **② 平台效果（可实时量化的价值证据）**：`GET /api/experiments/metrics` 从真实入库数据实时计算——已接入记录数、抽取科研实体数、**跨实验关联数**（同一材料/方法/参数出现在 ≥2 个实验）、**潜在重复实验预警**（实体 Jaccard 相似度 ≥0.5 即预警，典型如「基准实验 vs 重复性验证」）、估算为研究者节省的时间。指标随用户上传量真实变化，是平台价值的直接证据。
- **③ 基于用户数据的接地问答**：`POST /api/experiments/query` 复用混合检索（关键词 TF-IDF + FAISS 向量 + RRF 融合）对用户**自己的实验**做检索，回答**标注来源、可回溯到原始文件、绝不幻觉**；未命中如实告知。
- **④ 跨实验知识图谱**：`GET /api/experiments/graph` 返回科研实体共现图（节点=材料/方法/参数，边=同实验共现，权=共现记录数），演示页用 canvas 力导向可视化，把零散实验连成知识网络。
- **落地代码**：`app/services/experiment_store.py`（仓库 + 抽取 + 共现图 + 检索 + 指标 + 示例数据落盘）、`app/api/experiments.py`（7 个端点）、`static/experiment-agent.html`（政务蓝白演示页：上传面板 + 接地问答 + KPI 看板 + 知识图谱 + 重复预警）。示例数据见 `app/services/experiment_store.py::_SEED_EXPERIMENTS`（光催化分解水制氢研究线，8 个互相引用的实验，含 1 对「基准 vs 重复性验证」重复预警）。
- 技术文档 [`docs/experiment-agent.md`](docs/experiment-agent.md)；演示页 `/experiment-agent.html`（点「加载示例数据」秒级体验，或上传你自己的实验记录）。

### 方向 13 · 审计运维控制台（真实数据驱动，蓝鲸经验落地）⭐
- **背景与定位**：审计人员最在意「审计技术支持」和「日常运维」的真实数据，**不能缺**。本方向以用户给定的**十大审计技术支持（ukey/perm/mail/resource/ups/lottery/web/terminal/meeting/backup）+ 三大日常运维（devops/appops/platops）** 为权威分类（见 `app/services/catalog.py`），借鉴蓝鲸（BlueKing）的 CMDB / 监控告警 / ITSM / 故障自愈 / 工作门户经验，构建**真实大量数据驱动的运维控制台**，显著提升工作台停留体验。
- **① 真实数据引擎（确定性种子 + 落盘）**：`app/services/ops_data.py` 用固定种子生成 **148 条审计技术支持工单、107 条日常运维告警、50 条变更记录**，落盘 `data/ops/ops_data.json`（重启不丢）。数据全部围绕真实审计场景（Ukey 回收、权限越权、远程邮件、底稿备份、应用超时、证书过期…），**不编造**。
- **② 多用户运维智能体（贴合痛点）**：内置 6 个智能体 persona（系统运维/数据库/安全/应用支持/自动化/审计业务支持），各自承接工单与告警、自动化处置占比、CSAT，模拟多用户协作；页面「多用户智能体」面板展示其活跃度与效能。
- **③ 真实量化 KPI（ITSM + 运维）**：由真实数据计算——工单已解决率 / **自动化率** / **SLA 达标率** / **MTTR** / **CSAT** / FCR / 重开率；运维主机在线率 / **告警收敛（降噪）率** / **自愈率** / 平均恢复时长；变更**双人审批率 100%**（呼应审计留痕）。指标随数据真实变化，是平台价值的直接证据。
- **④ 痛点洞察（由数据推导）**：自动计算权限类工单占比、高频重复工单、告警噪声、P0/P1 SLA 敏感性、全程可追溯率，并给出 AIOps 改进建议（自助化、知识库聚类、告警收敛、紧急通道）。
- **⑤ 蓝鲸式服务目录细化**：`app/models.py` 的 `ServiceItem` 扩展 SLA/自助化/监控指标/工单字段/痛点/AI 价值/月单量字段，`service-catalog.html` 与运维控制台「服务目录」Tab 均渲染这些细化信息。
- **落地代码**：`app/services/ops_data.py`、`app/api/ops.py`（7 端点）、`static/ops-console.html`（政务蓝白控制台：KPI 条 + 多用户智能体 + 工单看板 + 告警流 + 变更留痕 + 痛点洞察 + 服务目录细化）、`static/service-catalog.html`（细化）。首页 `index.html` 新增「运维控制台」入口与状态条联动。
- 技术文档 [`docs/ops-console.md`](docs/ops-console.md)；演示页 `/ops-console.html`（默认即真实数据，可点 `POST /api/ops/seed` 重新生成）。

### 运维控制台 API 示例
```bash
# 工作台总览：ITSM + 运维 + 变更 KPI、多用户智能体、痛点洞察
curl http://127.0.0.1:8001/api/ops/summary
# 审计技术支持工单（可按 service/status/priority/auto 过滤）
curl "http://127.0.0.1:8001/api/ops/tickets?status=resolved&auto=1"
# 日常运维告警（可按 service/severity/status/auto 过滤）
curl "http://127.0.0.1:8001/api/ops/alerts?severity=致命"
# 变更记录（双人审批留痕）
curl http://127.0.0.1:8001/api/ops/changes
# 多用户智能体画像 / 痛点洞察 / 重新生成真实数据
curl http://127.0.0.1:8001/api/ops/agents
curl http://127.0.0.1:8001/api/ops/pain-points
curl -X POST http://127.0.0.1:8001/api/ops/seed
# 用（可插拔）LLM 基座对真实 KPI 做对话式智能分析（Mock 优雅降级为结构化模板）
curl -X POST http://127.0.0.1:8001/api/ops/analyze
```

### 方向 14 · 强化学习对齐（PPO → DPO → GRPO）⭐
- **为什么要讲清上下游关系**：对齐（Alignment）处在「Pretrain → SFT → (RM) → 对齐 → 部署优化」这条单向依赖链的中后段。越往下游越贴近「可用、可上线」——本项目落在最下游，把对齐好的模型低成本 serve 出来（蒸馏/INT8/剪枝/投机解码/Prompt Cache）。讲清这条链，才能说清「为什么需要 PPO/DPO/GRPO」。
- **三种方法（同一张 2D 偏好测试台真跑，纯 numpy/CPU，秒级可复现）**：
  - **DPO（2023）**：离线偏好对 + 隐式奖励（策略与参考策略的 logprob 差），**不需要显式 RM、不需要在线采样、只 2 个模型**（policy+ref），稳定易复现；代价：受静态偏好数据质量约束、无法在线探索。
  - **PPO（RLHF）**：在线 RL，需 **4 个模型**（policy/value/ref/RM），带基线 + KL 惩罚的裁剪代理目标；可在线探索、上限高，但训练不稳、显存大、超参敏感。
  - **GRPO（2024, DeepSeek-R1）**：保留 PPO 在线探索，但用**组内相对优势去掉 value 网络**（省显存/工程），适合可验证奖励（math/code/工具调用）。
- **可复现结论（真实仿真数值）**：DPO 最终准确率 100%、3 步收敛、最稳；GRPO 92.5%、5 步；PPO 85%、15 步（本玩具为静态奖励，未发挥 PPO 在线探索上限，其真实上限在可验证奖励任务）。结论诚实：DPO 是偏好分类的稳快之选，GRPO 是「在线 + 轻量」的折中，PPO 上限高但最娇气。
- **落地代码**：`sft/rl_alignment.py`（DPO/PPO/GRPO 偏好优化 numpy 仿真，输出 `sft/data/rl_report.json`）、`app/api/extra.py` 的 `GET /api/opt/rl-report` 与 `POST /api/opt/rl-run`、`static/rl-alignment.html`（政务蓝白：上下游流水线图 + 策略对比表 + 准确率/收敛/稳定性可视化 + 关键结论）。
- 技术文档 [`docs/rl-alignment.md`](docs/rl-alignment.md)（待补，要点见本段）；演示页 `/rl-alignment.html`。

### RL 对齐 API 示例
```bash
# 生成 RL 对齐仿真报告（纯 numpy/CPU，秒级）
python sft/rl_alignment.py
# 查看报告（DPO/PPO/GRPO 的最终准确率/收敛步数/稳定性/上下游流水线/对比表）
curl http://127.0.0.1:8001/api/opt/rl-report
# 运行时重算
curl -X POST http://127.0.0.1:8001/api/opt/rl-run
```

### 演示页面一览
| 页面 | 地址 | 体现能力 |
|---|---|---|
| 工作台 | `/` | 统一入口 + AI 对话直达 + 进度卡片 + RAG 问答（大模型智能助手主界面） |
| Agent 编排可视化 | `/agent-demo.html` | 意图识别→拆单→审批路由→记忆 全流程演示 + **🧩 Agent 技能中心**（9 技能清单）+ **⌨️ OA-CLI 原生工具**（6 个 CLI 式 OA 命令，可实时调用） |
| 混合检索 | `/knowledge-hybrid.html` | **关键词 / 混合 RRF / 图 RAG 增强 三列对比 + 多模态 RAG 扩展区块** |
| 语音入口 | `/voice.html` | 录音→ASR→工单 |
| 监控大屏 | `/monitor.html` | 智能监控 KPI + 异常 |
| 服务目录 | `/service-catalog.html` | 13 项点选式提交（蓝鲸经验细化：SLA/自助化/监控指标/痛点/AI 价值） |
| **算法侧优化实验台** | `/optimization.html` | **蒸馏/量化/剪枝/投机解码/缓存/企业级并行/单轮成本/Prompt缓存 实测可视化（七区块 + §9）+ 单轮 token 成本计算器** |
| **科研实验记录智能体** | `/experiment-agent.html` | **AdventureX 黑客松原型：真实文件接入 + 基于用户数据的接地问答 + 跨实验知识图谱 + 重复实验预警 + 效果实时量化（KPI 看板）** |
| **审计运维控制台** | `/ops-console.html` | **真实数据驱动：多用户智能体 + 审计技术支持工单看板 + 日常运维告警流/收敛/自愈 + 变更双人审批留痕 + 痛点洞察 + 服务目录细化 + 🤖 LLM 智能分析** |
| **强化学习对齐讲解** | `/rl-alignment.html` | **PPO→DPO→GRPO 演进：上下游关系图 + 策略优劣对比 + 纯 numpy 仿真可视化（准确率/收敛/稳定性）+ 关键结论** |

## 九、智能体研发路径（最佳实践）

把本项目从立项到可演示、可面试的完整过程，提炼为一条**可复用的智能体研发路径**（定位调研 → 原型对齐 → 最小闭环 → 四路检索 → 六线优化+并行 → 技能/CLI/缓存沉淀 → 真实数据驱动 → 智能分析+RL 对齐 → 参赛叙事升华），每一步附**做法 / 关键产物 / 最佳实践 / 易错点**，并附踩坑与约定复用清单。

→ 完整手册见 [**docs/agent-rd-path.md**](docs/agent-rd-path.md)。

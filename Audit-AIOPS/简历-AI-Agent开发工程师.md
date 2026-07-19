# 【姓名】— AI Agent / 大模型应用开发工程师（简历）

> ⚠️ 姓名/电话/邮箱/学校/年限 为占位，请按真实信息替换；项目经历已按 Audit-AIOPS 写实填充，可直接用。

---

## 基本信息
- 姓名：【姓名】 ｜ 电话：【138-xxxx-xxxx】 ｜ 邮箱：【name@example.com】
- 求职意向：AI Agent 开发工程师 / 大模型应用开发工程师
- 城市：【城市】 ｜ 经验：【X 年】 ｜ GitHub：【链接】 ｜ 技术博客：【链接】

---

## 技术栈
- **语言/框架**：Python、FastAPI、Pydantic、异步（asyncio/httpx）、TypeScript/原生前端
- **Agent / LLM**：Agent 编排（ReAct 式意图识别→拆单→路由→记忆）、可插拔 LLM（混元 / 通义千问 OpenAI 兼容）、Prompt Engineering
- **检索 / RAG**：混合检索（TF-IDF + FAISS 向量 + RRF 融合）、**图 RAG（实体共现图 + 双层检索，第三路）**、**多模态 RAG（表格/截图统一检索，RAG-Anything 思路）**、可溯源生成、离线确定性向量
- **模型优化**：LoRA/QLoRA 微调、4/8-bit 量化、知识蒸馏、应用层 KV/Prompt Cache、前缀 KV-Cache 强化、请求路由
- **工程化**：Docker / docker-compose、Nginx + HTTPS、MCP 适配、OA/MCP 打通、CI 友好
- **工具链**：Git、Linux、Postman/curl、pytest、数据飞轮（dataset→train→evaluate）

---

## 教育背景
- 【学校】 ｜ 【计算机/软件/AI 相关专业】 ｜ 【本科/硕士】 ｜ 【20xx.09 – 20xx.06】
- 主修：数据结构、机器学习、数据库、分布式系统（按实际填写）

---

## 核心项目：Audit-AIOPS · 审计智能一体化运维平台助手（个人/主力项目）
**角色**：后端 + Agent 架构 + 模型优化 主研 ｜ **周期**：【X 个月】 ｜ **状态**：本地全链路跑通 + Docker 一键部署

**项目简介**：面向审计运维场景的智能助手。员工用一句话（文字/语音）提诉求，系统由 Agent 自动完成
意图识别、工单拆单、审批路由与进度跟踪；知识问答用混合检索保证事实可溯源；底层大模型可插拔
混元/千问，并用缓存复用 / 量化 / 蒸馏做推理加速与私有化落地。

**我的工作与亮点**：
1. **Agent 编排主链路**：设计意图识别 → 拆单 → 审批路由 → 记忆的 ReAct 式编排；一句话多意图自动
   拆成多条独立审批并分别路由责任人/时限，进度卡片可视化（避免"只办一半、中途补单"）。
2. **混合检索 + RRF 融合**：实现 TF-IDF 关键词召回 + FAISS 向量召回，用 Reciprocal Rank Fusion
   融合异构排序，兼顾字面命中与语义命中；离线确定性向量，零外网依赖即可跑通。
3. **可溯源防幻觉**：检索结果强制带 source，生成时引用来源，满足审计合规与事实核查。
4. **算法侧 · 大模型推理优化（真实落地并实测，非概念）**：
   - **知识蒸馏 + INT8 压缩端到端跑通**（`sft/distill_compress.py`，纯 numpy/CPU 秒级可复现）：在审计意图识别（14 类）上，
     Teacher(dim=8192, acc=100%) 对全量样本打软标签，把仅有 42 条人工标签、acc=95% 的小学生模型蒸馏回 **100%（+5pt）**；
     再对学生权重做 **INT8 对称量化**，**体积压 3.95×、0 掉点**；端到端 **Teacher→INT8 学生 体积压 63×、CPU 提速 10.8×、精度保持 100%**，
     结果经 `/api/opt/distill-report` 与 `/optimization.html` 可视化。
   - **幅度剪枝端到端跑通**（`sft/prune.py`）：Student 权重按 |w| 幅度置零，实测 **98% 稀疏仍 0 掉点、稀疏存储 1.1KB、理论乘加削减 50×**，
     99% 后精度断崖——完整「精度-稀疏度」权衡曲线，`/api/opt/prune-report` 可查。
   - **投机解码端到端跑通**（`sft/speculative.py`）：草稿(bigram)提议 + 目标(trigram)并行校验，实测 **接受率 39.5%、Target 调用降 53%、加速 2.14×、输出与自回归 100% 一致（无损）**；Draft 可复用蒸馏小模型形成闭环。
   - 应用层 **Prompt/Semantic Cache**（KV-Cache 思想）：相同/近似提示复用结果，高频 FAQ 命中省 ~800ms/次、成本归零（已实现并 Demo）。
   - **图 RAG 检索增强（真实落地，吸收 LightRAG）**（`sft/graph_rag.py` + `retrieval_hybrid.py`）：在 TF-IDF/FAISS 两路之外加**审计实体共现图**作为第三路，Low-level 具体实体 + High-level 图扩散召回，三路 RRF 融合；实体抽取用审计领域词典（17 实体/108 边，纯 CPU 可复现），     实测 **6/6 查询图扩散多召回、平均 +2.33 篇**（关系相关但词面未现的文档也能召回）。
   - **多模态 RAG（真实落地，吸收 RAG-Anything）**（`retrieval_hybrid.py`）：把文档附带的「表格 / 截图描述」作为多模态元数据纳入统一检索，命中返回 image/table 模态；本环境以描述文本代理、零依赖可复现，复现 RAG-Anything「any modality 统一进 RAG」思想（端点 `/api/knowledge/multimodal`、演示页 `/knowledge-hybrid.html` 多模态区块）。
   - **单轮 token 成本量化（呼应黄超成本控制）**：`/api/opt/cost-report` + 实验台 §8「降本计算器」，纯 Teacher(API)→INT8 学生→学生+投机+缓存，单轮 ¥0.042→¥4.9e-5，月调用 500 万次可省约 99.9%（压缩比/加速为真实实测，单价/命中率为演示假设）。
   - **Prompt/前缀 KV-Cache 强化（呼应黄超成本控制，吸收 nanobot）**（`sft/prompt_cache.py`，纯 numpy/CPU）：仿真审计运维「长稳定系统前缀 + 短多变 query」流量，同一前缀二次起复用 prefill KV、跳过前缀重算；实测 **5 业务域 × 2000 请求：命中率 99.75%、省 token 占全量 92.4%、TTFT（首字延迟）↓87.7%、月省 ¥1,496 prefill 算力**；与 `cache.py` 应用层精确+语义响应缓存构成**两层缓存架构**（`/api/opt/prompt-cache-report`、实验台 §9 命中率/省 token/累计节省曲线）。
   - **Agent 技能中心（吸收 OpenSpace「skill 进化」）**（`app/skills/registry.py`）：领域技能注册表（8 技能：审批路由/工单拆单/知识问答/监控告警/服务目录/工单推进/审计留痕/语音入口），每技能含触发意图、是否需双人审批、工具、版本与演进来源；编排层 `resolve_skills()` 实时映射、零改动增删能力；审批技能与双人审批+Checkpoint 对齐（`/api/skills`、演示页 `/agent-demo.html` 🧩 技能中心面板）。
   - 大模型上线路线：训练侧 **QLoRA**、推理侧 **4/8-bit 量化**（`quantize.py`）、**大模型蒸馏模板**（`distill.py`）。
   - 一句话：**蒸馏 / 量化 / 剪枝 / 投机解码 / 缓存 五条优化线全部端到端真跑、可当场复现**（纯 numpy / CPU 秒级），非 GPU 模板或概念。
5. **语音 + OA 真实打通**：ASR 适配层（FunASR 预留）+ OA/MCP 适配层（适配器模式，可切真实 OA），
   审批流从"对话"直达"责任人与截止时间"。
6. **一键部署与可演示**：FastAPI + Dockerfile + docker-compose；政务蓝白前端原型 6 个演示页
   （工作台/Agent 可视化/混合检索对比/语音入口/监控/服务目录）。

**产出/验证口径（均可现场复现）**：混合检索 RRF 命中可列来源；SFT 评测基线意图识别 acc≈0.975；
**知识蒸馏 +5pt（95%→100%）、INT8 压缩 3.95× 且 0 掉点、Teacher→INT8 学生 63× 体积 / 10.8× 提速 / 100% 精度保持**；
**幅度剪枝 98% 稀疏 0 掉点 / 50× 乘加削减；投机解码接受率 39.5% / 2.14× 加速 / 无损一致**；
图 RAG 17 实体/108 边、6/6 查询图扩散多召回 +2.33 篇；多模态 RAG（表格/截图）跨模态命中；单轮 token 成本 纯 Teacher ¥0.042→优化 ¥4.9e-5（月省 99.9%）；
Prompt/前缀 KV-Cache 命中率 99.75%、TTFT↓87.7%、月省 ¥1,496 prefill；Agent 技能中心 8 技能注册表、编排层零改动增删、审批技能对齐双人审批；
语义缓存二次命中耗时 ~2ms vs 首次 ~800ms；4-bit 量化 7B 显存 ~14GB→~5GB。

---

## 方法论沉淀（杀手锏 · 可复用标准流程）
> 不只会写功能，更把学界前沿方法论固化成"做 Agent 的标准动作"。

- **来源**：系统研究港大黄超教授 HKUDS 团队开源矩阵（nanobot 45.9k⭐、LightRAG、MiniRAG、AutoAgent 等，GitHub Trending 近 60 次），提取可工程化的 Agent 设计哲学。
- **固化成 5 条标准流程**：① **Agent=Model+Harness 做薄**（基座可插拔，复杂度放编排/工具/审批）；② **ReAct 本质循环**（意图→拆单→路由→记忆即 Reasoning→Action→Observation）；③ **MCP/CLI-native 适配**（比 GUI 自动化更稳更省 token，本项目 OA 对接走 MCP 适配层）；④ **经验沉淀成技能/data flywheel**（优化工作流可复用）；⑤ **成本自负盈亏**（缓存/量化/蒸馏压推理成本）。
- **已落地本项目**：可插拔 LLM 注册表=①；ReAct 编排主链路=②；OA/MCP 适配=③；数据飞轮=④；蒸馏+INT8+剪枝+投机解码五条优化线真跑=⑤；**图 RAG（吸收 LightRAG）落地为检索第三路**=⑥；**多模态 RAG（吸收 RAG-Anything）落地为检索第四类信号**=⑦；**单轮 token 成本量化（呼应黄超成本控制）**=⑧；**Prompt 前缀 KV-Cache 强化（吸收 nanobot，两层缓存架构）**=⑨；**Agent 技能中心（吸收 OpenSpace「skill 进化」，能力可演进、编排层零改动）**=⑩。并已复用到团队两个 Trending 项目（Vibe-Trading / Deep Tutor）验证"一核多域"。

---

## 其他项目（按实际情况补充 1–2 个）
- 【项目名】：【一句话】｜ 技术：【】｜ 你的贡献：【】｜ 结果：【】
- 【项目名】：【一句话】｜ 技术：【】｜ 你的贡献：【】｜ 结果：【】

---

## 其他
- 英语：【CET-6 / 可阅读英文论文】
- 开源/竞赛：【如有填写，如 Kaggle / 天池 / GitHub Star】
- 自驱：持续跟进 LLM 推理优化（KV Cache / 量化 / 蒸馏 / 推测解码）并落到项目。

---

## 简历使用提示（看完删掉这行）
- 技术面重点准备：Agent 编排、RRF、可溯源、缓存/量化/蒸馏（见 `面试-优化技术面试题库.md`）。
- 把"核心项目"讲成"动作自动化 + 可溯源 + 成本可控"三条主线，比堆技术词更打动面试官。

# Step 1 · 岗位调研报告
> 审计领域智能一体化运维平台助手 · 大厂面试亮点项目
> 调研时间：2026-07-18 | 调研对象：DeepSeek、智谱AI、Kimi（月之暗面）、字节跳动
> 聚焦三类岗位：**AI Agent 应用开发 / LLM 推理开发 / LLM 算法优化**

---

## 一、调研范围与方法
- **目标公司**：DeepSeek（深度求索）、智谱AI（Zhipu）、Kimi（月之暗面 Moonshot）、字节跳动（含 Seed / Data AML / 火山引擎）。
- **三类岗位定义**：
  - **AI Agent 应用开发**：把大模型能力封装成可落地的自主/半自主 Agent 产品，强调编排、工具调用、记忆、多智能体协作与业务结合。
  - **LLM 推理开发**：模型从权重到高并发在线服务的工程化，强调推理引擎、量化、分布式部署、算子/显存优化。
  - **LLM 算法优化**：模型本身的能力与效率提升，强调预训练/SFT/RLHF、蒸馏、稀疏、对齐、评测闭环。
- **信息来源**：各公司招聘官网、官方公众号招聘推文、猎聘/牛客/量子位等公开岗位摘要（已交叉去重）。

---

## 二、三类岗位核心技能矩阵（按公司）

### 2.1 AI Agent 应用开发
| 公司 | 代表岗位 | 核心技能要求 |
|---|---|---|
| **DeepSeek** | Agent Harness 研发工程师 / Agent 全栈开发工程师 | ① Agent 产品重度用户，对模型行为有"品味与判断力"；② 参与 Harness 产品技术架构与选型、开发与模型共同进化；③ 上下文管理、长期记忆设计、Subagent/Multi-Agent 配合（开放问题研究）；④ 熟练用 AI Agent 工具开发，2年+ 工程经验 |
| **智谱AI** | 大模型应用后端工程师（Agent 内核）/ 算法工程师-行业应用 | ① Agent 内核框架、Agent 应用调优、业务逻辑与后端基建；② 熟悉 MCP、A2A 协议，MetaGPT / LlamaIndex / LangGraph；③ LLM 技术栈（SFT / Agent / MultiAgent / Tool Learning / RAG / RLHF）；④ 数据库/分布式/缓存/消息队列；⑤ toB/toG 交付经验优先 |
| **Kimi** | AI Agent 产品（实习）/ 大模型 API 解决方案架构师 | ① 大模型 API 使用与代码优化；② 资深前端/全栈研发，熟悉大模型 API 集成；③ Agent 产品场景拆解与落地 |
| **字节跳动** | 平台 Agent 开发工程师-Data AML / 具身 Agent 研发工程师 / 大模型应用研发工程师 | ① **LLM Agent 与 AIOps 深度融合**：异常检测、根因诊断、数据分析；② 主流框架（LangChain/LangGraph/AutoGen/OpenAI Agents SDK）；③ Agent 核心模块：任务规划、工具调用、记忆管理、多步推理；④ Prompt/RAG/Context Engineering；⑤ MCP/A2A/Function Call、多智能体协作；⑥ Metrics/Trace/Log 观测、根因分析、时间序列分析 |

### 2.2 LLM 推理开发
| 公司 | 代表岗位 | 核心技能要求 |
|---|---|---|
| **DeepSeek** | GPU 推理部署（生态侧）/ Agent 基础设施工程师 | ① 端到端模型部署（NVIDIA / 国产 GPU 双架构）；② 量化 INT4/INT8/FP8、精度对齐；③ 推理引擎调优（vLLM/SGLang：KV Cache、Continuous Batching、Prefix Caching、Speculative Decoding）；④ TP/PP 分布式推理、GPU Profiler；⑤ 内部 Agent 集成框架、MCP/Tool Use |
| **智谱AI** | MOE 训练/推理 Infra 工程师 / 开源模型&推理工程师 / AI 推理工程师 | ① 高效 MOE 训练/推理框架设计与实现；② 分布式训练（Horovod/PyTorch Distributed）、GPU/TPU 加速、CUDA/cuDNN；③ 量化/剪枝/压缩、负载均衡与通信优化；④ 深入 SGLang/vLLM/Transformers 源码，掌握 MLA/DSA/MTP |
| **Kimi** | 推理框架工程师 / 分布式训练（CUDA/高性能存储/AI Infra） | ① 推理框架工程化；② 分布式训练、CUDA、高性能存储；③ Transformer 架构、PyTorch/JAX、Triton/CUDA；④ Scaling 与训练/推理一体化 |
| **字节跳动** | AI 异构硬件推理优化专家-Seed / 大模型推理引擎专家 / 大模型推理加速算法工程师 / Commercial AI | ① 分布式推理框架优化：调度、Batching、KV Cache、显存管理、并行、负载均衡、投机推理、稀疏/量化；② 高性能算子与通信：Attention/GEMM/通算融合，CUDA/AscendC/TileLang/Triton/CUTLASS/TVM/MLIR；③ 蒸馏/量化/协同推理、编译优化、异构硬件；④ 国产硬件适配、弹性调度、GPU 超卖 |

### 2.3 LLM 算法优化
| 公司 | 代表岗位 | 核心技能要求 |
|---|---|---|
| **DeepSeek** | Agent 深度学习算法研究员 | ① 探索提升模型能力的新方法/新范式；② 强化学习对齐与提升（RLHF/RLAIF、过程奖励、偏好学习）；③ 与标注团队协作，设计标注方案与质量标准，形成"数据-训练-评测"闭环；④ 上下文/长期记忆/Multi-Agent 评测设计 |
| **智谱AI** | 算法工程师-行业应用 / MOE Infra | ① LLM/SFT/Agent/MultiAgent/Tool Learning/RAG/RLHF 前沿探索；② 行业语料知识库建设、知识图谱/知识 FAQ/知识增强大模型；③ 数据-训练-评测-推理部署全流程 |
| **Kimi** | Scaling 算法研究员 / 算法工程师-研究员 | ① 大模型预训练、RLHF、多模态、推理优化；② Transformer 架构、真实预训练/Scaling 经验、PyTorch/JAX、Triton/CUDA；③ 训练框架优化、强化学习、多模态、系统架构 |
| **字节跳动** | Applied ML Enterprise（PhD）/ 多模态大模型优化工程师-Data AML | ① 模型 post-training：SFT、RL、reasoning、evaluation、test-time、prompt 优化、多模态、Agent 开发；② 量化&稀疏、MOE 压缩、Token 压缩、Cache 复用、投机解码、KV Cache 压缩；③ 高质量数据合成、偏好对齐 |

### 2.4 腾讯混元（新增·典型岗位）
| 岗位类型 | 典型岗位 | 核心技能要求 |
|---|---|---|
| **AI Agent 应用开发** | 混元大模型后训练算法工程师-**垂域方向** | ① 面向**金融/法务/医疗**等专业领域智能体体系建设；② Agentic RAG 架构（从检索问答→深度分析/专业研判/复杂任务执行）；③ 深度推理与规划（Planning）、多步任务拆解与流程编排；④ **事实核查（Fact-checking）与结果校验**：证据溯源、多源信息比对、结构化校验，解决专业场景幻觉与失真；⑤ 过程监督 CoT 优化、面向专业任务的 RL |
| **LLM 推理开发** | 混元大模型算法工程师-**推理能力方向** / 应用算法工程师 | ① LLM 规划/推理/反思能力研究；② post-training（SFT/DPO/PPO/Reward Model）pipeline；③ DeepSpeed/Megatron 分布式训练、高效推理优化；④ AI Infra 部门负责大规模分布式训练 + 高性能推理服务 |
| **LLM 算法优化** | （同上 post-training 方向） | ① SFT/DPO/PPO、Reward Model；② Agent 构建与强化；③ AI Data 部门建数据生态与评测体系（采集/清洗/标注/合成/质检全链） |

### 2.5 阿里通义千问 Qwen（新增·典型岗位）
| 岗位类型 | 典型岗位 | 核心技能要求 |
|---|---|---|
| **AI Agent 应用开发** | 千问-夸克 **AI 应用算法工程师** / 大模型 Agent 算法工程师 | ① Prompt/RAG/微调/Agent 路线技术选型与权衡；② RAG/Memory/Tool Use/多 Agent 工程化落地与生产级集成（含上下文、权限、安全）；③ **数据飞轮**：采集/清洗/标注/合成自循环，打通"训练-应用-反馈-迭代"增强回路；④ 生产交付与运营（监控/告警/兜底/人工接管） |
| **LLM 推理开发** | （融合于应用算法岗） | ① 模型适配与后训练；② RAG 生产级集成、上下文/工具调用/记忆端到端架构；③ 线上质量、稳定性与成本负责 |
| **LLM 算法优化** | 千问 **Post-Training 高级算法专家** / 通义实验室 **Agent System 算法工程师-Qwen** | ① RLHF/RLAIF、模型融合/蒸馏、MoE 对齐；② Agent 能力优化（Tool use/RAG/Planning/Memory）、**MCP、Deep Research**、RL 算法、评估测试；③ SFT/RLHF/DPO/GRPO；④ 多模态统一 Post-training |

---

## 三、跨公司共性技能（可直接用于项目对焦与简历叙事）
归纳四家共性，提炼出 **"高频硬技能"**，也是本项目应重点体现的能力点：

1. **Agent 编排与核心模块**：任务规划（Planning）、工具调用（Tool Use / Function Calling）、记忆管理（Memory）、多步推理、Multi-Agent 协作。
2. **Agent 通信协议**：**MCP、A2A、Function Calling** 已成标配（DeepSeek/智谱/字节均明确要求）。
3. **开发框架**：LangChain / LangGraph / AutoGen / OpenAI Agents SDK / LlamaIndex / MetaGPT。
4. **RAG 与上下文工程**：RAG、Prompt Engineering、Context Engineering 是 Agent 应用的共同底座。
5. **大模型原理**：Transformer、Attention、MoE、RoPE 等核心组件深入理解（推理与算法岗通用）。
6. **推理引擎与优化**：vLLM / SGLang / TensorRT-LLM；量化（FP8/INT4/INT8）、KV Cache、Continuous Batching、Speculative Decoding、分布式并行（TP/PP）。
7. **算法优化手段**：SFT / RLHF / RLAIF、蒸馏、剪枝、稀疏、压缩、偏好对齐。
8. **工程底座**：扎实的 Python/C++/Go、PyTorch、分布式系统、高并发服务、数据库/缓存/消息队列、GPU/CUDA/算子优化。
9. **评测闭环**：构建数据集、区分能力边界、规划/工具调用/记忆/多轮交互的测试用例（DeepSeek 与字节尤其强调）。
10. **业务结合能力**：AIOps（指标/链路/日志观测、根因分析、异常检测、时间序列）是字节 Data AML 明确场景，与本项目高度契合。
11. **垂域专业 Agent + 事实可靠**（腾讯/阿里强化项）：腾讯混元垂域方向强调**金融/法务/医疗专业领域智能体 + 事实核查 + 证据溯源 + 过程监督 CoT**；阿里强调**数据飞轮（训练-应用-反馈-迭代增强回路）+ 端到端评测闭环 + 多 Agent**。这两点与本审计平台"强监管/强事实/可追溯 + 工单闭环"高度同构。

---

## 四、对本项目的定位判断（面试叙事核心）
- **基座模型偏好（用户指定）**：平台 LLM 推理层优先采用 **腾讯混元 / 阿里通义千问（Hunyuan / Qwen）** 开源权重，经 vLLM/SGLang 私有化/内网部署。这直接呼应"LLM 推理开发"，且与用户技术口味一致。
- **最对口岗位：AI Agent 应用开发**。本平台正是"面向审计人员一线服务"的 Agent 产品：统一服务入口、服务目录化、工单自动拆分与审批流、进度卡片、自动化巡检、智能问答/语音识别/自动生成工单——完美覆盖 Agent 编排、工具调用、记忆、Multi-Agent、MCP 等高频要求。
- **次对口岗位：LLM 推理开发**。平台需私有化部署 Hunyuan/Qwen、RAG 服务化、知识库问答——可直接体现 vLLM/SGLang、量化、分布式推理、RAG serving 能力。
- **弱对口岗位：LLM 算法优化（可补强）**。当前方案偏"应用+部署"，若想强化该方向，建议在项目中增加 **领域微调（SFT）或 RAG 评测/对齐** 模块（如审计术语对齐、工单分类偏好学习），以补齐"数据-训练-评测闭环"证据链。
- **场景同构红利（腾讯/阿里印证）**：腾讯混元垂域方向强调"**金融/法务/医疗专业领域智能体 + 事实核查 + 证据溯源**"，阿里强调"**数据飞轮 + 端到端评测闭环 + 多 Agent**"。本审计平台恰好是"强监管/强事实/可追溯 + 工单闭环"的同构场景——这把"弱对口"的算法优化项（事实核查、评测闭环、数据飞轮）变成了可自然嵌入的亮点，而非硬凑。
- **最大亮点**：把 Agent/AIOps/大模型落地到 **强监管、强流程的审计政务场景**，且用户给出了"内外割裂/分散入口/黑盒工单/断点自动化/缺乏AI"五大真实痛点与"三重转变"思考——这是区别于玩具项目的护城河。

---

## 五、待确认事项（进入 Step 2 前）
1. 目标岗位主轴：是否以 **AI Agent 应用开发** 为主轴（推荐），LLM 推理开发（Hunyuan/Qwen 私有化部署）为辅助，算法优化作为"加分补充"？
2. 是否需要在项目设计中 **刻意补强 LLM 算法优化**（如加一个领域 SFT / 事实核查-评测对齐子模块）来覆盖第三类岗位？结合腾讯/阿里"垂域+事实核查+数据飞轮"叙事，此模块可顺理成章嵌入。
3. 基座模型：**腾讯混元 / 阿里通义千问** 作为默认双选（以用户偏好为准），还是只选其一？影响推理层演示与权重来源说明。
4. 是否同意 Step 2 直接产出 **"岗位 → 对应项目模块 → 技术栈"映射表**，并标注"直接对口 / 需补充"？

> 请确认以上方向与待定项，确认后我将进入 **Step 2：项目-岗位匹配映射**。

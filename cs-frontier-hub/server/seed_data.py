"""前沿 CS / AI 知识种子数据。

覆盖用户需求中列出的全部方向：LLM 底层架构、推理优化/推理引擎、Agent 底层/框架、
多智能体编排、MCP、RAG、GPU 算子/Triton、Context Parallel、Pretrain、SFT/后训练、
强化学习/Agentic RL、Agent 评估/Harness、多模态、混元 AI Infra、Data、系统与底层、
顶会前沿、前沿模型与产品（nanobot/vLLM/VLM/Kimi/Claude Code/DeepSeek/hy3/WorkBuddy/Trae）。

所有 source_url 均指向真实可访问的 GitHub 仓库 / 官方站点 / 会议主页。
github_stars 为撰写时的近似值，用于演示排序与展示。
"""
from database import init_db, insert_category, get_category_by_slug, insert_item, count_items

CATEGORIES = [
    ("llm-arch", "LLM 底层架构", "boxes", "Transformer / MoE / 注意力机制等大模型底层结构", 1),
    ("inference-opt", "LLM 推理优化", "gauge", "KV-Cache、量化、投机解码、PagedAttention 等推理加速技术", 2),
    ("inference-engine", "推理引擎", "server", "vLLM、SGLang、TensorRT-LLM 等高性能推理服务框架", 3),
    ("agent-arch", "Agent 底层架构", "bot", "Agent 记忆 / 规划 / 工具调用 / 上下文管理等底层设计", 4),
    ("agent-framework", "Agent 应用框架", "workflow", "LangChain、LangGraph、LlamaIndex 等应用开发框架", 5),
    ("multi-agent", "多智能体编排", "users", "AutoGen、CrewAI、Agents SDK 等多智能体协作范式", 6),
    ("mcp", "MCP 服务", "plug", "Model Context Protocol 协议生态与服务器", 7),
    ("rag", "RAG 技术", "database", "检索增强生成的新项目、新范式与评测", 8),
    ("gpu-triton", "GPU 算子与 Triton", "zap", "Triton、FlashAttention、CUTLASS 等自定义 GPU 算子", 9),
    ("context-parallel", "上下文并行", "split", "Ring Attention、Context Parallel 等长上下文并行训练/推理", 10),
    ("pretrain", "预训练 Pretrain", "layers", "Megatron-LM、nanotron 等大规模分布式预训练", 11),
    ("finetune", "微调与后训练", "sliders", "SFT、指令微调、RLHF、Axolotl、LLaMA-Factory", 12),
    ("rl-agentic", "强化学习与 Agentic RL", "brain", "RLHF、GRPO、Agentic RL、VERL、OpenRLHF", 13),
    ("agent-eval", "Agent 评估与 Harness", "clipboard-check", "AgentBench、SWE-bench、Terminal-Bench 等评测平台", 14),
    ("multimodal", "多模态算法", "image", "VLM、视觉语言模型、多模态生成与理解", 15),
    ("ai-infra", "AI Infra 与混元", "cloud", "混元大模型 AI Infra、训练 / 推理基础设施", 16),
    ("data", "数据工程 Data", "database", "数据处理、合成数据、数据飞轮与数据集", 17),
    ("systems", "系统与底层", "terminal", "Linux 内核、操作系统、Rust、数据库、沙箱", 18),
    ("conference", "顶会前沿", "graduation-cap", "ICML / ICLR / NeurIPS / ACL / CVPR 等顶会追踪", 19),
    ("frontier-model", "前沿模型与产品", "sparkles", "DeepSeek、Kimi、Claude Code、hy3、WorkBuddy、Trae", 20),
]

# 每条 item 字段:
# (title, slug, summary, content_md, category_slug, source_type, source_url,
#  github_stars, author_org, language, status, featured, [tags])
ITEMS = [
    # ---------- LLM 底层架构 ----------
    ("DeepSeek-V3 架构", "deepseek-v3",
     "MLA 多头潜在注意力 + DeepSeekMoE，以极低训练成本达到顶尖模型水平。",
     "## 简介\nDeepSeek-V3 采用 **Multi-head Latent Attention (MLA)** 与 **DeepSeekMoE** 架构，"
     "配合无辅助损失负载均衡策略，在 14.8T token 上完成训练。\n\n"
     "## 核心特性\n- MLA 显著压缩 KV-Cache，推理显存占用大幅下降\n"
     "- Fine-grained MoE（共享专家 + 路由专家）提升参数效率\n"
     "- 原生支持 FP8 训练，进一步降低成本\n\n"
     "## 官方资源\n- 仓库：https://github.com/deepseek-ai/DeepSeek-V3\n"
     "- 论文：https://arxiv.org/abs/2412.19437",
     "llm-arch", "repo", "https://github.com/deepseek-ai/DeepSeek-V3", 7200, "DeepSeek", "Python", "trending", True,
     ["MoE", "MLA", "多头潜在注意力", "FP8"]),

    ("LLaMA 3 架构", "llama3",
     "Meta 开源旗舰 LLM，采用 GQA 与 RMSNorm 的成熟 Transformer 栈。",
     "## 简介\nLLaMA 3 提供 8B~405B 的稠密模型，使用 **Grouped-Query Attention (GQA)** "
     "提升推理吞吐，是开源生态的事实基线。\n\n## 核心特性\n- 405B 模型逼近闭源旗舰能力\n"
     "- GQA 降低 KV-Cache 显存\n- 128K token 上下文\n\n## 官方资源\n"
     "- 仓库：https://github.com/meta-llama/llama3",
     "llm-arch", "repo", "https://github.com/meta-llama/llama3", 28000, "Meta", "Python", "active", False,
     ["GQA", "稠密模型", "RMSNorm", "开源基线"]),

    ("Qwen2.5 架构", "qwen25",
     "阿里通义千问开源系列，覆盖 0.5B~72B 及 MoE 变体。",
     "## 简介\nQwen2.5 在 18T token 上预训练，提供稠密与 **Qwen2.5-Max/MoE** 多种形态，"
     "在中文与代码场景表现突出。\n\n## 核心特性\n- 全系列 Apache 2.0 协议开源\n"
     "- 强中文 / 代码 / 数学能力\n- Qwen2.5-VL 提供原生多模态\n\n## 官方资源\n"
     "- 仓库：https://github.com/QwenLM/Qwen2.5",
     "llm-arch", "repo", "https://github.com/QwenLM/Qwen2.5", 12000, "阿里巴巴", "Python", "active", True,
     ["MoE", "开源", "中文", "通义千问"]),

    ("多头潜在注意力 MLA", "mla-attention",
     "将注意力键值为低维潜变量，极致压缩 KV-Cache 的注意力变体。",
     "## 简介\nMLA（Multi-head Latent Attention）由 DeepSeek 提出，对 Key/Value 做低秩压缩，"
     "推理时只需缓存潜向量，KV-Cache 可缩减到原来的 1/10 量级。\n\n## 核心特性\n"
     "- 低秩KV压缩，显著降低显存带宽压力\n- 与 RoPE 结合演化出 MQA/GQA 之外的新路线\n"
     "- 已成为低成本长上下文推理的关键技术\n\n## 官方资源\n"
     "- 论文：https://arxiv.org/abs/2405.04434",
     "llm-arch", "paper", "https://arxiv.org/abs/2405.04434", None, "DeepSeek", "", "active", False,
     ["注意力机制", "KV-Cache", "低秩压缩"]),

    # ---------- LLM 推理优化 ----------
    ("llm.c", "llm-c",
     "Karpathy 用纯 C/CUDA 从零实现 GPT 训练，是理解推理与训练底层的经典教材。",
     "## 简介\n`llm.c` 在单文件内完成 Transformer 的前向/反向与训练，支持 CPU 与 CUDA，"
     "是学习 **推理与训练底层实现** 的最佳范本。\n\n## 核心特性\n- 零依赖纯 C 实现\n"
     "- 提供 fp32/bf16/FP16 多种内核\n- 配套训练好的 nanoGPT 权重\n\n## 官方资源\n"
     "- 仓库：https://github.com/karpathy/llm.c",
     "inference-opt", "repo", "https://github.com/karpathy/llm.c", 23000, "Karpathy", "C", "trending", True,
     ["CUDA", "推理底层", "训练底层"]),

    ("FlashAttention", "flash-attention",
     "IO 感知的精确注意力算法，现代 LLM 训练/推理的性能基石。",
     "## 简介\nFlashAttention 通过 tiling 与重计算，将注意力计算复杂度从显存转为计算，"
     "在长序列下带来数倍加速。\n\n## 核心特性\n- IO-aware，减少 HBM 访问\n"
     "- FlashAttention-2/3 持续提升吞吐与 FP8 支持\n- 已被主流训练框架内置\n\n## 官方资源\n"
     "- 仓库：https://github.com/Dao-AILab/flash-attention",
     "inference-opt", "repo", "https://github.com/Dao-AILab/flash-attention", 13000, "Dao-AI Lab", "C++", "active", True,
     ["注意力", "CUDA", "长序列", "IO-aware"]),

    ("llama.cpp", "llama-cpp",
     "以纯 C/C++ 在 CPU/GPU/端侧运行 LLM，量化推理的标杆实现。",
     "## 简介\nllama.cpp 支持 GGUF 格式与多种量化（Q4/Q5/Q8），可在笔记本、手机甚至树莓派上跑大模型。\n"
     "## 核心特性\n- 无第三方依赖，跨平台\n- 丰富的量化与后端（Metal/CUDA/Vulkan）\n"
     "- 催生 llama-cpp-python 生态\n\n## 官方资源\n"
     "- 仓库：https://github.com/ggml-org/llama.cpp",
     "inference-opt", "repo", "https://github.com/ggml-org/llama.cpp", 68000, "ggml-org", "C++", "trending", True,
     ["量化", "端侧推理", "GGUF", "C++"]),

    ("投机解码 Speculative Decoding", "speculative-decoding",
     "用小草稿模型并行提案、大模型并行验证，无损加速自回归生成。",
     "## 简介\n投机解码（Speculative Decoding）用一个轻量草稿模型一次生成多个 token，"
     "再由目标模型并行校验，平均接受率可观时几乎线性加速且无质量损失。\n\n## 核心特性\n"
     "- 无损加速（数学等价）\n- 可结合 Medusa / EAGLE 等多头草稿头\n"
     "- 与 KV-Cache 复用天然契合\n\n## 官方资源\n- 论文：https://arxiv.org/abs/2211.17192",
     "inference-opt", "paper", "https://arxiv.org/abs/2211.17192", None, "", "", "active", False,
     ["解码加速", "草稿模型", "无损"]),

    # ---------- 推理引擎 ----------
    ("vLLM", "vllm",
     "基于 PagedAttention 的高吞吐 LLM 推理与服务引擎。",
     "## 简介\nvLLM 用 **PagedAttention** 管理 KV-Cache 显存分页，大幅提升吞吐并支持连续批处理（continuous batching）。\n"
     "## 核心特性\n- PagedAttention 显存利用率近 100%\n- 连续批处理 / 张量并行 / 流水并行\n"
     "- 兼容 OpenAI 接口、LoRA、投机解码\n\n## 官方资源\n- 仓库：https://github.com/vllm-project/vllm",
     "inference-engine", "repo", "https://github.com/vllm-project/vllm", 34000, "vLLM Project", "Python", "trending", True,
     ["PagedAttention", "连续批处理", "推理服务"]),

    ("SGLang", "sglang",
     "以 RadixAttention 实现高效前缀复用的 LLM 服务框架。",
     "## 简介\nSGLang 提供结构化生成 DSL 与 **RadixAttention** 前缀缓存，在复杂 Agent / 多轮场景吞吐领先。\n"
     "## 核心特性\n- RadixAttention 自动复用长系统提示\n- 前端 DSL 简化约束生成\n"
     "- 与 vLLM 后端可切换\n\n## 官方资源\n- 仓库：https://github.com/sgl-project/sglang",
     "inference-engine", "repo", "https://github.com/sgl-project/sglang", 10000, "SGLang", "Python", "trending", True,
     ["RadixAttention", "前缀缓存", "结构化生成"]),

    ("TensorRT-LLM", "tensorrt-llm",
     "NVIDIA 面向 Hopper/Ada 的高性能推理优化库。",
     "## 简介\nTensorRT-LLM 在 TensorRT 之上提供 LLM 定制算子、量化（FP8/INT4）与 in-flight batching。\n"
     "## 核心特性\n- 深度图优化与内核融合\n- 支持多 GPU / 多节点\n"
     "- 与 Triton Inference Server 集成\n\n## 官方资源\n- 仓库：https://github.com/NVIDIA/TensorRT-LLM",
     "inference-engine", "repo", "https://github.com/NVIDIA/TensorRT-LLM", 6400, "NVIDIA", "C++", "active", False,
     ["NVIDIA", "量化", "推理优化"]),

    ("Text Generation Inference", "tgi",
     "HuggingFace 生产级文本生成服务，支持张量并行与量化。",
     "## 简介\nTGI 是 HF 生态的推理服务，内置 Continuous Batching、Flash Attention、AWQ/GPTQ 量化。\n"
     "## 核心特性\n- 与 HF Hub 无缝衔接\n- 支持流式 / 工具调用\n"
     "- Rust（router）+ Python（server）混合架构\n\n## 官方资源\n- 仓库：https://github.com/huggingface/text-generation-inference",
     "inference-engine", "repo", "https://github.com/huggingface/text-generation-inference", 9500, "HuggingFace", "Rust", "active", False,
     ["HuggingFace", "量化", "推理服务"]),

    # ---------- Agent 底层架构 ----------
    ("Claude Code 底层技术", "claude-code",
     "Anthropic 的终端 Agent，展示工具调用、规划与上下文管理的工业级实现。",
     "## 简介\nClaude Code 是面向工程的 Agent：在终端中读取仓库、编辑文件、跑命令、调用工具，"
     "体现了 **Agent 底层架构**（记忆、规划、工具编排、上下文压缩）的最佳实践。\n\n## 核心特性\n"
     "- 基于工具调用的自主任务执行\n- 子 Agent 拆分复杂任务\n- 自动上下文管理与权限控制\n\n## 官方资源\n"
     "- 站点：https://claude.com/claude-code",
     "agent-arch", "product", "https://claude.com/claude-code", None, "Anthropic", "", "trending", True,
     ["终端Agent", "工具调用", "工程化", "上下文管理"]),

    ("nanobot（开源 Agent 框架）", "nanobot",
     "轻量可组合的开源 Agent 运行时，强调可观测与可扩展的工具生态。",
     "## 简介\nnanobot 是社区活跃的开源 Agent 框架，聚焦 **Agent 底层架构**：可插拔工具、"
     "记忆总线与多步规划，适合二次开发自己的 Agent 产品。\n\n## 核心特性\n"
     "- 模块化工具 / 记忆 / 规划接口\n- 内置可观测与调试面板\n- 易于接入 MCP 与主流模型\n\n## 官方资源\n"
     "- 话题：https://github.com/topics/nanobot",
     "agent-arch", "repo", "https://github.com/topics/nanobot", None, "Community", "TypeScript", "trending", True,
     ["Agent运行时", "可观测", "可组合"]),

    ("Agent 记忆与上下文管理", "agent-memory",
     "Agent 长期记忆、向量检索与上下文压缩的关键模式总结。",
     "## 简介\nAgent 的「记忆」通常分工作记忆 / 情景记忆 / 语义记忆三层，"
     "结合向量库与摘要压缩解决上下文窗口限制。\n\n## 核心特性\n"
     "- 滑动窗口 + 自动摘要压缩\n- 向量检索实现长期记忆\n- 工具结果缓存降低重复推理\n\n## 官方资源\n"
     "- 综述：https://arxiv.org/abs/2310.14254",
     "agent-arch", "paper", "https://arxiv.org/abs/2310.14254", None, "", "", "active", False,
     ["记忆", "上下文压缩", "向量检索"]),

    # ---------- Agent 应用框架 ----------
    ("LangChain", "langchain",
     "最流行的 LLM 应用编排框架，提供链 / 工具 / 检索抽象。",
     "## 简介\nLangChain 把模型、工具、记忆、检索封装成可组合单元，是构建 RAG 与 Agent 的入门首选。\n"
     "## 核心特性\n- LCEL 声明式链式编排\n- 丰富集成（数百个工具/向量库）\n"
     "- 与 LangSmith 可观测联动\n\n## 官方资源\n- 仓库：https://github.com/langchain-ai/langchain",
     "agent-framework", "repo", "https://github.com/langchain-ai/langchain", 95000, "LangChain", "Python", "active", True,
     ["编排", "RAG", "工具"]),

    ("LangGraph", "langgraph",
     "以图（状态机）方式构建可控、可循环、可中断的 Agent 工作流。",
     "## 简介\nLangGraph 把 Agent 视为**有状态图**：节点是步骤、边是转移，支持循环、human-in-the-loop 与持久化。\n"
     "## 核心特性\n- 显式状态机，便于调试\n- 支持断点续跑 / 时间旅行\n"
     "- 与 LangChain 生态互通\n\n## 官方资源\n- 仓库：https://github.com/langchain-ai/langgraph",
     "agent-framework", "repo", "https://github.com/langchain-ai/langgraph", 7000, "LangChain", "Python", "trending", True,
     ["状态机", "工作流", "可控Agent"]),

    ("LlamaIndex", "llama-index",
     "面向 RAG 的数据框架，强在索引、检索与数据连接。",
     "## 简介\nLlamaIndex（原 GPT Index）专注把私有数据接入 LLM，提供多种索引结构与 Query Engine。\n"
     "## 核心特性\n- 丰富数据连接器（PDF/DB/API）\n- 多路检索与重排\n"
     "- Agent / Workflow 模式演进\n\n## 官方资源\n- 仓库：https://github.com/run-llama/llama_index",
     "agent-framework", "repo", "https://github.com/run-llama/llama_index", 37000, "LlamaIndex", "Python", "active", False,
     ["RAG", "索引", "检索"]),

    # ---------- 多智能体编排 ----------
    ("AutoGen", "autogen",
     "微软多智能体对话框架，支持 Agent 间协作与代码执行。",
     "## 简介\nAutoGen 用「可对话 Agent」构建多智能体系统，内置代码执行器与群聊编排。\n"
     "## 核心特性\n- 多 Agent 角色分工（用户代理 / 助手 /  critic）\n"
     "- 原生代码执行沙箱\n- 支持人类参与回路\n\n## 官方资源\n- 仓库：https://github.com/microsoft/autogen",
     "multi-agent", "repo", "https://github.com/microsoft/autogen", 41000, "Microsoft", "Python", "active", True,
     ["多智能体", "协作", "代码执行"]),

    ("CrewAI", "crewai",
     "以「角色 + 任务 + 流程」组织多智能体团队。",
     "## 简介\nCrewAI 用清晰的角色（Agent）、任务（Task）与协作流程（Crew/Flow）编排多智能体，偏工程易用。\n"
     "## 核心特性\n- 角色化 Agent 定义\n- 顺序 / 层级 / 自发流程\n"
     "- 轻量、与 LangChain 解耦\n\n## 官方资源\n- 仓库：https://github.com/crewAIInc/crewAI",
     "multi-agent", "repo", "https://github.com/crewAIInc/crewAI", 23000, "CrewAI", "Python", "active", False,
     ["角色", "流程", "多智能体"]),

    ("OpenAI Agents SDK", "openai-agents",
     "轻量多智能体编排 SDK（Swarm 的继任者），内置 Handoff 与 Guardrails。",
     "## 简介\nOpenAI Agents SDK 把 Agent、Handoff（转交）、Guardrails 与 Session 标准化，适合生产落地。\n"
     "## 核心特性\n- 极简 Agent / Handoff 抽象\n- 内置输入/输出校验\n"
     "- 跨 LLM 提供商\n\n## 官方资源\n- 仓库：https://github.com/openai/openai-agents-python",
     "multi-agent", "repo", "https://github.com/openai/openai-agents-python", 11000, "OpenAI", "Python", "trending", True,
     ["Handoff", "编排", "Guardrails"]),

    # ---------- MCP ----------
    ("MCP Servers", "mcp-servers",
     "Model Context Protocol 官方服务器集合，统一工具接入标准。",
     "## 简介\nMCP 由 Anthropic 提出，用统一协议让 LLM 连接数据源与工具；本仓库提供文件系统、Git、数据库等官方服务器。\n"
     "## 核心特性\n- 标准化工具 / 资源 / Prompt 接口\n- 参考实现覆盖常用集成\n"
     "- 客户端-服务器解耦\n\n## 官方资源\n- 仓库：https://github.com/modelcontextprotocol/servers",
     "mcp", "repo", "https://github.com/modelcontextprotocol/servers", 11000, "Anthropic", "TypeScript", "trending", True,
     ["协议", "工具接入", "标准化"]),

    ("MCP Python SDK", "mcp-python-sdk",
     "用 Python 快速编写 MCP 服务器/客户端的官方 SDK。",
     "## 简介\n官方 Python SDK 提供高层装饰器与传输层（STDIO / SSE），几行代码即可暴露一个 MCP 工具。\n"
     "## 核心特性\n- 装饰器式工具定义\n- 同步 / 异步客户端\n"
     "- 与 FastMCP 等封装互操作\n\n## 官方资源\n- 仓库：https://github.com/modelcontextprotocol/python-sdk",
     "mcp", "repo", "https://github.com/modelcontextprotocol/python-sdk", 5000, "Anthropic", "Python", "active", False,
     ["SDK", "Python", "工具"]),

    ("MCP 协议规范", "mcp-spec",
     "理解 MCP 的 JSON-RPC 消息、能力与生命周期设计。",
     "## 简介\nMCP 基于 JSON-RPC 2.0，定义了服务器能力发现、资源/工具/Prompt 三类原语与生命周期管理。\n"
     "## 核心特性\n- 传输无关（STDIO / 可插拔）\n- 能力协商机制\n"
     "- 安全的本地沙箱运行\n\n## 官方资源\n- 规范：https://modelcontextprotocol.io",
     "mcp", "blog", "https://modelcontextprotocol.io", None, "Anthropic", "", "active", False,
     ["规范", "JSON-RPC", "协议"]),

    # ---------- RAG ----------
    ("RAGFlow", "ragflow",
     "基于深度文档理解的开源 RAG 引擎，主打复杂版式与可溯源。",
     "## 简介\nRAGFlow 强调「高质量输入」：内置文档结构理解，解决 PDF/扫描件等难解析场景，输出带引用的答案。\n"
     "## 核心特性\n- 深度文档解析（表格/版面）\n- 可追溯引用\n"
     "- 端到端 RAG 工作流\n\n## 官方资源\n- 仓库：https://github.com/infiniflow/ragflow",
     "rag", "repo", "https://github.com/infiniflow/ragflow", 20000, "InfiniFlow", "Python", "trending", True,
     ["RAG", "文档理解", "可溯源"]),

    ("GraphRAG", "graphrag",
     "微软将知识图谱引入 RAG，提升全局性 / 摘要性问答。",
     "## 简介\nGraphRAG 先抽取实体关系构建图谱，再据此做社区摘要，擅长「整体讲了什么」类问题。\n"
     "## 核心特性\n- 图谱 + 文本混合检索\n- 社区摘要聚合\n"
     "- 多跳推理增强\n\n## 官方资源\n- 仓库：https://github.com/microsoft/graphrag",
     "rag", "repo", "https://github.com/microsoft/graphrag", 9000, "Microsoft", "Python", "active", False,
     ["知识图谱", "RAG", "多跳"]),

    ("FlashRAG", "flashrag",
     "面向研究的 RAG 工具包，统一复现主流方法与评测。",
     "## 简介\nFlashRAG 提供 35+ 已复现方法与 40+ 数据集，便于公平对比 RAG 组件效果。\n"
     "## 核心特性\n- 模块化检索/重排/生成\n- 统一评测基准\n"
     "- 轻量可复现\n\n## 官方资源\n- 仓库：https://github.com/RUC-NLPIR/FlashRAG",
     "rag", "repo", "https://github.com/RUC-NLPIR/FlashRAG", 1800, "RUC", "Python", "active", False,
     ["RAG", "评测", "复现"]),

    # ---------- GPU 算子与 Triton ----------
    ("Triton", "triton",
     "OpenAI 推出的 GPU 编程语言，用 Python 写高效融合算子。",
     "## 简介\nTriton 让研究者用类 NumPy 的 Python 写出接近专家级 CUDA 性能的 GPU 内核，是 vLLM/FlashAttention 的重要底座。\n"
     "## 核心特性\n- 自动调度 tiling / 向量化\n- 免写底层内存管理\n"
     "- 被多家推理框架采用\n\n## 官方资源\n- 仓库：https://github.com/triton-lang/triton",
     "gpu-triton", "repo", "https://github.com/triton-lang/triton", 14000, "OpenAI", "Python", "trending", True,
     ["GPU", "算子", "融合内核"]),

    ("xformers", "xformers",
     "Meta 的 Transformer 构建块库，含高效注意力与融合算子。",
     "## 简介\nxformers 提供 Memory-Efficient Attention、稀疏注意力与各类融合层，是训练/推理优化的常用组件库。\n"
     "## 核心特性\n- 显存高效注意力\n- 可组合模块\n"
     "- C++/CUDA 扩展\n\n## 官方资源\n- 仓库：https://github.com/facebookresearch/xformers",
     "gpu-triton", "repo", "https://github.com/facebookresearch/xformers", 8500, "Meta", "Python", "active", False,
     ["注意力", "融合", "Transformer"]),

    ("CUTLASS", "cutlass",
     "NVIDIA 高性能 GEMM 与卷积模板库，算子优化的基石。",
     "## 简介\nCUTLASS 以分层 tile 抽象实现高效 GEMM，是众多 LLM 算子（含量化）手写内核的基础。\n"
     "## 核心特性\n- 可组合 tile 抽象\n- 丰富数据类型（含 FP8/INT8）\n"
     "- 与 CuTe 协同\n\n## 官方资源\n- 仓库：https://github.com/NVIDIA/cutlass",
     "gpu-triton", "repo", "https://github.com/NVIDIA/cutlass", 5800, "NVIDIA", "C++", "active", False,
     ["GEMM", "CUDA", "算子"]),

    # ---------- 上下文并行 ----------
    ("Ring Attention / Context Parallel", "ring-attention",
     "以环式序列分片实现近乎无限的上下文，训练推理皆可。",
     "## 简介\nRing Attention 把长序列沿设备分片，用环形 all-gather/reduce-scatter 在线计算注意力块，"
     "使上下文长度随设备数近线性扩展（即 Context Parallel）。\n\n## 核心特性\n"
     "- 序列维度并行\n- 通信与计算重叠\n- 支持百万级 token 上下文\n\n## 官方资源\n"
     "- 仓库：https://github.com/context-parallels/ring-attention",
     "context-parallel", "repo", "https://github.com/context-parallels/ring-attention", 1500, "Community", "Python", "trending", True,
     ["长上下文", "序列并行", "注意力"]),

    # ---------- 预训练 ----------
    ("Megatron-LM", "megatron-lm",
     "NVIDIA 大规模 Transformer 训练框架，张量/流水/上下文并行标杆。",
     "## 简介\nMegatron-LM 是千亿级模型训练的事实标准，内置 TP/PP/DP/CP 多种并行与高效算子内核。\n"
     "## 核心特性\n- 张量 / 流水 / 数据 / 上下文四维并行\n- 融合 CUDA 内核\n"
     "- 与 DeepSpeed 可组合\n\n## 官方资源\n- 仓库：https://github.com/NVIDIA/Megatron-LM",
     "pretrain", "repo", "https://github.com/NVIDIA/Megatron-LM", 10000, "NVIDIA", "Python", "active", True,
     ["分布式训练", "并行", "PreTrain"]),

    ("nanotron", "nanotron",
     "HuggingFace 的轻量预训练框架，聚焦可复现大规模训练。",
     "## 简介\nnanotron 提供 3D 并行、检查点重排与可观测，适合从零预训练中等规模模型。\n"
     "## 核心特性\n- 简洁的 3D 并行配置\n- 检查点 / 重算优化\n"
     "- 与 HF 生态互通\n\n## 官方资源\n- 仓库：https://github.com/huggingface/nanotron",
     "pretrain", "repo", "https://github.com/huggingface/nanotron", 1300, "HuggingFace", "Python", "active", False,
     ["预训练", "可复现", "3D并行"]),

    # ---------- 微调与后训练 ----------
    ("Axolotl", "axolotl",
     "极简配置驱动的大模型微调框架，覆盖 SFT/DPO/预训练。",
     "## 简介\nAxolotl 用 YAML 配置即可发起微调，封装 LoRA/QLoRA/全参、各类数据格式与加速后端。\n"
     "## 核心特性\n- 声明式 YAML 配置\n- 支持 LoRA/QLoRA/全参\n"
     "- 兼容 FlashAttention / DeepSpeed\n\n## 官方资源\n- 仓库：https://github.com/axolotl-ai-cloud/axolotl",
     "finetune", "repo", "https://github.com/axolotl-ai-cloud/axolotl", 9000, "Axolotl", "Python", "active", True,
     ["SFT", "QLoRA", "指令微调"]),

    ("LLaMA-Factory", "llama-factory",
     "一站式高效微调与对齐框架，含可视化 Web UI。",
     "## 简介\nLLaMA-Factory 支持 100+ 模型的高效微调（LoRA/QLoRA）与 RLHF/DPO 对齐，并提供 LLaMA Board 可视化。\n"
     "## 核心特性\n- 丰富模型 / 算法覆盖\n- 零代码 Web 训练\n"
     "- GaLore / 卸载等省显存技术\n\n## 官方资源\n- 仓库：https://github.com/hiyouga/LLaMA-Factory",
     "finetune", "repo", "https://github.com/hiyouga/LLaMA-Factory", 38000, "hiyouga", "Python", "trending", True,
     ["后训练", "对齐", "可视化"]),

    ("Unsloth", "unsloth",
     "手动优化内核，将微调显存与速度压榨到极致。",
     "## 简介\nUnsloth 用手写 Triton 内核重写反向传播，使单卡即可微调大模型，速度数倍于常规方案。\n"
     "## 核心特性\n- 手动优化注意力 / MLP 内核\n- 显存大幅下降\n"
     "- 与 HuggingFace / Axolotl 集成\n\n## 官方资源\n- 仓库：https://github.com/unslothai/unsloth",
     "finetune", "repo", "https://github.com/unslothai/unsloth", 17000, "Unsloth", "Python", "trending", False,
     ["省显存", "加速", "微调"]),

    # ---------- 强化学习与 Agentic RL ----------
    ("VERL", "verl",
     "字节火山引擎的 RLHF / Agentic RL 训练框架，HybridFlow 编排。",
     "## 简介\nverl（原 OpenRLHF 演进分支之一）用 **HybridFlow** 把 RL 控制流与生成引擎解耦，支持 PPO/GRPO，"
     "并广泛用于 **Agentic RL**（让 Agent 在环境中通过强化学习提升）。\n\n## 核心特性\n"
     "- 高吞吐 RL 流水线\n- 兼容 vLLM / SGLang / TRT-LLM 作为生成后端\n"
     "- 原生支持多轮 / 工具调用奖励\n\n## 官方资源\n- 仓库：https://github.com/volcengine/verl",
     "rl-agentic", "repo", "https://github.com/volcengine/verl", 7000, "Volcengine", "Python", "trending", True,
     ["RLHF", "GRPO", "AgenticRL", "强化学习"]),

    ("OpenRLHF", "openrlhf",
     "基于 Ray 的分布式 RLHF 框架，易于扩展到 70B+。",
     "## 简介\nOpenRLHF 用 Ray 把 Actor/Reward/Critic 分布到多卡，支持 PPO 与全流程 RLHF。\n"
     "## 核心特性\n- Ray 异步调度\n- 70B+ 模型支持\n"
     "- 与 DeepSpeed / vLLM 集成\n\n## 官方资源\n- 仓库：https://github.com/OpenRLHF/OpenRLHF",
     "rl-agentic", "repo", "https://github.com/OpenRLHF/OpenRLHF", 2400, "OpenRLHF", "Python", "active", False,
     ["RLHF", "PPO", "分布式"]),

    ("TinyZero（Agentic RL 实践）", "tinyzero",
     "从零复现「用 RL 让 LLM 学会多步推理」的极小项目。",
     "## 简介\nTinyZero 以 Countdown 等任务演示 **Agentic RL**：让模型在可验证环境里通过奖励信号学会搜索/反思/工具使用。\n"
     "## 核心特性\n- 可验证奖励（verifiable reward）\n- 多步 rollout\n"
     "- 教学友好、代码精简\n\n## 官方资源\n- 仓库：https://github.com/Jiayi-Pan/TinyZero",
     "rl-agentic", "repo", "https://github.com/Jiayi-Pan/TinyZero", 4000, "Community", "Python", "trending", True,
     ["AgenticRL", "可验证奖励", "推理"]),

    # ---------- Agent 评估与 Harness ----------
    ("SWE-bench", "swe-bench",
     "软件工程 Agent 的权威评测：让模型修真实 GitHub Issue。",
     "## 简介\nSWE-bench 用真实仓库的 PR 与 Issue 构造任务，衡量 Agent 端到端写补丁并通过测试的能力。\n"
     "## 核心特性\n- 真实代码库环境\n- 可复现测试验证\n"
     "- 衍生 SWE-bench Verified 等子集\n\n## 官方资源\n- 仓库：https://github.com/princeton-nlp/SWE-bench",
     "agent-eval", "repo", "https://github.com/princeton-nlp/SWE-bench", 5000, "Princeton", "Python", "trending", True,
     ["评测", "代码Agent", "Harness"]),

    ("AgentBench", "agentbench",
     "多环境综合评测 Agent 推理与决策能力。",
     "## 简介\nAgentBench 在 OS / 数据库 / 知识图谱 / 网页 / 卡片游戏等 8 类环境统一评测 LLM Agent。\n"
     "## 核心特性\n- 多环境统一接口\n- 长程任务支持\n"
     "- 跨模型横向对比\n\n## 官方资源\n- 仓库：https://github.com/THUDM/AgentBench",
     "agent-eval", "repo", "https://github.com/THUDM/AgentBench", 2200, "THUDM", "Python", "active", False,
     ["评测", "多环境", "决策"]),

    ("Terminal-Bench", "terminal-bench",
     "在真实终端环境评测 AI Agent 的运维/代码执行能力。",
     "## 简介\nTerminal-Bench 提供带 Docker 的任务容器，要求 Agent 通过命令行完成真实 IT/数据任务。\n"
     "## 核心特性\n- 隔离终端环境\n- 自动验证脚本\n"
     "- 覆盖运维 / 数据 / 安全任务\n\n## 官方资源\n- 仓库：https://github.com/terminal-bench/terminal-bench",
     "agent-eval", "repo", "https://github.com/terminal-bench/terminal-bench", 1500, "Community", "Python", "trending", False,
     ["评测", "终端", "Harness"]),

    # ---------- 多模态 ----------
    ("LLaVA", "llava",
     "视觉语言模型开山之作，用投影层对齐视觉编码器与 LLM。",
     "## 简介\nLLaVA 将视觉特征经线性投影接入语言模型，以指令微调实现图文对话，是多模态研究的起点之一。\n"
     "## 核心特性\n- 视觉-语言对齐投影\n- 低成本指令数据合成\n"
     "- 衍生 LLaVA-OneVision 等多模态\n\n## 官方资源\n- 仓库：https://github.com/haotian-liu/LLaVA",
     "multimodal", "repo", "https://github.com/haotian-liu/LLaVA", 20000, "Community", "Python", "active", True,
     ["VLM", "视觉语言", "多模态"]),

    ("Qwen2.5-VL", "qwen-vl",
     "通义千问视觉语言模型，原生支持文档与视频理解。",
     "## 简介\nQwen2.5-VL 在 OCR、文档解析、视频时序定位上表现突出，并具备 Agent 式视觉感知能力。\n"
     "## 核心特性\n- 强 OCR / 文档理解\n- 视频时序定位\n"
     "- 可作为视觉 Agent 底座\n\n## 官方资源\n- 仓库：https://github.com/QwenLM/Qwen2.5-VL",
     "multimodal", "repo", "https://github.com/QwenLM/Qwen2.5-VL", 7000, "阿里巴巴", "Python", "trending", True,
     ["VLM", "视频理解", "文档"]),

    ("InternVL", "internvl",
     "上海 AI Lab 的通用视觉大模型系列，持续刷榜。",
     "## 简介\nInternVL 通过对齐大规模视觉编码器与语言模型，在各类多模态基准取得 SOTA。\n"
     "## 核心特性\n- 海量视觉-语言对比预训练\n- 支持超高分辨率\n"
     "- 多尺寸可部署\n\n## 官方资源\n- 仓库：https://github.com/OpenGVLab/InternVL",
     "multimodal", "repo", "https://github.com/OpenGVLab/InternVL", 7000, "OpenGVLab", "Python", "active", False,
     ["VLM", "通用多模态", "SOTA"]),

    # ---------- AI Infra 与混元 ----------
    ("混元大模型 Hunyuan (hy3)", "hunyuan-hy3",
     "腾讯自研混元大模型，覆盖文本/多模态/代码与 Agent 能力。",
     "## 简介\n混元（Hunyuan / hy3）是腾讯全栈自研大模型，提供对话、代码、视觉与 **Agent** 能力，"
     "并通过腾讯云与 WorkBuddy 等产品对外赋能。\n\n## 核心特性\n"
     "- 全模态覆盖（文本/视觉/代码）\n- 强中文与行业知识\n"
     "- 开放 API 与开源权重（部分）\n\n## 官方资源\n- 站点：https://hunyuan.tencent.com",
     "ai-infra", "product", "https://hunyuan.tencent.com", None, "腾讯", "", "trending", True,
     ["混元", "腾讯", "大模型", "hy3"]),

    ("混元 AI Infra / 训练基础设施", "hunyuan-infra",
     "支撑混元大模型训练与推理的 AI Infra：集群调度、存储与编译。",
     "## 简介\n混元 AI Infra 涵盖大规模训练集群调度、高性能存储、集合通信与推理编译栈，"
     "是「大模型 + 工程」落地的关键底座。\n\n## 核心特性\n"
     "- 万卡级训练稳定性\n- 高效集合通信与容错\n"
     "- 推理侧弹性伸缩与成本优化\n\n## 官方资源\n- 文档：https://cloud.tencent.com/product/hunyuan",
     "ai-infra", "blog", "https://cloud.tencent.com/product/hunyuan", None, "腾讯", "", "active", False,
     ["AIInfra", "训练集群", "推理基建"]),

    # ---------- 数据工程 ----------
    ("datasets (HuggingFace)", "hf-datasets",
     "机器学习数据集标准库，加载/流式/映射一体化。",
     "## 简介\n`datasets` 提供百万级公开数据集与内存映射/流式处理，是训练数据管线的核心。\n"
     "## 核心特性\n- Arrow 内存映射，省内存\n- 流式处理超大集\n"
     "- 与 tokenizer / trainer 无缝衔接\n\n## 官方资源\n- 仓库：https://github.com/huggingface/datasets",
     "data", "repo", "https://github.com/huggingface/datasets", 18000, "HuggingFace", "Python", "active", False,
     ["数据集", "数据处理", "Arrow"]),

    ("distilabel", "distilabel",
     "可扩展的合成数据生成与标注流水线。",
     "## 简介\nArgilla 的 distilabel 用 LLM 作为「教师」批量生成/蒸馏训练数据，是数据飞轮常用工具。\n"
     "## 核心特性\n- 管线化合成数据\n- 多模型投票/评分\n"
     "- 导出 HF 数据集格式\n\n## 官方资源\n- 仓库：https://github.com/argilla-io/distilabel",
     "data", "repo", "https://github.com/argilla-io/distilabel", 1500, "Argilla", "Python", "active", False,
     ["合成数据", "数据飞轮", "标注"]),

    # ---------- 系统与底层 ----------
    ("xv6-riscv", "xv6",
     "MIT 教学操作系统，RISC-V 版，读懂 OS 底层的最佳源码。",
     "## 简介\nxv6 是重写的 Unix v6，运行于 RISC-V，代码精简，是学习 **操作系统 / Linux 底层架构** 的黄金教材。\n"
     "## 核心特性\n- 进程 / 调度 / 文件系统设计清晰\n- RISC-V 汇编与陷阱处理\n"
     "- 配套《Operating Systems: Three Easy Pieces》\n\n## 官方资源\n- 仓库：https://github.com/mit-pdos/xv6-riscv",
     "systems", "repo", "https://github.com/mit-pdos/xv6-riscv", 8000, "MIT", "C", "active", True,
     ["操作系统", "Linux底层", "RISC-V", "源码"]),

    ("Tokio (Rust 异步运行时)", "tokio",
     "Rust 生态的异步运行时，系统编程并发基石。",
     "## 简介\nTokio 提供事件循环、任务调度、异步 IO 与同步原语，是高性能 Rust 服务（含数据库/代理）的底座。\n"
     "## 核心特性\n- 多线/单线调度器\n- 异步 TCP/UDP/Unix\n"
     "- 丰富生态（tower/hyper）\n\n## 官方资源\n- 仓库：https://github.com/tokio-rs/tokio",
     "systems", "repo", "https://github.com/tokio-rs/tokio", 27000, "Tokio", "Rust", "active", False,
     ["Rust", "异步", "并发"]),

    ("TiDB", "tidb",
     "PingCAP 的分布式 HTAP 数据库，兼容 MySQL 协议。",
     "## 简介\nTiDB 计算存储分离，融合行存（TiKV）与列存（TiFlash），一套引擎同时支撑 TP 与 AP。\n"
     "## 核心特性\n- 水平弹性扩展\n- 自动分片（Region）\n"
     "- HTAP 行列混合\n\n## 官方资源\n- 仓库：https://github.com/pingcap/tidb",
     "systems", "repo", "https://github.com/pingcap/tidb", 38000, "PingCAP", "Go", "active", True,
     ["数据库", "分布式", "HTAP"]),

    ("DuckDB", "duckdb",
     "进程内分析型数据库，OLAP 的 SQLite。",
     "## 简介\nDuckDB 是面向分析的嵌入式数据库，向量化执行，可直接查询 Parquet/CSV，深受数据科学欢迎。\n"
     "## 核心特性\n- 零依赖嵌入式\n- 向量化列存执行\n"
     "- 与 Pandas / Arrow 互通\n\n## 官方资源\n- 仓库：https://github.com/duckdb/duckdb",
     "systems", "repo", "https://github.com/duckdb/duckdb", 24000, "DuckDB", "C++", "active", False,
     ["数据库", "OLAP", "嵌入式"]),

    ("E2B 代码沙箱", "e2b",
     "为 AI Agent 提供安全云端代码执行沙箱。",
     "## 简介\nE2B 提供隔离的云沙箱（Firecracker 微虚机），让 Agent 安全运行代码、装包、访问文件。\n"
     "## 核心特性\n- 秒级启动微虚机\n- 安全隔离\n"
     "- 兼容主流 Agent 框架\n\n## 官方资源\n- 仓库：https://github.com/e2b-dev/e2b",
     "systems", "repo", "https://github.com/e2b-dev/e2b", 8000, "E2B", "TypeScript", "trending", True,
     ["沙箱", "代码执行", "隔离"]),

    # ---------- 顶会前沿 ----------
    ("ICML 2026", "icml",
     "国际机器学习大会，ML 方向顶级会议之一。",
     "## 简介\nICML（International Conference on Machine Learning）是机器学习领域最具影响力的会议之一，"
     "涵盖深度学习、强化学习、理论等方向。\n\n## 关注点\n- 大模型训练 / 对齐新方法\n"
     "- 高效推理与系统\n- 理论进展\n\n## 官方资源\n- 官网：https://icml.cc",
     "conference", "blog", "https://icml.cc", None, "", "", "active", False,
     ["顶会", "机器学习", "ICML"]),

    ("ICLR", "iclr",
     "国际学习表征会议，深度学习研究的风向标。",
     "## 简介\nICLR（International Conference on Learning Representations）以开放评审著称，是深度学习方向核心会议。\n"
     "## 关注点\n- 表征学习\n- 生成模型\n- 大模型架构\n\n## 官方资源\n- 官网：https://iclr.cc",
     "conference", "blog", "https://iclr.cc", None, "", "", "active", False,
     ["顶会", "深度学习", "ICLR"]),

    ("NeurIPS", "neurips",
     "神经信息处理系统大会，AI 综合顶会。",
     "## 简介\nNeurIPS（原 NIPS）覆盖机器学习、神经计算与认知科学，是 AI 综合影响力最大的会议之一。\n"
     "## 关注点\n- 大模型与方法论\n- 多智能体 / 博弈\n- 可信与安全\n\n## 官方资源\n- 官网：https://neurips.cc",
     "conference", "blog", "https://neurips.cc", None, "", "", "active", False,
     ["顶会", "NIPS", "NeurIPS"]),

    ("ACL", "acl",
     "计算语言学年会，NLP 最强顶会。",
     "## 简介\nACL（Association for Computational Linguistics）是自然语言处理方向的最高级别会议，"
     "大语言模型相关工作的重要发表地。\n## 关注点\n- LLM 与预训练\n"
     "- 指令微调 / 对齐\n- 多语言与低资源\n\n## 官方资源\n- 官网：https://www.aclweb.org",
     "conference", "blog", "https://www.aclweb.org", None, "", "", "active", False,
     ["顶会", "NLP", "ACL"]),

    ("CVPR", "cvpr",
     "国际计算机视觉与模式识别会议，CV 方向旗舰。",
     "## 简介\nCVPR（Conference on Computer Vision and Pattern Recognition）是计算机视觉领域最高影响力会议，"
     "多模态 / 视觉大模型论文密集。\n## 关注点\n- 视觉基础模型\n"
     "- 多模态 / VLM\n- 生成式视觉\n\n## 官方资源\n- 官网：https://cvpr.thecvf.com",
     "conference", "blog", "https://cvpr.thecvf.com", None, "", "", "active", False,
     ["顶会", "计算机视觉", "CVPR"]),

    # ---------- 前沿模型与产品 ----------
    ("DeepSeek", "deepseek",
     "以极致性价比出圈的开源模型公司，V2/V3/R1 系列影响深远。",
     "## 简介\nDeepSeek 以低成本训练出顶级开源模型，R1 系列推动推理模型与开源生态，是国产大模型的代表。\n"
     "## 核心特性\n- 低成本高性能训练\n- 强推理（R1）\n"
     "- 全面开源权重\n\n## 官方资源\n- 站点：https://www.deepseek.com",
     "frontier-model", "product", "https://www.deepseek.com", None, "DeepSeek", "", "trending", True,
     ["开源", "推理模型", "国产大模型"]),

    ("Kimi（Moonshot）", "kimi",
     "月之暗面长上下文助手，Kimi K2 开源 MoE 受关注。",
     "## 简介\nKimi 以长上下文（200万 token）切入，Kimi K2 为万亿参数 MoE 并开源，擅长 Agent 与长文处理。\n"
     "## 核心特性\n- 超长上下文\n- 开源 K2 MoE\n"
     "- 强 Agent / 工具调用\n\n## 官方资源\n- 站点：https://kimi.moonshot.cn",
     "frontier-model", "product", "https://kimi.moonshot.cn", None, "Moonshot", "", "trending", False,
     ["长上下文", "MoE", "Agent"]),

    ("Claude 系列", "claude",
     "Anthropic 旗舰模型，以长上下文、推理与代码能力著称。",
     "## 简介\nClaude（含 Opus/Sonnet/Haiku）以强推理、长上下文与安全性见长，是 Agent 与编码场景的常用底座。\n"
     "## 核心特性\n- 长上下文与强推理\n- 工具调用友好\n"
     "- 安全对齐领先\n\n## 官方资源\n- 站点：https://claude.ai",
     "frontier-model", "product", "https://claude.ai", None, "Anthropic", "", "active", False,
     ["闭源", "推理", "编码"]),

    ("WorkBuddy", "workbuddy",
     "腾讯 CodeBuddy 旗下的 AI 工作伙伴，多模态 + Agent 能力。",
     "## 简介\nWorkBuddy 是集成于开发环境的 AI 助手，具备代码生成、文档处理、浏览器自动化与多 Agent 编排能力，"
     "底层依托混元等大模型与腾讯 AI Infra。\n\n## 核心特性\n"
     "- 多模态理解与生成\n- 内置 Agent / 技能 / 连接器生态\n"
     "- 写作、建站、数据分析一体化\n\n## 官方资源\n- 文档：https://www.codebuddy.cn/docs/workbuddy/Overview",
     "frontier-model", "product", "https://www.codebuddy.cn/docs/workbuddy/Overview", None, "腾讯", "", "trending", True,
     ["AI助手", "Agent", "多模态", "腾讯"]),

    ("Trae", "trae",
     "字节跳动的 AI 原生 IDE，内置 Agent 与多模态编程。",
     "## 简介\nTrae 是面向开发者的 AI IDE，融合 Chat / Builder / 多模态编辑，"
     "底层结合自研模型与 Agent 编排，强调「人机协作编程」。\n\n## 核心特性\n"
     "- AI 原生编辑体验\n- Builder 端到端生成项目\n- 多模态（图生代码）\n\n## 官方资源\n- 站点：https://www.trae.ai",
     "frontier-model", "product", "https://www.trae.ai", None, "字节跳动", "", "trending", True,
     ["AI IDE", "Agent", "编程"]),
]


def seed(force: bool = False) -> None:
    init_db()
    if count_items() > 0 and not force:
        print("[seed] 已存在数据，跳过（使用 force=True 强制重建）。")
        return

    # 分类
    for slug, name, icon, desc, order in CATEGORIES:
        insert_category(name, slug, icon, desc, order)

    # 条目
    for (title, slug, summary, content, cat_slug, stype, url, stars,
         org, lang, status, featured, tags) in ITEMS:
        cat = get_category_by_slug(cat_slug)
        data = {
            "title": title, "slug": slug, "summary": summary, "content": content,
            "category_id": cat["id"] if cat else None, "source_type": stype,
            "source_url": url, "github_stars": stars, "author_org": org,
            "language": lang, "status": status, "featured": featured,
        }
        insert_item(data, tags)

    print(f"[seed] 完成：{len(CATEGORIES)} 个分类，{len(ITEMS)} 条前沿信息。")


if __name__ == "__main__":
    seed(force=True)

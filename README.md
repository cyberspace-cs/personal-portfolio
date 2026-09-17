# 🏠 Tao Xie · Portfolio

> 个人简历网页 + 项目集散地：这里是 **AI Agent / LLM 工程 / 审计智能化** 方向的实战项目合集。
> 每一个项目都从 0 到 1 亲手实现，不调用 LLM API 也能跑通完整链路。

<div align="center">

![GitHub stars](https://img.shields.io/github/stars/cyberspace-cs/personal-portfolio?style=social)
![GitHub forks](https://img.shields.io/github/forks/cyberspace-cs/personal-portfolio?style=social)
![在线简历](https://img.shields.io/badge/在线简历-Portfolio-8A2BE2)
![Agent](https://img.shields.io/badge/Agent-编排-22d3ee)
![LLM](https://img.shields.io/badge/LLM-工程化-22d3ee)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?logo=react&logoColor=black)
![Vue](https://img.shields.io/badge/Vue-4FC08D?logo=vue.js&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)

</div>

---

## 📌 项目速览

| # | 项目 | 一句话说明 | 状态 |
| --- | --- | --- | --- |
| 1 | [**Audit-AIOPS**](Audit-AIOPS/) | 审计智能一体化运维平台助手：Agent 编排 + 大模型，四大痛点一站式解决 | 🌟 面试亮点 |
| 2 | [**auditscope**](auditscope/) | 「审查查」——对标企查查/天眼查的审计尽调综合信息查询平台 | 🌟 面试亮点 |
| 3 | [**competition-hub**](competition-hub/) | 竞赛雷达：黑客松/Kaggle/CTF/AI 竞赛聚合平台 | ✅ 可运行 |
| 4 | [**cs-frontier-hub**](cs-frontier-hub/) | CS 前沿：Agent/LLM/GPU 算子/顶会知识聚合平台 | ✅ 可运行 |
| 5 | [**shuati-coach**](shuati-coach/) | 刷题教练：岗位调研 → 项目匹配 → 技术提取的 AI 刷题助手 | ✅ 可运行 |
| 6 | [**shuaticoach-trae**](shuaticoach-trae/) | 刷题教练（Trae 版）：Python + 模板渲染的轻量实现 | ✅ 可运行 |
| 7 | [**ai-code-copilot**](projects/ai-code-copilot/) | AI 代码助手：解释 / 审查 / 生成 / 补全四大能力 | ✅ 可运行 |
| 8 | [**llm-finetune-studio**](projects/llm-finetune-studio/) | 大模型微调工作台：PEFT 全流程，无 GPU 可演示 | ✅ 可运行 |
| 9 | [**multimodal-chat-hub**](projects/multimodal-chat-hub/) | 多模态对话机器人：文本 + 视觉 + 语音三模态融合 | ✅ 可运行 |
| 10 | [**rag-knowledge-hub**](projects/rag-knowledge-hub/) | 企业级 RAG 知识问答：混合检索 + 阈值门控防幻觉 | ✅ 可运行 |
| 11 | [**smart-service-desk**](projects/smart-service-desk/) | 智能客服机器人：意图路由 + FAQ 匹配 + 工单系统 | ✅ 可运行 |

---

## 🚀 重点项目

### 1. Audit-AIOPS · 审计智能一体化运维平台

> 面向审计领域的 Agent 编排 + 大模型应用，解决「入口分散、流程黑盒、自动化断点、缺乏 AI 赋能」四大痛点。

- 🧩 **Agent 编排层**：意图识别 → 拆单 → 审批路由 → 记忆系统（ReAct 式编排 + 工具调用）
- 🧠 **大模型可插拔**：腾讯混元 / 阿里通义千问，灵活切换
- 📊 **进度卡片**：节点状态 + 责任人 + 一键联系，工单全程透明
- 🔍 **RAG 知识问答**：对话直达服务单，异常自动发现
- 📁 面试亮点：覆盖「十类审计支持 + 三类运维」业务场景

### 2. auditscope · 审计综合信息查询工具（审查查）

> 对标企查查、天眼查的审计/尽调综合信息查询平台，把「查老板 / 查人员 / 查公司 / 查流水 / 查社保」整合到一个搜索框。

- 🎯 **目标用户**：审计师、尽调人员、合规与风控
- 🧠 **智能能力**：LLM 查询理解 + RAG 证据问答 + 向量检索
- 🎨 **设计系统**：深色玻璃拟态卡片 + 审计蓝青主色，专业数据工作台

### 3. cs-frontier-hub · CS 前沿知识聚合平台

> 聚合 GitHub 高星项目、前沿论文/文档、开源笔记与前沿产品，覆盖 GPU 算子、Triton、推理引擎、Agent 框架、MCP、RAG、RL 与顶会。

- 🗺️ **动态技术架构地图**：交互式 SVG 分层图，点击节点按方向筛选
- 🤖 **公开源爬虫**：自动聚合 GitHub / Gitee / HF Papers / arXiv / CSDN / Semantic Scholar
- 🎨 蓝白酷炫 HUD 风格：深蓝黑底 + 霓虹强调 + 科技网格

### 4. competition-hub · 技术竞赛聚合平台

> 聚合黑客松 / Kaggle / 算法大赛 / CTF / AI 大模型 / 创新创业等全球技术竞赛。

- 🔌 **自动聚合**：内置可插拔数据源适配器，自动搜寻入库赛事
- 🔍 多维筛选：分类 / 状态 / 形式组合筛选 + 模糊搜索 + 多种排序
- 👤 用户认证 + 收藏 + 赛事 CRUD

### 5. shuati-coach · 刷题教练

> 面向求职的 AI 刷题辅导，从岗位调研、项目岗位匹配到技术提取的系统方法论 + Agent 升级设计。

- 📋 三步法：岗位调研 → 项目匹配 → 技术提取
- 🤖 Agent 升级设计文档（docs/）
- 🖥️ 含 agent.html / coach.html 双页面 + miniprogram 小程序端 + server 后端

---

## 💼 五大可落地 AI 应用（projects/）

| 项目 | 核心能力 | 技术要点 |
| --- | --- | --- |
| [**AI Code Copilot**](projects/ai-code-copilot/) | 代码解释 / 审查 / 生成 / 补全 | AST 静态分析 + 圈复杂度 + lint 规则引擎 |
| [**LLM Finetune Studio**](projects/llm-finetune-studio/) | 数据集校验 / 超参配置 / 训练调度 / 对比推理 | LoRA/QLoRA/DoRA，Canvas 实时曲线 |
| [**Multimodal Chat Hub**](projects/multimodal-chat-hub/) | 文本 / 视觉 / 语音三模态对话 | 情感词典 + 视觉特征映射 + Web Speech API |
| [**RAG Knowledge Hub**](projects/rag-knowledge-hub/) | 企业级检索增强问答 | 纯 Python 实现 TF-IDF ⊕ BM25 混合检索 |
| [**Smart Service Desk**](projects/smart-service-desk/) | 智能客服 + 工单系统 | 六类意图路由 + 置信度门控转人工 |

> 💡 这五个项目全部**无需 API Key / GPU / 向量数据库**即可本地运行演示，前后端分离，蓝白科技感统一风格。

---

## 🛠️ 技术栈

| 层 | 技术 |
| --- | --- |
| 后端 | Python · FastAPI · SQLite · Agent 编排 |
| 前端 | React · Vue 3 · TypeScript · Tailwind CSS · 原生 HTML |
| AI | LLM 多厂商接入（混元 / 通义 / DeepSeek）· RAG · Agent · 微调 |
| 部署 | Docker · GitHub Pages · Vercel |

---

## 🧠 学习资料

| 文档 | 说明 |
| --- | --- |
| [AGENT_LLM_MAPPING.md](AGENT_LLM_MAPPING.md) | Agent 与 LLM 映射关系学习：架构、调用链路、提示工程 |
| [LEARNING_PATH.md](LEARNING_PATH.md) | 学习路径规划 |
| [docs/](docs/) | 刷题教练 AI 优化提示词库等 |

---

## 📈 GitHub 统计

<div align="center">

![Tao Xie's GitHub stats](https://github-readme-stats.vercel.app/api?username=cyberspace-cs&show_icons=true&theme=vue)

</div>

---

## 📄 关于

- 👋 你好，我是 **Tao Xie（buleboy）**
- 🎯 方向：AI Agent 应用开发、LLM 工程化、审计智能化
- ✨ 欢迎 Star ⭐，也欢迎交流合作

<div align="center">

**Build it. Break it. Fix it. Learn it.** 🚀

</div>

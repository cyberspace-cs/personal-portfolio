# 面试题库 · Agent 算法与推理优化（量化/蒸馏/KV cache/框架）

> 覆盖：模型压缩与量化 / 知识蒸馏 / KV cache 与注意力 / 推理框架与吞吐 / Agent 降本 / 项目深挖。
> 每题给「考察点 + 回答要点 + 项目锚定」，锚定《专属刷题教练》真实实现。

---

## 一、模型压缩与量化

**Q1. 模型量化 INT8/INT4 怎么做的？GPTQ 和 AWQ 区别？**
- 考察：量化原理与选型。
- 要点：① 线性层权重/激活从 FP16 映射到 INT，减显存增吞吐；② GPTQ 是 post-training 二阶信息补偿、按列顺序量化；AWQ 是激活感知、保护重要权重（salient weights）少量化；③ INT4 显存≈FP16 的 1/4。
- 项目锚定：刷题教练基座预留混元/通义 + AWQ 4bit 私有化，用评测闭环看是否掉点。

**Q2. 量化后怎么保证不掉点？**
- 考察：质量验证。
- 要点：用固定评测集对比量化前后指标（困惑度/任务准确率）；垂域要自建评测。
- 项目锚定：`run_self_eval` 同时评 teacher/student，看 `hit_rate/citation_rate/hallucination_rate`，量化模型也过同一闸门。

**Q3. 量化对 Agent 的取舍？**
- 考察：工程权衡。
- 要点：边缘/高并发用 INT4 降本，关键链路（讲题准确性）可留 FP16；分层——轻量任务量化、重任务全精度。

---

## 二、知识蒸馏

**Q4. 什么是知识蒸馏？soft label 比 hard label 好在哪？**
- 考察：KD 原理。
- 要点：teacher(大模型)输出软标签(概率分布)含类间关系信息，student 学分布比学 one-hot 泛化好；温度 τ 软化分布。

**Q5. 怎么把 KD 用到 Agent？**
- 考察：应用迁移。
- 要点：teacher 生成讲题/变式/诊断作训练集 → student 小模型做轻量/边缘答疑；仍可保留工具调用与 RAG 引用。
- 项目锚定：刷题教练可让大模型(teacher)产出讲题样本，蒸馏小模型(student)做离线答疑，评测闭环同时评两者。

**Q6. 蒸馏和微调怎么选？**
- 考察：训练策略。
- 要点：有 teacher 且要小模型用 KD；无 teacher 或任务窄用 SFT；可 KD+SFT 结合。

---

## 三、KV cache 与注意力优化

**Q7. 什么是 KV cache？为什么能加速？**
- 考察：自回归推理基础。
- 要点：缓存每层的 Key/Value，避免每 token 重算历史；decode 阶段只算新 token 的 Q 与缓存 K/V 做注意力。显存随序列增长。

**Q8. KV cache 的显存怎么算？怎么优化？**
- 考察：显存估算。
- 要点：≈ 2 × layers × hidden × seq_len × batch × dtype_bytes（K、V 各一份）；优化：PagedAttention(分页避免碎片)、MQA/GQA(共享 KV 降头数)、量化 KV(Int8)、prefix caching(复用公共前缀)。
- 项目锚定：五段式上下文预算里【身份】【长期画像】是稳定前缀 → prefix caching 复用，多轮对话省重算。

**Q9. MQA/GQA 是什么，为什么推理快？**
- 考察：注意力结构。
- 要点：MQA 所有 head 共享一组 KV，GQA 分组共享；显存与算力随 KV 头数下降而降，吞吐升。

**Q10. FlashAttention 解决什么？**
- 考察：IO 感知。
- 要点：把 QK^T、softmax、PV 融合到 SRAM，避免将大 N×N 注意力矩阵写回 HBM，降显存与带宽瓶颈，长上下文更明显。

---

## 四、推理框架与吞吐

**Q11. vLLM 的 PagedAttention 解决了什么？**
- 考察：主流框架。
- 要点：把 KV cache 像虚拟内存分页，按需分配、消除碎片、支持抢占，显存利用率高，并发强。

**Q12. continuous batching 为什么比静态 batch 好？**
- 考察：调度。
- 要点：静态 batch 等最长序列，短请求空等；continuous batching 来一个进一个、完成即出，GPU 利用率高、首字/吞吐双优。
- 项目锚定：刷题教练多用户并发答疑上 vLLM continuous batching 提吞吐；反思节点确定性不额外 decode，省调度。

**Q13. SGLang 的结构化生成有什么用？**
- 考察：Agent 场景。
- 要点：constrained decoding 控 JSON/函数调用格式，减少解析失败与重试；radix cache 复用公共前缀。

**Q14. 投机解码 speculative decoding 原理？**
- 考察：降延迟。
- 要点：小草稿模型先出 k 个 token，大模型一次并行验证，接受率高则提速；草稿错则回退。降首字/解码延迟不损精度。
- 项目锚定：讲题/变式骨架可用草稿模型先出，target 验证，答疑首字更快。

---

## 五、Agent 降本与上下文

**Q15. Agent 推理成本怎么压？**
- 考察：综合降本。
- 要点：① context 压缩（长记忆→摘要）② 公共前缀 prefix caching ③ 工具替代生成 ④ 量化/蒸馏小模型 ⑤ 确定性节点不调 LLM ⑥ 路由分级（简单意图不进大模型）。
- 项目锚定：五段式预算(context 压缩) + 稳定前缀(KV 复用) + 诊断/错题走工具(0 生成) + 反思确定性(0 decode)。

**Q16. 长上下文怎么处理最省？**
- 考察：上下文工程。
- 要点：分层（长期结构化摘要 + 短期滑窗）、RAG 替代全量塞入、预算截断（当前消息优先）、压缩器(LLMLingua)。
- 项目锚定：本项目五段式预算，每段限额、当前用户消息永不被裁。

**Q17. prompt compression 怎么落地？**
- 考察：前沿。
- 要点：LLMLingua 类用小模型挑重要 token 压缩；或把历史压成结构化摘要再注入。保任务指标前提下降 token。
- 项目锚定：【对话历史】段可接压缩器进一步降本，且评测闭环验证不掉点。

---

## 六、项目深挖（把上面串回刷题教练）

**Q18. 你的 Agent 哪里体现了推理优化意识？**
- 答：四个点——context 压缩(五段式预算)、KV 复用(稳定前缀 prefix cache)、工具替代生成(诊断/错题 0 token)、反思确定性(0 额外 decode)；并有评测闭环做量化/蒸馏的质量闸门。

**Q19. 如果要私有化部署降本，你怎么做？**
- 答：混元/通义开源权重 + vLLM 私有化 + AWQ 4bit 量化 + continuous batching 提吞吐；边缘答疑用蒸馏小模型；评测闭环对照 teacher/student 验证不掉点。

**Q20. 多用户并发答疑，你的服务怎么撑？**
- 答：上 vLLM continuous batching；前缀缓存复用公共系统提示与用户画像；反思确定性不占 decode；静态资源与 API 分离（nginx 反代）。

**Q21. 你做过哪些「不调大模型也能完成」的设计？**
- 答：① 反思节点确定性校验 ② RAG 相关性用 2-gram 关键词判据（不靠 LLM）③ 诊断/错题/掌握度走工具返回 ④ RRF 重排用 TF-IDF 不调大模型 —— 都是降本且更可控。

**Q22. 蒸馏/量化后你怎么证明 Agent 没变傻？**
- 答：`agent_eval_log` 留每次 RAG 调用，`run_self_eval` 跑固定样本聚合 hit_rate/citation_rate/hallucination_rate，teacher/student 同闸门对比，grade 不降级即放行。

**Q23. KV cache 和你的分层记忆什么关系？**
- 答：分层记忆（长期画像/短期滑窗）从「语义」上减少重复上下文，直接降低进入 KV cache 的 token 量；稳定前缀（身份+画像）再从「缓存」上复用，双管降本。

**Q24. 如果让你给这个 Agent 做推理侧的 OKR？**
- 答：① 私有化量化后单请求显存降 50%+ ② 并发吞吐(continuous batching)提升 3× ③ 首字延迟(投机解码)降 40% ④ 蒸馏小模型覆盖 60% 边缘答疑且评测不掉点。

---

## 七、反向提问面试官
- 「团队推理侧用 vLLM 还是自研？量化/蒸馏有统一基建吗？」
- 「Agent 服务的并发与首字延迟指标怎么定的？」
- 「垂域蒸馏的训练数据是怎么造的？」

---

## 八、方法论 killer 题（把学界 Trending 方法论沉淀为标准流程）

> 这组题用来展示「不仅会写功能，还能定标准、做复用」，是和普通候选人的差异化点。

**Q25. 你做 Agent 有什么自己的方法论？还是跟着感觉堆功能？**
- 考察：是否有可复用的工程哲学，而非一次性实现。
- 答：我吸收港大黄超教授 HKUDS 团队（nanobot 45.9k⭐ 等）的方法论，沉淀出 5 条标准流程：① Agent=Model+Harness 做薄（基座可插拔，复杂度放编排/工具）② ReAct 本质循环 ③ Channel 与思考解耦（一核多源）④ 经验沉淀成技能/data flywheel ⑤ 成本自负盈亏（token 经济学）。每条都对应我代码里的具体模块，不是口号。
- 项目锚定：Phase G 多厂商注册表=①；六节点 StateGraph=②；Phase H channel.py=③；三层记忆+MCP=④；inference.py 7 项优化=⑤。

**Q26. 你研究过 nanobot / LightRAG 这类 Trending 项目，是照搬吗？**
- 考察：辨别"借鉴范式"与"套壳"的能力。
- 答：只借鉴范式，不搬代码。比如 nanobot 的 Channel 解耦与 HISTORY.md 三层记忆，我在刷题教练里**独立实现**了零依赖的 `channel.py` 和 append-only 可 grep 的 `agent_history`；MCP 我也写了不依赖第三方 SDK 的声明式桥。范式是他人的，实现是我的、可跑的、有评测的。

**Q27. 你怎么证明这套方法论不是只服务于一个项目？**
- 考察：方法论的通用性 / 复用能力。
- 答：同一套"一核多域"骨架被团队两个 Trending 项目（Vibe-Trading 量化 / Deep Tutor 教育）复用——只换垂直 Skills+Memory+MCP 工具，Agent core 不动。说明沉淀的是跨项目的标准，不是某个项目的临时方案。

**Q28. 如果要你从 0 接手一个新垂直域（比如金融投研 Agent），你怎么起步？**
- 考察：方法论的可执行性（行为面试）。
- 答：按我的标准流程——① 定 Harness 骨架（编排/工具网关/记忆/评测先搭好，基座先可插拔占位）② 用 ReAct 六节点打通最小闭环 ③ Channel 接入层隔离来源 ④ 垂直能力以 MCP/skill 插件注入 ⑤ 上推理优化 + 评测闭环控成本与质量。核心不重写，只填垂直内容，几天可出 MVP。

**Q29. 你说"成本自负盈亏"，具体怎么落到 Agent 设计里？**
- 考察：成本意识是否虚。
- 答：四个实招——① 稳定前缀 prefix cache 复用系统提示/画像 ② 该查库不生成（诊断/错题走工具 0 token）③ 反思节点确定性 0 decode ④ 评测闭环量化每次调用的 hit/citation/reject/hallucination 率，质量闸门卡住降本导致的掉点。本项目实测 kv_cache_hit_rate≈0.8、speedup≈8x。

**Q30. 你认可的 Agent 设计原则里，哪条最反常识但最有价值？**
- 考察：是否有独立判断。
- 答：「把 Agent 做薄」。多数人会堆 prompt、堆模型能力，但 HKUDS 和我的实践都证明——**复杂度应放在 harness（编排/工具/环境），Agent 本身越薄越稳、越可迁移**。这直接决定了我项目能复用到两个 Trending 产品。

**Q31.（反向）如果面试官质疑"你这些方法论是不是包装？"**
- 答：用代码反证——打开 `agent/channel.py`（解耦）、`agent/memory.py` 六段式（分层）、`agent/mcp.py`（插件化）、`inference.py`（降本指标），每条方法论都能指到具体文件与实测数字；并可现场 `python run_agent_cli.py` 无 Key 跑通证明工程扎实。

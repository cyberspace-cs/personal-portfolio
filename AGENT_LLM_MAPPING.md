# Agent 与 LLM 映射关系学习文档

> 本文档梳理 Audit-AIOPS 与刷题教练两个项目中 Agent 组件与 LLM 的调用关系、提示工程模式、推理优化策略，帮助理解企业级 Agent 应用中 LLM 的角色定位与工程实践。

---

## 一、整体架构：Agent → LLM 调用链路

### 1.1 双层 Agent 架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    用户层（对话入口）                             │
│  自然语言输入 → AgentHub / ApiChannel → AgentOrchestrator        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    编排层（状态机 / 图）                           │
│  IntentClassifier → Planner → Router → Executor → Reflector     │
│       ↓                ↓           ↓          ↓         ↓       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    LLM 抽象层（统一调用）                          │
│  LLMClient / call_llm → Provider Switch → Cache → API Call      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    模型层（多厂商兼容）                           │
│  智谱 / Kimi / 混元 / 豆包 / 千问 / DeepSeek / OpenAI            │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 调用层级表

| 层级 | 组件 | 文件 | 职责 |
|------|------|------|------|
| **用户层** | AgentHub / ApiChannel | `shuati-coach/server/agent/channel.py` | 多渠道接入分发 |
| **编排层** | AgentOrchestrator / CoachAgent | `app/agent/orchestrator.py` / `shuati-coach/server/agent/orchestrator.py` | ReAct 式 / StateGraph 编排 |
| **技能层** | SkillRegistry / CoachTools | `app/skills/registry.py` / `shuati-coach/server/agent/tools.py` | 能力注册与工具封装 |
| **LLM 抽象层** | LLMClient / call_llm | `app/llm/client.py` / `shuati-coach/server/agent/llm.py` | 统一调用接口 |
| **优化层** | LLMCache / optimized_call_llm | `app/llm/cache.py` / `shuati-coach/server/agent/inference.py` | 缓存、压缩、投机解码 |
| **协议层** | OpenAI 兼容 API | 各厂商 SDK | `/chat/completions` |

---

## 二、Agent 组件与 LLM 映射详解

### 2.1 Audit-AIOPS Agent 编排映射

**AgentOrchestrator** → [orchestrator.py](file:///data/usershare/project/TxBuddy/personal-portfolio/Audit-AIOPS/app/agent/orchestrator.py)

```python
class AgentOrchestrator:
    def __init__(self, llm: LLMClient):
        self.llm = llm  # LLM 客户端注入

    def handle(self, message, session_id):
        # ① 技能解析（无需 LLM）
        skills = resolve_skills(message)
        
        # ② 意图识别 → LLM 映射
        intents = self.llm.classify_intent(message, CATALOG)
        
        # ③ 规划/拆单（规则 + LLM）
        wo = create_work_order(items)
        
        # ④ 问答类 → LLM 映射
        ans = self.llm.answer(message)
```

**LLM 调用映射表**：

| Agent 节点 | LLM 方法 | 系统提示 | 温度 | 用途 |
|-----------|---------|---------|------|------|
| 意图识别 | `classify_intent()` | "你是审计运维平台的意图识别器" | 0.3 | 自然语言 → 服务项 ID |
| 知识问答 | `answer()` | "你是审计运维平台的知识助手" | 0.3 | RAG 检索后生成 |
| 审批路由 | `classify_intent()` | 同上 | 0.3 | 识别审批意图 |

### 2.2 刷题教练 Agent 编排映射

**CoachAgent（LangGraph 同构）** → [orchestrator.py](file:///data/usershare/project/TxBuddy/personal-portfolio/shuati-coach/server/agent/orchestrator.py)

```python
# StateGraph 节点与 LLM 映射
g.add_node("classify", self._n_classify)      # Supervisor: 意图分类
g.add_node("diagnose", self._n_diagnose)      # 规则工具（0 token）
g.add_node("wrongbook", self._n_wrongbook)    # 规则工具（0 token）
g.add_node("plan", self._n_plan)              # LLM: 生成学习计划
g.add_node("rag_qa", self._n_rag_qa)          # LLM: RAG 问答
g.add_node("reflect", self._n_reflect)        # 规则: 反思建议
```

**StateGraph 节点与 LLM 映射表**：

| 节点 | 方法 | 是否调用 LLM | 系统提示 | 用途 |
|------|------|-------------|---------|------|
| `classify` | `_n_classify()` | ✅ | "你是意图分类器" | 分类 diagnose/wrongbook/plan/chat |
| `diagnose` | `_n_diagnose()` | ❌ | — | SQL 聚合计算薄弱度 |
| `wrongbook` | `_n_wrongbook()` | ❌ | — | SQL 查询高频错题 |
| `plan` | `_n_plan()` | ✅ | "你是备考规划师" | 生成冲刺计划 JSON |
| `rag_qa` | `_n_rag_qa()` | ✅ | "你是专属刷题教练" | 基于检索知识回答 |
| `reflect` | `_n_reflect()` | ❌ | — | 规则生成跟进建议 |

### 2.3 意图分类映射（Supervisor 模式）

**核心逻辑** → [orchestrator.py](file:///data/usershare/project/TxBuddy/personal-portfolio/shuati-coach/server/agent/orchestrator.py#L29-L46)

```python
async def _classify(self, message: str, ctx_summary: str) -> str:
    # 规则兜底（无 Key 时）
    if not HAS_KEY:
        if any(k in m for k in ["薄弱", "弱项", "掌握度"]):
            return "diagnose"
        if any(k in m for k in ["错题", "错在哪"]):
            return "wrongbook"
        # ... 其他规则
    
    # LLM 意图分类（有 Key 时）
    sys = ("你是意图分类器。可选意图：diagnose, wrongbook, plan, chat。"
           "只输出 JSON {intent: 其一}。")
    text = await optimized_call_llm(sys, 
        "用户学习概况：" + ctx_summary + "\n用户说：" + message, 
        200, json_mode=True)
    return json.loads(text).get("intent", "chat")
```

**意图触发词与路由映射**：

| 意图 | 触发关键词 | 路由目标 | 是否需要 LLM |
|------|-----------|---------|-------------|
| `diagnose` | 薄弱、弱项、掌握度、哪里差、不会 | DiagnoseAgent | ❌ 规则 |
| `wrongbook` | 错题、错在哪、易错 | WrongBookAgent | ❌ 规则 |
| `plan` | 计划、怎么学、安排、冲刺、押题 | PlanAgent | ✅ LLM |
| `chat` | 默认（其他） | RAG_QAAgent | ✅ LLM |

---

## 三、LLM 客户端抽象层

### 3.1 Audit-AIOPS LLMClient

**核心设计** → [client.py](file:///data/usershare/project/TxBuddy/personal-portfolio/Audit-AIOPS/app/llm/client.py)

```python
class LLMClient:
    def __init__(self):
        self.provider = settings.llm_provider  # mock / hunyuan / qwen
    
    def _chat(self, system, user, temperature=0.3) -> str:
        # ① 缓存命中检查
        cached = llm_cache.get(self.provider, system, user)
        if cached:
            return cached
        
        # ② 真实模型调用（OpenAI 兼容）
        resp = httpx.post(f"{base}/chat/completions", ...)
        text = resp.json()["choices"][0]["message"]["content"]
        
        # ③ 缓存回写
        llm_cache.put(self.provider, system, user, text)
        return text
```

**Mock 模式**（无 Key 时自动降级）：

```python
def classify_intent(self, message, catalog):
    if self.provider != "mock":
        # LLM 意图识别
        out = self._chat(sys_p, f"服务目录:\n{ids}\n\n用户诉求: {message}")
        return json.loads(...)
    
    # Mock：关键词匹配
    msg = message.lower()
    for item in catalog:
        for kw in self._kw(item):
            if kw.lower() in msg:
                matched.append(item.id)
    return matched
```

### 3.2 刷题教练多厂商 LLM 客户端

**厂商注册表** → [llm.py](file:///data/usershare/project/TxBuddy/personal-portfolio/shuati-coach/server/agent/llm.py#L33-L84)

```python
PROVIDERS = {
    "zhipu": {
        "label": "智谱 GLM",
        "api_base": "https://open.bigmodel.cn/api/paas/v4",
        "key_envs": ["ZHIPU_API_KEY", "GLM_API_KEY"],
        "default_model": "glm-4.6",
        "supports_json": True,
    },
    "moonshot": {
        "label": "Kimi (Moonshot)",
        "api_base": "https://api.moonshot.cn/v1",
        "key_envs": ["MOONSHOT_API_KEY", "KIMI_API_KEY"],
        "default_model": "kimi-k2-0905-preview",
        "supports_json": True,
    },
    # ... 其他厂商
}
```

**运行期切换机制**：

```python
def switch_provider(name: str) -> dict:
    """运行期切换激活厂商（需该厂商已配置 Key）"""
    cfg = _resolve_provider(name)
    if not cfg["api_key"]:
        raise ValueError(f"厂商 {name} 未配置 Key")
    _ACTIVE = cfg
    LLM_CONFIG = {"API_BASE": cfg["api_base"], ...}
    HAS_KEY = True
    ACTIVE_PROVIDER = cfg["name"]
```

**厂商选择优先级**：

| 优先级 | 条件 | 说明 |
|--------|------|------|
| 1 | `LLM_PROVIDER` 环境变量指定 | 显式选择 |
| 2 | 自动选第一个配置了 Key 的厂商 | 自动适配 |
| 3 | `API_KEY` / `API_BASE` 历史变量 | 自定义网关兜底 |
| 4 | 无 Key 降级 | 规则模式 |

---

## 四、提示工程模式

### 4.1 标准化提示结构

**统一模板**：

```python
def _chat(system: str, user: str, temperature: float = 0.3) -> str:
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
```

**提示工程原则**：

| 原则 | 示例 | 说明 |
|------|------|------|
| **角色设定** | "你是审计运维平台的意图识别器" | 明确 LLM 身份 |
| **输出约束** | "只返回 JSON 数组，例如 [\"ukey\",\"mail\"]" | 限定输出格式 |
| **上下文注入** | "用户学习概况：{ctx_summary}" | 提供相关背景 |
| **知识边界** | "不编造未提供的数据，不确定时诚实说明" | 防止幻觉 |

### 4.2 五段式上下文预算

**刷题教练 MemoryStore** → [memory.py](file:///data/usershare/project/TxBuddy/personal-portfolio/shuati-coach/server/agent/memory.py)

```
[身份] 你是在线备考教练，擅长结合用户错题给出精准讲题与复习建议。
[长期画像] 备考方向：考研数学，薄弱模块：概率统计，最近活跃：3天前
[诊断摘要] 上次诊断：薄弱项为期望方差、条件概率、假设检验
[对话历史] 用户：概率密度函数怎么求？
           教练：概率密度函数 f(x) = dF(x)/dx，需要掌握...
[当前] 用户：大数定律和中心极限定理的区别是什么？
```

**上下文压缩策略** → [inference.py](file:///data/usershare/project/TxBuddy/personal-portfolio/shuati-coach/server/agent/inference.py#L133-L162)

```python
def compress_context(text: str, max_tokens: int = 400) -> str:
    """TF-IDF 抽取式压缩：保留高权重句子"""
    sents = re.split(r"(?<=[。！？\n])", text)
    docs = [{"content": s, "id": i} for i, s in enumerate(sents)]
    idx = TfidfIndex().fit(docs)
    hits = idx.search(" ".join(sents), top_k=len(sents))
    # 取分最高的句子，直到接近 token 预算
```

### 4.3 RAG 提示模式

**检索增强生成** → [tools.py](file:///data/usershare/project/TxBuddy/personal-portfolio/shuati-coach/server/agent/tools.py#L104-L143)

```python
async def rag_qa(self, message: str, context: str, user_id=None) -> dict:
    # ① 检索
    res = self.retriever.search(message, top_k=5, user_id=user_id)
    hits = res["hits"]
    
    # ② 防幻觉：低相关拒答
    if not res["relevant"]:
        return {"reply": "抱歉，未找到足够相关资料..."}
    
    # ③ 构建 RAG 提示
    sys = ("你是专属刷题教练。基于检索到的知识点回答，标注引用编号 [n]；"
           "若引用不足以回答，明确说明，不要编造。")
    knowledge = "\n\n".join(
        f"[{i+1}] {h['title']}\n{h['content']}" for i, h in enumerate(hits)
    )
    user = f"【检索到的参考知识】\n{knowledge}\n\n用户问题：{message}"
    
    # ④ LLM 生成
    text = await optimized_call_llm(sys, user, 800)
```

**RAG 提示结构**：

```
【系统提示】
你是专属刷题教练。基于检索到的知识点回答，标注引用编号 [n]；
若引用不足以回答，明确说明，不要编造。

【检索到的参考知识】
[1] 大数定律
    大数定律指出，当试验次数足够多时，随机事件的频率趋近于其概率...
[2] 中心极限定理
    中心极限定理表明，大量独立同分布的随机变量之和近似服从正态分布...

【用户问题】
大数定律和中心极限定理的区别是什么？
```

---

## 五、推理优化层

### 5.1 优化技术栈总览

**7 项优化** → [inference.py](file:///data/usershare/project/TxBuddy/personal-portfolio/shuati-coach/server/agent/inference.py)

| 优化项 | 实现类/函数 | 原理 | 可观测指标 |
|--------|-----------|------|-----------|
| ① KV 前缀缓存 | `KVCacheManager` | 稳定前缀复用 | `kv_cache_hit_rate` |
| ② 上下文压缩 | `compress_context()` | TF-IDF 抽取摘要 | `compressed_saved_tokens` |
| ③ 投机解码 | `speculative_decode()` | 草稿+目标拒绝采样 | `spec_accept_rate` |
| ④ 知识蒸馏 | `Distiller` | Teacher→Student | `rouge2` 相似度 |
| ⑤ 连续批处理 | `InferenceBatcher` | asyncio.gather 合并 | `batch_merged_requests` |
| ⑥ 工具替代生成 | `mark_tool_substitution()` | 0 token 工具命中 | `tool_substitutions` |
| ⑦ 量化/AWQ | `QUANT_CONFIG` | 4bit 量化 | `quant_mode` |

### 5.2 组合缓存机制

**PromptCache + SemanticCache** → [cache.py](file:///data/usershare/project/TxBuddy/personal-portfolio/Audit-AIOPS/app/llm/cache.py)

```python
class LLMCache:
    def __init__(self):
        self.prompt = PromptCache()      # 精确命中（归一化哈希）
        self.semantic = SemanticCache()  # 语义命中（cos 相似度）
    
    def get(self, provider, system, user):
        # ① 先查精确缓存
        exact = self.prompt.get(provider, system, user)
        if exact:
            return exact
        # ② 再查语义缓存
        return self.semantic.get(user)
    
    def put(self, provider, system, user, text):
        self.prompt.put(provider, system, user, text)
        self.semantic.put(user, text)
```

**缓存命中率计算**：

```python
def stats(self):
    total = self.prompt.stats["hits"] + self.prompt.stats["misses"]
    return {
        "hit_rate": round(self.prompt.stats["hits"] / total, 4) if total else 0.0,
        "semantic_hits": self.semantic.stats["hits"],
        "saved_ms_total": self.saved_ms_total,
    }
```

### 5.3 优化版 LLM 调用入口

**optimized_call_llm** → [inference.py](file:///data/usershare/project/TxBuddy/personal-portfolio/shuati-coach/server/agent/inference.py#L355-L368)

```python
async def optimized_call_llm(system, user, max_tokens=800, 
                             json_mode=False, compress=True) -> str:
    # ① 超长上下文自动压缩
    if compress and token_estimate(user) > 500:
        user = compress_context(user, max_tokens=400)
    
    # ② KV 前缀缓存测算
    prefix = KVCacheManager().stable_prefix(system, "", "")
    KVCacheManager().account(prefix)
    
    # ③ 累计 token 统计
    LEDGER.prompt_tokens_total += token_estimate(system + user)
    
    # ④ 调用底层 LLM
    return await call_llm(system, user, max_tokens, json_mode)
```

---

## 六、MCP 与工具调用

### 6.1 MCP 桥接模式

**声明式 MCP Bridge** → [mcp.py](file:///data/usershare/project/TxBuddy/personal-portfolio/shuati-coach/server/agent/mcp.py)

```python
@dataclass
class MCPToolSpec:
    name: str                    # 工具名
    description: str             # 描述（供 LLM 理解）
    input_schema: dict           # JSON Schema
    source: str = "builtin"      # builtin / remote

class MCPBridge:
    def call(self, tool_name: str, arguments: dict) -> dict:
        # ① 内置工具直接调用
        if tool_name in self._builtins:
            spec, func = self._builtins[tool_name]
            return func(**arguments)
        # ② 远程工具走 HTTP JSON-RPC
        return await self._remote_call(remote_url, tool_name, arguments)
```

**内置工具定义**：

```python
self.register_builtin(
    MCPToolSpec(
        "exam_syllabus",
        "按备考分类检索考纲概览（考研 / 考公 / 大厂）。",
        {"type": "object",
         "properties": {"cat": {"type": "string"}}},
        "builtin",
    ),
    self._tool_exam_syllabus,
)
```

### 6.2 虚拟工具范式（Virtual Tools）

**用 Function Calling 约束输出** → [llm.py](file:///data/usershare/project/TxBuddy/personal-portfolio/shuati-coach/server/agent/llm.py#L235-L291)

```python
async def call_llm_tool(system, user, tool_name, tool_schema, ...) -> dict:
    """虚拟工具：用 Function Calling 约束结构化输出"""
    payload = {
        "model": cfg["model"],
        "messages": [...],
        "tools": [{
            "type": "function",
            "function": {
                "name": tool_name,
                "description": "按给定 JSON schema 输出结构化结果",
                "parameters": tool_schema,
            },
        }],
        "tool_choice": {"type": "function", "function": {"name": tool_name}},
    }
    # 截获 tool_calls[0].function.arguments 作为结构化数据
    # 不真正执行工具（幽灵工具技巧）
```

**优势**：
- 比 `response_format=json_object` 更稳定
- 所有 OpenAI 兼容端点统一支持
- 参数有严格 JSON 约束

---

## 七、错误处理与降级机制

### 7.1 无 Key 降级

```python
def classify_intent(self, message, catalog):
    if self.provider != "mock":
        out = self._chat(sys_p, ...)
        try:
            return json.loads(...)
        except Exception:
            return []  # LLM 失败降级为空
    
    # 规则兜底
    return keyword_match(message, catalog)
```

### 7.2 防幻觉机制

**RAG 低相关拒答** → [tools.py](file:///data/usershare/project/TxBuddy/personal-portfolio/shuati-coach/server/agent/tools.py#L112-L122)

```python
if not res["relevant"]:
    return {
        "reply": ("抱歉，我在知识点库和你的错题里没找到足够相关的资料，"
                  "无法保证回答准确，先不瞎编啦～"),
        "relevant": False,
        "citations": [],
    }
```

### 7.3 异常捕获

```python
async def call_llm(system, user, ...) -> str:
    try:
        resp = await client.post(url, ...)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return ""  # 异常降级为空串，由调用方处理
```

---

## 八、完整调用流程图

### 8.1 刷题教练 Agent 完整链路

```
用户输入："概率统计怎么学？"
         ↓
    AgentHub.dispatch_api()
         ↓
    CoachAgent.handle()
         ↓
    MemoryStore 构建上下文
         ↓
    StateGraph.invoke(state)
         ↓
    ┌──────────────────────────────────────────────────────────┐
    │ ① classify 节点：意图分类                                 │
    │    → optimized_call_llm("你是意图分类器", ...)             │
    │    → 返回 "plan"                                         │
    └──────────────────────────────────────────────────────────┘
         ↓
    ┌──────────────────────────────────────────────────────────┐
    │ ② plan 节点：生成学习计划                                 │
    │    → tools.diagnose(user_id) → SQL 聚合薄弱度              │
    │    → optimized_call_llm("你是备考规划师", ...)             │
    │    → 返回 {focus: [...], plan: [...]}                     │
    └──────────────────────────────────────────────────────────┘
         ↓
    ┌──────────────────────────────────────────────────────────┐
    │ ③ reflect 节点：反思建议                                  │
    │    → 规则生成："记得每天打卡，我会持续跟进..."              │
    └──────────────────────────────────────────────────────────┘
         ↓
    MemoryStore.add_turn() 持久化
         ↓
    返回结果：{intent, reply, cards, source}
```

### 8.2 Audit-AIOPS Agent 完整链路

```
用户输入："申请制作Ukey"
         ↓
    AgentOrchestrator.handle()
         ↓
    ① resolve_skills("申请制作Ukey")
       → ["workorder_decompose", "approval_routing"]
       → needs_approval = True
         ↓
    ② llm.classify_intent("申请制作Ukey", CATALOG)
       → ["ukey"]
         ↓
    ③ create_work_order([ukey_item])
       → 生成工单 WO-xxx，路由审批责任人
         ↓
    ④ 返回 ChatResponse
       → "已识别您的诉求：Ukey制作。AI已自动拆单..."
```

---

## 九、关键设计模式总结

### 9.1 依赖注入模式

```python
class AgentOrchestrator:
    def __init__(self, llm: LLMClient):
        self.llm = llm  # 依赖注入，便于测试与替换
```

### 9.2 策略模式（多厂商切换）

```python
def call_llm(system, user, provider=None):
    cfg = _ACTIVE
    if provider:
        cfg = _resolve_provider(provider)  # 运行期切换策略
    return httpx.post(f"{cfg['api_base']}/chat/completions", ...)
```

### 9.3 模板方法模式（优化层封装）

```python
async def optimized_call_llm(system, user, ...):
    # 固定流程：压缩 → 缓存 → 统计 → 调用
    user = compress_context(user)
    KVCacheManager().account(prefix)
    LEDGER.prompt_tokens_total += ...
    return await call_llm(system, user, ...)
```

### 9.4 状态机模式（LangGraph 同构）

```python
g = StateGraph()
g.add_node("classify", ...)
g.add_node("plan", ...)
g.add_conditional_edges("classify", lambda s: s["intent"], {
    "plan": "plan",
    "chat": "rag_qa",
})
```

---

## 十、学习路径建议

### 阶段一：理解调用链路（1 周）
1. 阅读 [LLMClient](file:///data/usershare/project/TxBuddy/personal-portfolio/Audit-AIOPS/app/llm/client.py) 理解统一调用接口
2. 阅读 [orchestrator.py](file:///data/usershare/project/TxBuddy/personal-portfolio/Audit-AIOPS/app/agent/orchestrator.py) 理解 Agent 编排
3. 理解 **Mock 模式**：无 Key 时如何用规则替代 LLM

### 阶段二：深入提示工程（1-2 周）
1. 分析各 Agent 节点的 **系统提示** 设计
2. 理解 **五段式上下文** 的构建逻辑
3. 掌握 **RAG 提示** 的构建与防幻觉机制

### 阶段三：推理优化实践（2 周）
1. 阅读 [cache.py](file:///data/usershare/project/TxBuddy/personal-portfolio/Audit-AIOPS/app/llm/cache.py) 理解缓存机制
2. 阅读 [inference.py](file:///data/usershare/project/TxBuddy/personal-portfolio/shuati-coach/server/agent/inference.py) 理解 7 项优化
3. 理解 **工具替代生成** 的 0 token 思想

### 阶段四：MCP 与工具集成（1 周）
1. 阅读 [mcp.py](file:///data/usershare/project/TxBuddy/personal-portfolio/shuati-coach/server/agent/mcp.py) 理解声明式桥接
2. 理解 **虚拟工具范式** 的 Function Calling 约束
3. 学习如何扩展新的 MCP 工具

---

## 十一、文件索引速查表

| 模块 | 文件路径 | 核心内容 |
|------|---------|---------|
| LLM 抽象层 | [client.py](file:///data/usershare/project/TxBuddy/personal-portfolio/Audit-AIOPS/app/llm/client.py) | Audit-AIOPS 统一 LLM 调用 |
| 多厂商支持 | [llm.py](file:///data/usershare/project/TxBuddy/personal-portfolio/shuati-coach/server/agent/llm.py) | 7 厂商切换 + 虚拟工具 |
| 推理优化 | [inference.py](file:///data/usershare/project/TxBuddy/personal-portfolio/shuati-coach/server/agent/inference.py) | 7 项优化 + 指标台账 |
| 缓存机制 | [cache.py](file:///data/usershare/project/TxBuddy/personal-portfolio/Audit-AIOPS/app/llm/cache.py) | Prompt/Semantic Cache |
| Audit Agent | [orchestrator.py](file:///data/usershare/project/TxBuddy/personal-portfolio/Audit-AIOPS/app/agent/orchestrator.py) | ReAct 式编排 |
| 刷题 Agent | [orchestrator.py](file:///data/usershare/project/TxBuddy/personal-portfolio/shuati-coach/server/agent/orchestrator.py) | StateGraph 编排 |
| 技能系统 | [registry.py](file:///data/usershare/project/TxBuddy/personal-portfolio/Audit-AIOPS/app/skills/registry.py) | Skill 注册与解析 |
| 工具集 | [tools.py](file:///data/usershare/project/TxBuddy/personal-portfolio/shuati-coach/server/agent/tools.py) | CoachTools + RAG |
| MCP 桥接 | [mcp.py](file:///data/usershare/project/TxBuddy/personal-portfolio/shuati-coach/server/agent/mcp.py) | 声明式 MCP Bridge |

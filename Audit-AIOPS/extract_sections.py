import os, re

base = r"D:\download\project\TX-budddy\personal-portfolio\Audit-AIOPS"

targets = {
    "core_ai-agent-interview-guide-zh.txt": [
        "自动化运维", "Agent 的核心组成", "记忆（Memory）", "ReAct", "LATS",
        "LangChain Agent 实现", "AutoGen / CrewAI", "RAG 基础", "RAG 评估",
        "RAG 生产优化", "MCP 协议（Model Context Protocol）", "工具编排（Tool Orchestration）",
        "Agent 的工作流程", "Agent 的应用场景",
    ],
    "core_2-pico.txt": [
        "架构", "技术栈", "Agent", "多智能体", "编排", "工具", "RAG", "工作流", "方案",
    ],
    "core_DocAI多人AI文档协作平台.txt": [
        "架构", "技术", "Agent", "多智能体", "协作", "编排", "知识库", "RAG", "方案", "流程",
    ],
}

WIN = 1400
for fn, kws in targets.items():
    path = os.path.join(base, fn)
    with open(path, encoding="utf-8") as f:
        text = f.read()
    # 按页切分，保留页标题 + 页内全部命中上下文
    pages = re.split(r"(===== PAGE \d+/\d+ =====)", text)
    out = []
    seen = set()
    for i in range(1, len(pages), 2):
        header = pages[i]
        body = pages[i+1] if i+1 < len(pages) else ""
        for kw in kws:
            for m in re.finditer(re.escape(kw), body):
                s = max(0, m.start()-WIN)
                e = min(len(body), m.end()+WIN)
                chunk = body[s:e].strip()
                key = (kw, chunk[:80])
                if key in seen:
                    continue
                seen.add(key)
                out.append(f"【命中:{kw}】{header}\n{chunk}\n")
    out_path = os.path.join(base, "focus_" + fn.replace("core_", ""))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(out))
    print(f"{fn}: chunks={len(out)}, chars={sum(len(x) for x in out)} -> {out_path}")

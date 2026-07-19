import os, re

base = r"D:\download\project\TX-budddy\personal-portfolio\Audit-AIOPS"
files = [
    "extracted_2-pico.txt",
    "extracted_ai-agent-interview-guide-zh.txt",
    "extracted_DocAI多人AI文档协作平台.txt",
]

# 与本项目对口的 Agent/LLM 关键词（中英/大小写）
keywords = [
    r"Agent", r"智能体", r"orchestrat", r"编排", r"工具调用", r"tool call", r"function call",
    r"\bLLM\b", r"大模型", r"预训练", r"微调", r"\bSFT\b", r"推理", r"inference", r"vLLM", r"量化", r"蒸馏",
    r"\bRAG\b", r"检索增强", r"知识库", r"embedding", r"向量", r"语义检索",
    r"\bMCP\b", r"多智能体", r"multi-agent", r"协作",
    r"记忆", r"memory", r"上下文",
    r"语音", r"\bASR\b", r"识别",
    r"异常检测", r"anomaly", r"监控", r"AIOps", r"根因", r"巡检",
    r"工单", r"审批", r"workflow", r"流程自动化", r"自动化",
]

pat = re.compile("|".join(keywords), re.IGNORECASE)
kwset = [k for k in keywords]

for fn in files:
    path = os.path.join(base, fn)
    with open(path, encoding="utf-8") as f:
        text = f.read()
    # 按页切分，保留页标题
    pages = re.split(r"(===== PAGE \d+/\d+ =====)", text)
    out = []
    hits = 0
    for i in range(1, len(pages), 2):
        header = pages[i]
        body = pages[i+1] if i+1 < len(pages) else ""
        # 段落级命中，避免噪声
        paras = re.split(r"\n{1,}", body)
        kept = [p for p in paras if p.strip() and pat.search(p)]
        if kept:
            hits += 1
            out.append(header)
            out.append("\n".join(kept))
    out_path = os.path.join(base, "core_" + fn.replace("extracted_", "").replace(".txt", ".txt"))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(out))
    print(f"{fn}: matched_pages={hits}, chars={sum(len(x) for x in out)}, -> {out_path}")

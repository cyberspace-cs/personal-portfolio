"""
AI Code Copilot · 后端服务
================================
AI 代码助手后端（FastAPI）。用真实的静态分析 / 启发式规则实现四大能力：
  1) 代码解释：解析结构（函数/类/循环/分支），估算圈复杂度与可读性；
  2) 代码审查：内置多条 lint 规则，检出坏味道并给出修复建议与严重级别；
  3) 代码生成：从模板库按意图生成常见脚手架（API/爬虫/排序/类等）；
  4) 智能补全：基于上下文的规则补全（可无缝替换为真实 LLM 后端）。

无需 API Key，本地即可运行：
    pip install -r requirements.txt
    uvicorn main:app --reload --port 8003
"""
from __future__ import annotations

import ast
import re

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="AI Code Copilot API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

LANGS = ["python", "javascript"]


class CodeReq(BaseModel):
    code: str
    lang: str = "python"


class GenReq(BaseModel):
    prompt: str
    lang: str = "python"


class CompleteReq(BaseModel):
    code: str
    lang: str = "python"


# ----------------------------------------------------------------------------
# 1) 代码解释（Python 走 AST，JS 走正则启发式）
# ----------------------------------------------------------------------------
@app.post("/api/explain")
def explain(req: CodeReq) -> dict:
    code = req.code
    if req.lang == "python":
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {"ok": False, "error": f"语法错误：第 {e.lineno} 行 {e.msg}"}
        funcs, classes, loops, branches, calls = [], [], 0, 0, 0
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                args = [a.arg for a in node.args.args]
                funcs.append({"name": node.name, "args": args, "lineno": node.lineno,
                              "doc": bool(ast.get_docstring(node))})
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, (ast.For, ast.While)):
                loops += 1
            elif isinstance(node, (ast.If, ast.Try)):
                branches += 1
            elif isinstance(node, ast.Call):
                calls += 1
        complexity = 1 + branches + loops
        summary = _py_summary(funcs, classes, loops, branches)
        return {"ok": True, "language": "python",
                "structure": {"functions": funcs, "classes": classes, "loops": loops,
                              "branches": branches, "calls": calls},
                "cyclomatic_complexity": complexity,
                "complexity_level": _level(complexity),
                "lines": len(code.splitlines()),
                "summary": summary,
                "steps": _py_steps(tree)}
    else:
        funcs = re.findall(r"function\s+(\w+)|const\s+(\w+)\s*=\s*\(", code)
        names = [f[0] or f[1] for f in funcs]
        loops = len(re.findall(r"\b(for|while)\b", code))
        branches = len(re.findall(r"\b(if|switch|catch)\b", code))
        complexity = 1 + loops + branches
        return {"ok": True, "language": "javascript",
                "structure": {"functions": [{"name": n} for n in names], "loops": loops, "branches": branches},
                "cyclomatic_complexity": complexity, "complexity_level": _level(complexity),
                "lines": len(code.splitlines()),
                "summary": f"该 JS 代码包含 {len(names)} 个函数、{loops} 个循环、{branches} 个分支。",
                "steps": [f"定义函数 {n}" for n in names[:6]] or ["脚本按顺序执行语句"]}


def _py_summary(funcs, classes, loops, branches):
    parts = []
    if classes:
        parts.append(f"定义了 {len(classes)} 个类（{', '.join(classes)}）")
    if funcs:
        parts.append(f"{len(funcs)} 个函数（{', '.join(f['name'] for f in funcs[:5])}）")
    if loops:
        parts.append(f"{loops} 处循环")
    if branches:
        parts.append(f"{branches} 处条件/异常分支")
    return "这段 Python 代码" + ("；".join(parts) if parts else "为顺序执行的脚本") + "。"


def _py_steps(tree):
    steps = []
    for node in tree.body[:8]:
        if isinstance(node, ast.FunctionDef):
            steps.append(f"定义函数 {node.name}()")
        elif isinstance(node, ast.ClassDef):
            steps.append(f"定义类 {node.name}")
        elif isinstance(node, ast.Assign):
            tgt = node.targets[0]
            name = getattr(tgt, "id", "变量")
            steps.append(f"给 {name} 赋值")
        elif isinstance(node, (ast.For, ast.While)):
            steps.append("执行循环体")
        elif isinstance(node, ast.If):
            steps.append("条件判断分支")
        elif isinstance(node, ast.Expr):
            steps.append("执行表达式（可能是函数调用）")
    return steps or ["顺序执行语句"]


def _level(c):
    return "简单" if c <= 5 else ("中等" if c <= 10 else "偏高，建议拆分")


# ----------------------------------------------------------------------------
# 2) 代码审查（lint 规则）
# ----------------------------------------------------------------------------
RULES_PY = [
    (r"except\s*:", "high", "捕获裸异常 except:", "指定具体异常类型，如 except ValueError:"),
    (r"==\s*None|!=\s*None", "medium", "与 None 用 == 比较", "改用 is None / is not None"),
    (r"print\(", "low", "生产代码中使用 print", "改用 logging 模块记录日志"),
    (r"import\s+\*", "medium", "使用通配符 import *", "显式导入所需名称，避免命名污染"),
    (r"\beval\(", "high", "使用 eval() 存在安全风险", "改用 ast.literal_eval 或明确解析"),
    (r"password\s*=\s*['\"]", "high", "硬编码疑似密码", "改用环境变量 / 配置中心管理密钥"),
]
RULES_JS = [
    (r"\bvar\b", "medium", "使用 var 声明变量", "改用 let / const"),
    (r"==(?!=)|!=(?!=)", "medium", "使用非严格相等 == / !=", "改用 === / !=="),
    (r"console\.log", "low", "遗留 console.log", "移除或改用统一日志"),
    (r"\beval\(", "high", "使用 eval() 存在安全风险", "避免 eval，改用安全解析"),
]


@app.post("/api/review")
def review(req: CodeReq) -> dict:
    lines = req.code.splitlines()
    issues = []
    rules = RULES_PY if req.lang == "python" else RULES_JS
    for i, ln in enumerate(lines, 1):
        for pat, sev, msg, fix in rules:
            if re.search(pat, ln):
                issues.append({"line": i, "severity": sev, "message": msg, "suggestion": fix, "code": ln.strip()[:80]})
        if len(ln) > 100:
            issues.append({"line": i, "severity": "low", "message": f"行过长（{len(ln)} 字符）", "suggestion": "拆分为多行，建议 ≤ 100 字符", "code": ln.strip()[:60] + "…"})
    # Python 额外：无 docstring 的函数
    if req.lang == "python":
        try:
            for node in ast.walk(ast.parse(req.code)):
                if isinstance(node, ast.FunctionDef) and not ast.get_docstring(node):
                    issues.append({"line": node.lineno, "severity": "low",
                                   "message": f"函数 {node.name}() 缺少 docstring",
                                   "suggestion": "补充函数说明文档", "code": f"def {node.name}(...)"})
        except SyntaxError:
            pass
    score = max(0, 100 - sum({"high": 15, "medium": 8, "low": 3}[i["severity"]] for i in issues))
    return {"issues": sorted(issues, key=lambda x: x["line"]),
            "counts": {s: sum(1 for i in issues if i["severity"] == s) for s in ("high", "medium", "low")},
            "score": score, "grade": "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D"}


# ----------------------------------------------------------------------------
# 3) 代码生成（模板库）
# ----------------------------------------------------------------------------
@app.post("/api/generate")
def generate(req: GenReq) -> dict:
    p = req.prompt.lower()
    if any(k in p for k in ["api", "fastapi", "接口", "服务"]):
        code = ('from fastapi import FastAPI\n\napp = FastAPI()\n\n\n@app.get("/api/hello")\n'
                'def hello(name: str = "world"):\n    """示例接口。"""\n    return {"message": f"hello, {name}"}\n')
        note = "生成了一个 FastAPI 接口脚手架"
    elif any(k in p for k in ["爬虫", "爬取", "requests", "抓取", "spider"]):
        code = ('import requests\nfrom bs4 import BeautifulSoup\n\n\n'
                'def fetch(url: str) -> list[str]:\n    """抓取页面所有标题。"""\n'
                '    r = requests.get(url, timeout=10)\n    r.raise_for_status()\n'
                '    soup = BeautifulSoup(r.text, "html.parser")\n'
                '    return [h.get_text(strip=True) for h in soup.select("h1, h2")]\n')
        note = "生成了一个网页抓取脚本"
    elif any(k in p for k in ["排序", "sort", "快排", "quicksort"]):
        code = ('def quicksort(arr: list) -> list:\n    """快速排序（分治）。"""\n'
                '    if len(arr) <= 1:\n        return arr\n    pivot = arr[len(arr) // 2]\n'
                '    left = [x for x in arr if x < pivot]\n    mid = [x for x in arr if x == pivot]\n'
                '    right = [x for x in arr if x > pivot]\n    return quicksort(left) + mid + quicksort(right)\n')
        note = "生成了快速排序实现"
    elif any(k in p for k in ["类", "class", "面向对象"]):
        code = ('class Stack:\n    """基于列表的栈。"""\n\n    def __init__(self):\n        self._data = []\n\n'
                '    def push(self, x):\n        self._data.append(x)\n\n'
                '    def pop(self):\n        return self._data.pop()\n\n'
                '    def is_empty(self) -> bool:\n        return not self._data\n')
        note = "生成了一个栈类"
    else:
        fn = re.sub(r"[^a-z0-9]+", "_", p).strip("_")[:24] or "solution"
        code = (f'def {fn}(data):\n    """根据需求「{req.prompt}」实现的函数骨架。"""\n'
                '    # TODO: 实现核心逻辑\n    result = None\n    return result\n')
        note = "根据描述生成了函数骨架，可继续细化"
    return {"code": code, "note": note, "lang": req.lang}


# ----------------------------------------------------------------------------
# 4) 智能补全（上下文规则）
# ----------------------------------------------------------------------------
@app.post("/api/complete")
def complete(req: CompleteReq) -> dict:
    code = req.code.rstrip()
    last = code.splitlines()[-1] if code.splitlines() else ""
    sug = []
    if req.lang == "python":
        if last.strip().startswith("def ") and last.rstrip().endswith(":"):
            sug.append('    """补全：函数说明。"""\n    pass')
        if re.search(r"for\s+\w+\s+in\s+.+:$", last):
            sug.append("    # 循环体")
        if "import" in last and "requests" in last:
            sug.append("resp = requests.get(url, timeout=10)\nresp.raise_for_status()")
        if last.strip().endswith("try:"):
            sug.append("    pass\nexcept Exception as e:\n    logging.error(e)")
        if not sug:
            sug.append("# 补全建议：为上一行补充实现或返回值")
    else:
        if last.strip().endswith("{"):
            sug.append("  // 代码块")
        if "function" in last:
            sug.append("  return;")
        if not sug:
            sug.append("// 补全建议：补充下一条语句")
    return {"completions": sug}


@app.get("/api/meta")
def meta() -> dict:
    return {"languages": LANGS,
            "capabilities": ["explain", "review", "generate", "complete"],
            "rules": {"python": len(RULES_PY), "javascript": len(RULES_JS)}}


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "ai-code-copilot"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)

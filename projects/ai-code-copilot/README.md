# AI Code Copilot · AI 代码助手

基于真实静态分析的 AI 代码助手，四大能力：**解释 / 审查 / 生成 / 补全**。前后端分离，蓝白科技感统一风格，无需 API Key。

## 功能
- **代码解释**：Python 走 AST 解析结构（函数 / 类 / 循环 / 分支），估算圈复杂度与执行步骤；JS 走正则启发式。
- **代码审查**：内置多条 lint 规则（裸 except、`== None`、`eval`、硬编码密钥、`var`、非严格相等、行过长、缺 docstring…），按严重级别给修复建议与健康分（A/B/C/D）。
- **代码生成**：按意图从模板库生成脚手架（FastAPI 接口 / 爬虫 / 快排 / 类 / 函数骨架）。
- **智能补全**：基于上下文的规则补全，规则层可无缝替换为真实 LLM。

## 技术栈
- 后端：Python + FastAPI + `ast` 抽象语法树静态分析。
- 前端：原生 HTML / CSS / JS，代码编辑器 UI；后端离线时降级为浏览器端启发式分析。

## 运行
```bash
cd backend && pip install -r requirements.txt && uvicorn main:app --reload --port 8003
cd ../frontend && python -m http.server 5503   # 打开 http://localhost:5503
```

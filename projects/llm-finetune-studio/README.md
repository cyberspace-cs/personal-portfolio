# LLM Finetune Studio · 大模型微调工作台

参数高效微调（PEFT）全流程工作台。前后端分离，蓝白科技感统一风格，**无需 GPU / API Key 即可本地运行与演示**。

## 功能
- **数据集校验**：解析 JSONL，统计有效/异常样本、token 分布（均值 / P95 / 训练 token 估算），逐行检出脏数据。
- **超参配置**：基座模型（混元 / 通义 / Llama / GLM）、微调方法（LoRA / QLoRA / Full / DoRA）、rank / alpha / lr / epochs / batch。
- **训练调度**：后台任务调度，warmup + 余弦退火学习率，实时 loss / lr / grad_norm 曲线（自绘 Canvas，无第三方图表库），支持暂停 / 续训。
- **对比推理**：同一 prompt 下基座模型 vs 微调模型输出对比，含延迟 / 吞吐指标。

## 技术栈
- 后端：Python + FastAPI + Pydantic v2 + asyncio 后台任务，接口与 HuggingFace PEFT / Trainer 同构。
- 前端：原生 HTML / CSS / JS，零依赖，Canvas 自绘训练曲线；后端离线时自动降级为本地模拟。

## 运行
```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8001

# 前端（任意静态服务器）
cd ../frontend
python -m http.server 5501
# 浏览器打开 http://localhost:5501
```

## 目录
```
llm-finetune-studio/
├── backend/   FastAPI 服务（main.py + requirements.txt）
└── frontend/  index.html + styles.css + app.js
```

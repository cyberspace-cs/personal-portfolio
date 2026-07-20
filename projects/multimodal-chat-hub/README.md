# Multimodal Chat Hub · 多模态对话机器人

融合**文本 / 视觉 / 语音**三种模态的对话机器人。前后端分离，蓝白科技感统一风格，无需 API Key。

## 功能
- **文本理解**：情感词典分析（含否定词处理）+ 规则意图识别（提问 / 请求 / 问候 / 致谢 / 陈述）。
- **视觉理解**：前端 Canvas 从图片提取真实视觉特征（主色 / 亮度 / 边缘密度 / 宽高比），后端做「特征 → 语义」映射，输出图像描述与标签。
- **语音交互**：浏览器 Web Speech API 实现语音识别（STT）输入与语音合成（TTS）朗读回复。
- **多模态融合**：把文本意图、情感与视觉线索融合成一段自然应答。

## 技术栈
- 后端：Python + FastAPI，情感词典 + 视觉特征语义映射 + 多模态融合。
- 前端：原生 HTML / CSS / JS，Canvas 图像特征提取，Web Speech API；后端离线时降级为浏览器端同构推理。

## 运行
```bash
cd backend && pip install -r requirements.txt && uvicorn main:app --reload --port 8004
cd ../frontend && python -m http.server 5504   # 打开 http://localhost:5504（语音功能建议用 Chrome）
```

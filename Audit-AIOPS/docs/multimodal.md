# 多模态 RAG · 可插拔视觉编码器（RAG-Anything 思路）

> 把「图像 / 表格」统一编码为文本，再进入统一 RAG 检索——这是 HKUDS **RAG-Anything**「any modality → text」的核心思想。
> 本项目把这一「多模态 → 文本」的编码层做成**可插拔**，默认零依赖可复现，配置密钥即接真实多模态大模型。

---

## 1. 为什么是多模态 → 文本

审计文档天然含大量**表格（资产台账 / 权限变更表）**与**截图（Ukey 制作界面 / 审计留痕界面）**。纯文本 RAG 漏掉这些结构化 / 视觉信号。
RAG-Anything 的做法：用多模态大模型（VLM）把任意模态转成文本，再进入统一的文本 RAG。本项目沿用这一路径：

```
截图/表格 (图像字节)
   │  VLM 视觉理解（真实模式） / 预撰写描述（proxy 模式）
   ▼
文本描述（caption）
   │  关键词 + 审计实体 跨模态打分
   ▼
统一 RAG 召回（与文本文档同一套检索）
```

---

## 2. 视觉编码器三态可插拔（`app/services/multimodal_encoder.py`）

| 编码器 | mode | 依赖 | 行为 |
|---|---|---|---|
| `ProxyVisualEncoder` | `proxy` | 无 | 复用 `AUDIT_MULTIMODAL` 预撰写描述（= VLM 预期输出代理），零依赖可复现 |
| `HunyuanVisionEncoder` | `real-hunyuan` | `HUNYUAN_API_KEY` + 真实截图 | 调腾讯混元视觉（`hunyuan-vision`）对截图做视觉理解，产出实时 caption |
| `QwenVisionEncoder` | `real-qwen` | `QWEN_API_KEY` + 真实截图 | 调阿里千问-VL（`qwen-vl-max`）对截图做视觉理解，产出实时 caption |

**env 门控（与 LLM 基座一致的范式）**：
```bash
export VISION_PROVIDER=hunyuan   # 或 qwen / proxy（默认）
export HUNYUAN_API_KEY=xxx        # hunyuan 模式；qwen 模式用 QWEN_API_KEY
export VISION_MODEL=hunyuan-vision   # 可选，覆盖默认视觉模型
```

**优雅降级（诚实可讲）**：无密钥、或 `assets/screenshots/<标题>.png` 缺失、或真实调用失败，一律回退 proxy 并在响应标注 `encoder_mode`，服务不中断。

---

## 3. 接入点

- `MultimodalRetriever`（`app/services/retrieval_hybrid.py`）：每图经 `encode_image(path, cap)` 取描述（proxy=预撰写 / real=VLM 实时），再对描述做跨模态打分；响应项带 `encoder_mode`。
- 端点：
  - `POST /api/knowledge/multimodal` —— 多模态检索，返回 `modalities` / `multimodal_hits` / `encoder_mode`；
  - `GET /api/knowledge/multimodal-encoder-status` —— 当前视觉编码模式、可用 provider、密钥情况。
- 演示页 `/knowledge-hybrid.html` 多模态区块展示 `encoder_mode` 徽标（proxy / real-xxx）。

---

## 4. 真实截图接入

把真实截图放入 `assets/screenshots/`，按 `AUDIT_MULTIMODAL` 文档标题命名（见该目录 `README.md`），配置 `VISION_PROVIDER` + 密钥，重启即激活真·视觉嵌入，**无需改代码**。

---

## 5. 面试讲法（诚实标注）

- 「多模态 RAG 我吸收了 RAG-Anything 的『any modality → text』路径，把图像/表格统一编码成文本再进 RAG。
  视觉编码我做成了可插拔：默认用预撰写描述代理（等价于 VLM 预期输出，保证零依赖可复现），生产上配混元视觉 / 千问-VL + 真实截图就切换成真·视觉嵌入，响应带 encoder_mode 标记，降级也透明。」
- 区分清楚：**多模态 RAG 是检索侧能力**（图 RAG 是另一路，检索侧第三/四路），与算法侧的蒸馏/量化/剪枝不混淆。

# 多模态 RAG · 真实截图资源目录

本目录用于存放审计系统的**真实截图 / 表格图片**，激活 `MultimodalRetriever` 的「真·视觉嵌入」路径
（RAG-Anything 思路：截图 → 多模态大模型 → 文本描述 → 统一 RAG）。

## 文件名约定

按 `app/services/retrieval_hybrid.py` 中 `AUDIT_MULTIMODAL` 的文档标题命名，扩展名 `png/jpg/jpeg/webp` 均可：

- `Ukey 制作、调整与回收.png`   （含 Ukey 制作界面、Ukey 回收登记两张截图）
- `人员角色权限变更.png`        （权限变更审批表）
- `资产自动签收与自动化巡检.png`（资产台账表、巡检结果表）
- `数据安全与审计留痕.png`      （审计留痕界面 + 留痕字段表）
- `审批流自动拆分.png`          （审批流编排截图）
- `工单进度卡片与一键联系.png`  （工单字段表）
- `终端领用与维修.png`          （终端领用登记截图）
- `计算存储资源发放.png`        （资源规格表）

> 一个文档可放多张截图时，建议把描述信息写在文件名之外，直接用截图内容；
> 多张同名不同扩展名不会自动合并，推荐**每文档一张综合截图**或把多图打到一个长图。

## 激活真实视觉编码

1. 配置环境变量（与文本 LLM 同密钥）：
   ```bash
   export VISION_PROVIDER=hunyuan   # 或 qwen
   export HUNYUAN_API_KEY=xxx        # hunyuan 模式
   # export QWEN_API_KEY=xxx        # qwen 模式
   export VISION_MODEL=hunyuan-vision   # 可选，覆盖默认视觉模型
   ```
2. 重启服务：`python -m uvicorn app.main:app --port 8001`
3. 调用 `/api/knowledge/multimodal` 时，命中项 `multimodal_hits[].text` 即真实 VLM 描述，
   顶层 `encoder_mode` 变为 `real-hunyuan` / `real-qwen`。

## 本目录为何默认不含图片？

当前演示环境未配置视觉模型密钥，也无真实产品截图，故**默认走 proxy 模式**
（复用 `AUDIT_MULTIMODAL` 中预先撰写的人工描述，等价于「若把真实截图喂给 VLM 预期会产出的描述」），
保证零依赖、可复现。放入真实截图并配置密钥后，自动切换为真实视觉编码，无需改代码。

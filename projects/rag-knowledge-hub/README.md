# RAG Knowledge Hub · 企业级检索增强问答

企业级 RAG（检索增强生成）知识问答系统。**纯 Python 实现完整检索链路，无需向量数据库 / API Key**，前后端分离，蓝白科技感统一风格。

## 功能
- **文档入库与分块**：按语义句切分 + 贪心合并到目标长度（块间 overlap），自动建索引。
- **混合检索**：TF-IDF 余弦相似度 ⊕ BM25 关键词打分，归一化加权融合（Hybrid Search）。
- **阈值门控**：相关度低于阈值时主动拒答「暂无可靠依据」，从根源抑制幻觉。
- **引用溯源**：每条答案附来源文档、分块、混合分 / 余弦 / BM25 分及置信度，命中词高亮。

## 技术栈
- 后端：Python + FastAPI，纯 Python 实现中英文分词、TF-IDF、BM25、余弦相似度与阈值门控。
- 前端：原生 HTML / CSS / JS，聊天式问答 UI，引用卡片与命中高亮；后端离线时降级为浏览器端同构检索。

## 运行
```bash
cd backend && pip install -r requirements.txt && uvicorn main:app --reload --port 8002
cd ../frontend && python -m http.server 5502   # 打开 http://localhost:5502
```
先点「灌入示例」或自行入库，再提问（如「什么是混合检索？」）。

import urllib.request, json, time

BASE = "http://localhost:8011"

def post(path, data):
    req = urllib.request.Request(BASE+path, data=json.dumps(data).encode(),
        headers={"Content-Type":"application/json"}, method="POST")
    return json.loads(urllib.request.urlopen(req, timeout=30).read())

def get(path):
    return json.loads(urllib.request.urlopen(BASE+path, timeout=30).read())

# 1. finetune
alpaca = json.dumps([{"instruction":"翻译为英文","input":"你好世界","output":"Hello world"},
                     {"instruction":"总结","input":"长文本","output":"摘要"}]*3)
r = post("/api/finetune/ingest", {"content": alpaca, "format":"alpaca"})
print("finetune.ingest:", r["num_samples"], r["dataset_id"])
jid = post("/api/finetune/train", {"base_model":"Qwen2.5-3B-Instruct","method":"LoRA","r":8,"alpha":16,
        "lr":2e-4,"epochs":2,"batch_size":4,"data_ref":r["dataset_id"]})["job_id"]
time.sleep(2)
st = get(f"/api/finetune/train/{jid}")
print("finetune.train: status=", st["status"], "loss_curve_len=", len(st["loss_curve"]))
print("finetune.export:", get(f"/api/finetune/train/{jid}/export")["method"])
print("finetune.deploy vllm:", get(f"/api/finetune/train/{jid}/deploy")["vllm_command"][:40], "...")

# 2. rag
docs = [{"title":"产品手册","text":"我们的平台支持大模型微调和RAG检索。微调使用LoRA方法，显存占用低。RAG支持混合检索与引用溯源。"},
        {"title":"计费说明","text":"按调用量和训练时长计费，新用户有免费额度。"}]
print("rag.ingest:", post("/api/rag/ingest", {"docs":docs}))
ra = post("/api/rag/ask", {"question":"微调用什么方法，显存占用如何？","top_k":2,"use_llm":False})
print("rag.ask answer:", ra["answer"][:60], "| citations=", len(ra["citations"]))

# 3. code
print("code.generate:", post("/api/code/process", {"action":"generate","task":"快速排序","language":"Python"})["result"][:50])
pycode = "def add(a,b):\n    return a+b\nclass Foo:\n    pass"
print("code.refactor:", post("/api/code/process", {"action":"refactor","code":pycode,"language":"Python"})["result"][-40:])
print("code.explain:", post("/api/code/process", {"action":"explain","code":pycode,"language":"Python"})["result"][:50])

# 4. multimodal
print("mm.chat:", post("/api/multimodal/chat", {"message":"你们的产品太棒了，我很满意！","mode":"text"})["emotion"])
print("mm.image:", post("/api/multimodal/analyze-image", {"caption":"办公室里有一张桌子和一台电脑","session_id":"s1"})["scene"])
print("mm.transcribe:", post("/api/multimodal/transcribe", {"transcript":"我想退款"})["emotion"])

# 5. chatbot
print("chatbot order:", post("/api/chatbot/chat", {"message":"帮我查订单 ORDER12345 的物流","session_id":"c1"})["intent"])
print("chatbot product:", post("/api/chatbot/chat", {"message":"你们支持哪些模型","session_id":"c2"})["reply"][:50])
print("chatbot refund:", post("/api/chatbot/chat", {"message":"我要退款订单 ORDER9999","session_id":"c3"})["tool_calls"])
print("ALL SMOKE TESTS PASSED")

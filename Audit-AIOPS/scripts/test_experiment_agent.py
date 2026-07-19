import httpx, io, json

BASE = "http://127.0.0.1:8001"
c = httpx.Client(base_url=BASE, timeout=30)

def show(title, obj):
    print(f"\n=== {title} ===")
    print(json.dumps(obj, ensure_ascii=False, indent=2)[:1500])

# 1) seed
r = c.post("/api/experiments/seed", json={"force": True})
show("seed", r.json())

# 2) metrics (effect)
r = c.get("/api/experiments/metrics")
m = r.json()
show("metrics", m)

# 3) query grounded
for q in ["哪种催化剂在 25°C 下产氢速率最高？", "可见光下哪些实验表现好？", "哪些实验用了 TiO2？"]:
    r = c.post("/api/experiments/query", json={"question": q, "top_k": 3})
    d = r.json()
    print(f"\n=== query: {q} ===")
    print("  sources:", d["sources"])
    print("  grounded:", d["grounded"])
    print("  answer[:200]:", d["answer"][:200].replace("\n", " "))

# 4) graph
r = c.get("/api/experiments/graph")
g = r.json()
show("graph summary", {"nodes": len(g["nodes"]), "edges": len(g["edges"]),
                        "sample_nodes": g["nodes"][:5], "sample_edges": g["edges"][:3]})

# 5) REAL user data upload (custom md)
custom_md = """# 自研 Cu2O/g-C3N4 Z型异质结产氢
日期：2026-04-01
催化剂：Cu2O/g-C3N4（Z型异质结）；合成方法：水热法
光源：可见光；牺牲剂：三乙醇胺；温度：25°C
表征：XRD、TEM、PL光谱确认异质结形成。
结果：产氢速率 1.05 mmol·g⁻¹·h⁻¹，稳定性优于单一 g-C3N4。
结论：Z型机制促进载流子分离，可见光性能显著提升。
"""
files = {"file": ("my-Cu2O-gC3N4.md", custom_md.encode("utf-8"), "text/markdown")}
r = c.post("/api/experiments/upload", files=files)
show("upload custom", {"status": r.json()["status"], "record": r.json()["record"]["title"],
                       "entities": r.json()["record"]["entities"][:10], "metrics_records": r.json()["metrics"]["records"]})

# 5b) upload a CSV
custom_csv = "样品,温度(°C),产氢速率(mmol/g/h)\nA,25,0.95\nB,40,0.70\nC,60,0.52\n"
files = {"file": ("my-temp-sweep.csv", custom_csv.encode("utf-8"), "text/csv")}
r = c.post("/api/experiments/upload", files=files)
show("upload csv", {"title": r.json()["record"]["title"], "kind": r.json()["record"]["kind"],
                    "content": r.json()["record"]["content"][:120]})

# 6) list
r = c.get("/api/experiments/list")
show("list total", {"total": r.json()["total"], "ids": [x["id"] for x in r.json()["records"]]})

# 7) metrics after upload (should grow)
r = c.get("/api/experiments/metrics")
show("metrics after upload", {"records": r.json()["records"], "entities": r.json()["entities"],
                              "cross_links": r.json()["cross_links"],
                              "potential_duplicates": r.json()["potential_duplicates"],
                              "time_saved_h": r.json()["estimated_time_saved_hours"]})

print("\nALL TESTS DONE")

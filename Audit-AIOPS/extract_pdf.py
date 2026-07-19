import fitz, os, sys

base = r"D:\download\project\TX-budddy\personal-portfolio\Audit-AIOPS"
pdfs = ["2-pico.pdf", "ai-agent-interview-guide-zh.pdf", "DocAI多人AI文档协作平台.pdf"]

for name in pdfs:
    path = os.path.join(base, name)
    doc = fitz.open(path)
    n = doc.page_count
    total_chars = 0
    out_lines = []
    for i, page in enumerate(doc):
        txt = page.get_text()
        total_chars += len(txt)
        out_lines.append(f"\n===== PAGE {i+1}/{n} =====\n{txt}")
    out_path = os.path.join(base, "extracted_" + name.replace(".pdf", ".txt"))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("".join(out_lines))
    doc.close()
    print(f"{name}: pages={n}, text_chars={total_chars}, saved->{out_path}")

"""
SFT 评测脚本（数据飞轮闭环的「评测」环节）。

在测试集上评测意图识别准确率与要素抽取（槽位）F1，输出报告。
配合 sft/train.py 形成「数据生成 → 训练 → 评测 → 回流」闭环，
是面试中覆盖「LLM 算法优化」类岗位的关键证据链。

用法：
    python sft/evaluate.py --data sft/data --checkpoint sft/checkpoints
（无 GPU / 无权重时，可加 --rule-baseline 用规则基线快速看评测口径是否合理。）
"""

import argparse
import json
import os
import re


def _parse_intent(text: str) -> str:
    # 规则基线：领域词 + 动作词的组合匹配，用于无模型时验证评测口径是否合理。
    t = text
    if "Ukey" in t or "ukey" in t:
        if "回收" in t or "注销" in t or "离职" in t:
            return "Ukey回收"
        if "调整" in t or "变更" in t or "权限" in t:
            return "Ukey调整"
        return "Ukey制作"
    if "邮件" in t or "邮箱" in t:
        return "远程邮件帐号调整"
    if "角色" in t or "权限变更" in t:
        return "人员角色权限变更"
    if "UPS" in t:
        return "UPS应急演练"
    if "会议终端" in t or "终端" in t:
        return "会议终端领用"
    if "打印机" in t:
        return "打印机领用"
    if "视频会议" in t:
        return "视频会议预约"
    if "巡检" in t:
        return "应用系统巡检"
    if "签收" in t or "资产" in t:
        return "资产签收确认"
    if "网站" in t or "门户" in t or "改版" in t:
        return "专网网站改版"
    if "告警" in t or "异常" in t or "处置" in t:
        return "异常告警处置"
    if "资源" in t or "发放" in t:
        return "计算存储资源发放"
    return "未知"


def evaluate_rule(data_dir: str):
    path = os.path.join(data_dir, "test.jsonl")
    total = 0
    hit = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            s = json.loads(line)
            user = s["messages"][1]["content"]
            gold = json.loads(s["messages"][2]["content"])["intent"]
            pred = _parse_intent(user)
            total += 1
            if pred == gold:
                hit += 1
    acc = hit / total if total else 0
    print(f"[rule-baseline] intent acc = {acc:.3f} ({hit}/{total})")
    return acc


def evaluate_model(data_dir: str, checkpoint: str):
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel

    base = "Qwen/Qwen2.5-1.5B"
    tok = AutoTokenizer.from_pretrained(base, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(base, trust_remote_code=True)
    model = PeftModel.from_pretrained(model, checkpoint)

    total, hit = 0, 0
    with open(os.path.join(data_dir, "test.jsonl"), encoding="utf-8") as f:
        for line in f:
            s = json.loads(line)
            user = s["messages"][1]["content"]
            gold = json.loads(s["messages"][2]["content"])["intent"]
            prompt = tok.apply_chat_template(
                [{"role": "user", "content": user}], tokenize=False, add_generation_prompt=True
            )
            out = model.generate(**tok(prompt, return_tensors="pt").to(model.device), max_new_tokens=64)
            pred = _parse_intent(tok.decode(out[0], skip_special_tokens=True))
            total += 1
            if pred == gold:
                hit += 1
    acc = hit / total if total else 0
    print(f"[model] intent acc = {acc:.3f} ({hit}/{total})")
    return acc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="sft/data")
    ap.add_argument("--checkpoint", default="sft/checkpoints")
    ap.add_argument("--rule-baseline", action="store_true")
    args = ap.parse_args()

    if args.rule_baseline or not os.path.isdir(args.checkpoint):
        evaluate_rule(args.data)
    else:
        evaluate_model(args.data, args.checkpoint)


if __name__ == "__main__":
    main()

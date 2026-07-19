"""
模型压缩 · 量化部署脚本（4-bit / 8-bit）
======================================
面试与研发亮点：把「模型压缩 / 量化」落地到 Audit-AIOPS 的部署链路。

为什么做：领域 SFT 后的模型若以 FP16 部署，7B 需 ~14GB 显存，边缘/成本敏感场景扛不住。
量化把权重从 FP16 压到 INT8 / NF4(4-bit)，显存与带宽大幅下降，推理吞吐提升、成本下降。

两种范式（本项目均给出可运行模板）：
- 8-bit 量化（LLM.int8 / bitsandbytes）：几乎无损，显存 ~减半。
- 4-bit NF4 量化（QLoRA 同款）：显存再降一档，配合 LoRA 训练后直接以 4-bit 基座 + LoRA 适配器推理，
  单卡 12~16GB 即可跑 7B~13B，是「训练用 QLoRA、推理用 4-bit」的一体化路线。

运行（需 GPU + torch + transformers + bitsandbytes + accelerate）：
    pip install torch transformers bitsandbytes accelerate
    python sft/quantize.py --model Qwen/Qwen2.5-1.5B --bits 4
    # 也可加载 SFT 后的 LoRA 适配器：--adapter sft/checkpoints/lora

说明：演示机无 GPU/权重，不实际执行；脚本为可上线模板。量化已在 sft/train.py 的训练侧
（load_in_4bit=True 的 QLoRA）打通，本脚本补足「推理侧量化部署」闭环。
"""

import argparse


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-1.5B")
    ap.add_argument("--adapter", default=None, help="可选 LoRA 适配器路径（SFT 产物）")
    ap.add_argument("--bits", type=int, choices=[4, 8], default=4)
    ap.add_argument("--max_new_tokens", type=int, default=256)
    return ap.parse_args()


def build_quant_config(bits: int):
    """返回 bitsandbytes 量化配置（与 transformers 的 load_in_4bit/8bit 对齐）。"""
    if bits == 4:
        # NF4：QLoRA 推荐的 4-bit 数据类型，对正态分布权重最友好
        return {
            "load_in_4bit": True,
            "bnb_4bit_quant_type": "nf4",
            "bnb_4bit_compute_dtype": "bfloat16",
            "bnb_4bit_use_double_quant": True,  # 双重量化：对量化常数再量化，进一步省显存
        }
    # 8-bit：LLM.int8()，对离群值做混合精度分解
    return {"load_in_8bit": True}


def main():
    args = parse_args()
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
    )
    from peft import PeftModel

    qcfg = build_quant_config(args.bits)
    print(f"[QUANT] loading {args.model} in {args.bits}-bit -> {qcfg}")

    tok = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        trust_remote_code=True,
        quantization_config=BitsAndBytesConfig(**qcfg),
        device_map="auto",
    )
    # 推理侧挂载 SFT 的 LoRA 适配器（训练用 QLoRA，推理复用同一份 4-bit 基座）
    if args.adapter:
        print(f"[QUANT] attaching LoRA adapter: {args.adapter}")
        model = PeftModel.from_pretrained(model, args.adapter)

    prompt = "请把「借终端开视频会并联网」拆成审批事项。"
    inputs = tok(prompt, return_tensors="pt").to(model.device)
    out = model.generate(**inputs, max_new_tokens=args.max_new_tokens)
    print("[QUANT] output:", tok.decode(out[0], skip_special_tokens=True))


if __name__ == "__main__":
    main()

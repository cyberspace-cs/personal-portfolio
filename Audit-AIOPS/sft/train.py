"""
领域 SFT 训练脚本（LoRA / QLoRA）。

目标：用合成 + 真实回流的审计运维数据，对基座模型（默认混元/千问兼容的 Qwen2.5 系列）
做轻量监督微调，强化「意图识别 + 要素抽取 + 审批路由」等平台专属能力，
对应岗位要求中的「LLM 算法优化 / 领域对齐」。

设计要点（面试可讲）：
- 采用 **LoRA** 低参微调，显存友好（单卡 24G 可跑 7B，QLoRA 可在 12G 跑通）；
- 基座可插拔：默认 Qwen2.5-0.5B/1.5B 冷启动，生产切 7B/14B 或混元/千问；
- 与「数据飞轮」衔接：训练数据来自 sft/dataset.py 生成 + 线上真实工单校正回流；
- 评测见 sft/evaluate.py，形成「数据-训练-评测」闭环证据链。

运行环境：需 GPU + 能拉取基座权重（HuggingFace / ModelScope）。
    pip install transformers peft accelerate datasets torch
    python sft/train.py --model Qwen/Qwen2.5-1.5B --data sft/data --out sft/checkpoints

说明：本脚本为可运行模板；演示机无 GPU/权重，不实际执行训练，仅作为方案交付与上线依据。
"""

import argparse
import os


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-1.5B")
    ap.add_argument("--data", default="sft/data")
    ap.add_argument("--out", default="sft/checkpoints")
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--batch", type=int, default=4)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--lora_r", type=int, default=16)
    ap.add_argument("--max_len", type=int, default=512)
    return ap.parse_args()


def main():
    args = parse_args()
    from datasets import load_dataset
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        Trainer,
        TrainingArguments,
    )
    from peft import LoraConfig, get_peft_model

    os.makedirs(args.out, exist_ok=True)
    print(f"[SFT] loading base model: {args.model}")

    tok = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(args.model, trust_remote_code=True)

    # LoRA 低参微调
    lora = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_r * 2,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=0.05,
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()

    ds = load_dataset("json", data_files={
        "train": os.path.join(args.out.replace("checkpoints", "data"), "train.jsonl"),
        "validation": os.path.join(args.out.replace("checkpoints", "data"), "test.jsonl"),
    }) if False else load_dataset("json", data_files={
        "train": os.path.join(args.data, "train.jsonl"),
        "validation": os.path.join(args.data, "test.jsonl"),
    })

    def tok_fn(ex):
        text = tok.apply_chat_template(ex["messages"], tokenize=False)
        out = tok(text, max_length=args.max_len, truncation=True)
        out["labels"] = out["input_ids"].copy()
        return out

    ds = ds.map(tok_fn, remove_columns=["messages"])

    training_args = TrainingArguments(
        output_dir=args.out,
        per_device_train_batch_size=args.batch,
        per_device_eval_batch_size=args.batch,
        num_train_epochs=args.epochs,
        learning_rate=args.lr,
        logging_steps=20,
        eval_strategy="epoch",
        save_strategy="epoch",
        bf16=True,
        report_to="none",
    )
    trainer = Trainer(model=model, args=training_args, train_dataset=ds["train"], eval_dataset=ds["validation"])
    trainer.train()
    trainer.save_model(args.out)
    print(f"[SFT] done -> {args.out}")


if __name__ == "__main__":
    main()

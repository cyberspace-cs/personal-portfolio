"""
SFT 冷启动数据集生成器（数据飞轮的「数据」环节）。

产出审计运维领域的监督微调数据，覆盖平台核心意图与要素抽取，
格式为 ShareGPT / ChatML 的 messages 列表，可直接被 sft/train.py 消费。

覆盖意图（对应十类审计支持 + 三类运维 + 异常处置）：
  Ukey制作 / Ukey调整 / Ukey回收 / 人员角色权限变更 / 远程邮件帐号调整 /
  计算存储资源发放 / UPS应急演练 / 会议终端领用 / 打印机领用 / 视频会议预约 /
  应用系统巡检 / 资产签收确认 / 专网网站改版 / 异常告警处置

用法：
  python sft/dataset.py --out sft/data --n 2000 --seed 42
生成：sft/data/train.jsonl, sft/data/test.jsonl
"""

import argparse
import json
import os
import random

# 意图 -> 用户说法模板（{x} 为可替换槽位）
TEMPLATES = {
    "Ukey制作": ["我要为{auditor}制作一个Ukey", "申请制作Ukey给{auditor}", "新同事{auditor}需要Ukey"],
    "Ukey调整": ["把{auditor}的Ukey权限调整为{level}", "Ukey权限变更，{auditor}调到{level}"],
    "Ukey回收": ["回收{auditor}的Ukey", "人员离职，回收{auditor}的Ukey", "注销{auditor}的Ukey"],
    "人员角色权限变更": ["把{auditor}在系统里的角色改为{role}", "调整{auditor}的运维角色为{role}"],
    "远程邮件帐号调整": ["为{auditor}开通远程邮件帐号，容量{cap}", "远程邮件帐号扩容到{cap}", "给{auditor}开邮箱并扩容{cap}"],
    "计算存储资源发放": ["申请{res}资源给{auditor}的项目", "发放{res}计算存储资源"],
    "UPS应急演练": ["安排一次UPS应急演练", "预约UPS应急演练时间"],
    "会议终端领用": ["借用一台会议终端", "领用会议终端用于{place}"],
    "打印机领用": ["领用一台打印机到{place}", "申请打印机一台"],
    "视频会议预约": ["预约视频会议，参会{num}人", "预定视频会议"],
    "应用系统巡检": ["对{sys}做一次自动化巡检", "巡检应用系统{sys}"],
    "资产签收确认": ["资产到货，请自动签收确认", "签收确认一批运维资产"],
    "专网网站改版": ["专网网站需要改版，技术支持", "专网门户改版协助"],
    "异常告警处置": ["{sys}出现告警，请生成处置工单", "计算存储设备异常，自动处置"],
}

SLOT_POOL = {
    "auditor": ["审计一组", "审计二组", "审计三组", "张三", "李四", "王五", "赵六"],
    "level": ["高级", "中级", "基础", "只读"],
    "role": ["运维负责人", "审计员", "系统管理员", "访客"],
    "cap": ["2G", "5G", "10G", "20G"],
    "res": ["2核4G", "4核8G", "8核16G", "1TB存储"],
    "place": ["三楼会议室", "五楼办公区", "审计现场", "指挥中心"],
    "num": ["5", "10", "20", "30"],
    "sys": ["OA系统", "邮件系统", "门户网站", "日志平台", "监控平台"],
}

SYSTEM = (
    "你是审计智能一体化运维平台的意图理解模块。给定用户一句话，"
    "输出 JSON：{\"intent\": 意图名, \"slots\": {抽取到的要素}}。"
    "意图名必须来自已知意图集合。"
)


def fill(tpl: str, rng: random.Random) -> tuple:
    slots = {}
    import re

    for key in re.findall(r"\{(\w+)\}", tpl):
        val = rng.choice(SLOT_POOL.get(key, ["X"]))
        slots[key] = val
        tpl = tpl.replace("{" + key + "}", val)
    return tpl, slots


def build(n: int, seed: int):
    rng = random.Random(seed)
    intents = list(TEMPLATES.keys())
    rows = []
    for _ in range(n):
        intent = rng.choice(intents)
        tpl = rng.choice(TEMPLATES[intent])
        user, slots = fill(tpl, rng)
        assistant = json.dumps({"intent": intent, "slots": slots}, ensure_ascii=False)
        rows.append({
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": user},
                {"role": "assistant", "content": assistant},
            ]
        })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="sft/data")
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    rows = build(args.n, args.seed)
    rng = random.Random(args.seed + 1)
    rng.shuffle(rows)
    split = int(len(rows) * 0.9)
    with open(os.path.join(args.out, "train.jsonl"), "w", encoding="utf-8") as f:
        for r in rows[:split]:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(os.path.join(args.out, "test.jsonl"), "w", encoding="utf-8") as f:
        for r in rows[split:]:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"[dataset] 生成 {split} 训练 / {len(rows)-split} 测试 → {args.out}")


if __name__ == "__main__":
    main()

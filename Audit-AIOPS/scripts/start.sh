#!/usr/bin/env bash
# 一键启动脚本（开发 / 单机部署通用）
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_DIR"

PY="${PYTHON:-python3}"

echo "==> 检查依赖"
if [ ! -x "$(command -v $PY)" ]; then
  echo "缺少 python，请先安装 Python 3.13+"; exit 1
fi

$PY -m pip install -q -r requirements.txt || echo "（依赖安装失败请手动处理）"

echo "==> 生成 SFT 冷启动数据（如不存在）"
if [ ! -f "sft/data/train.jsonl" ]; then
  $PY sft/dataset.py --out sft/data --n 2000
fi

echo "==> 启动服务（端口 ${PORT:-8000}）"
export PORT="${PORT:-8000}"
exec $PY -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT"

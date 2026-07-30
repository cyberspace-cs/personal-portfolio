#!/usr/bin/env bash
# 竞赛信息聚合平台 · 后端启动脚本
# 用法: bash start.sh   (或: python main.py)
set -e
cd "$(dirname "$0")"

# 可选：隔离虚拟环境
if [ ! -d ".venv" ]; then
  python -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate 2>/dev/null || true

pip install -q -r requirements.txt

# 首次运行写入示例数据（竞赛表为空时自动种子）
python seed.py || true

export PORT="${PORT:-8000}"
echo "🚀 竞赛聚合平台后端启动于 http://localhost:${PORT}  (API 文档 /docs)"
exec uvicorn main:app --host 0.0.0.0 --port "$PORT" --reload

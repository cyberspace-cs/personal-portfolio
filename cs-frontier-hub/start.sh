#!/usr/bin/env bash
# 一键启动：安装依赖 -> 初始化/填充数据库 -> 启动 FastAPI（同时托管前端）
set -e
cd "$(dirname "$0")/server"
pip install -r requirements.txt
python -c "import seed_data; seed_data.seed()"
exec uvicorn main:app --host 0.0.0.0 --port 8000

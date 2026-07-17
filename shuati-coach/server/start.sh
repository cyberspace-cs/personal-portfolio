#!/usr/bin/env bash
# ================================================================
#  专属刷题教练 · 一键启动脚本（Python + FastAPI + SQLite）
#  用法：
#    ./start.sh                 # 无 Key 降级模式启动（AI 功能仍可用）
#    API_KEY=sk-xxx ./start.sh # 接入真实大模型
#    PORT=9000 ./start.sh      # 指定端口
# ================================================================
set -e

cd "$(dirname "$0")"

PORT="${PORT:-8000}"
export PORT

echo "[1/3] 正在检查 Python 依赖…"
python3 -m pip install -q -r requirements.txt 2>&1 | tail -3 || {
  echo "依赖安装失败，请手动执行：pip install -r requirements.txt"
}

if [ -n "$API_KEY" ]; then
  export API_KEY
  echo "[AI] 检测到 API_KEY，将启用真实大模型（AI 讲题 / 变式题 / 押题报告）。"
else
  echo "[AI] 未检测到 API_KEY，AI 接口以「降级模式」运行（返回结构化讲解，前端功能不受影响）。"
  echo "     如需真实大模型，请用：API_KEY=你的Key ./start.sh"
fi

echo ""
echo "启动服务中… 访问地址："
echo "   前端页面： http://localhost:${PORT}/coach.html"
echo "   健康检查： http://localhost:${PORT}/api/health"
echo "   按 Ctrl+C 停止服务"
echo "============================================================"

python3 main.py

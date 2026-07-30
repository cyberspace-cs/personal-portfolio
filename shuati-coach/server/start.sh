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

# 加载本地 .env（已被 .gitignore 忽略，不会进仓库）：
# 支持多厂商 Key，例如 DEEPSEEK_API_KEY / LLM_PROVIDER=deepseek
# 也可用环境变量直接传：DEEPSEEK_API_KEY=sk-xxx LLM_PROVIDER=deepseek ./start.sh
if [ -f .env ]; then
  set -a
  . ./.env
  set +a
  echo "[env] 已加载本地 .env（密钥仅本地生效）"
fi

PORT="${PORT:-8000}"
export PORT

echo "[1/3] 正在检查 Python 依赖…"
python3 -m pip install -q -r requirements.txt 2>&1 | tail -3 || {
  echo "依赖安装失败，请手动执行：pip install -r requirements.txt"
}

# 多厂商 Key 探测（优先级：LLM_PROVIDER 指定厂商的 Key → 任意已配置 Key）
if [ -n "$LLM_PROVIDER" ] && env | grep -qiE "^${LLM_PROVIDER^^}_API_KEY="; then
  echo "[AI] 检测到 ${LLM_PROVIDER^^}_API_KEY，将启用真实大模型（${LLM_PROVIDER}）：AI 讲题 / 自适应计划 / 变式题 / 押题报告。"
elif [ -n "$DEEPSEEK_API_KEY" ]; then
  export LLM_PROVIDER="${LLM_PROVIDER:-deepseek}"
  echo "[AI] 检测到 DEEPSEEK_API_KEY，将启用真实大模型（deepseek）。"
elif [ -n "$API_KEY" ]; then
  export API_KEY
  echo "[AI] 检测到传统 API_KEY（自定义 OpenAI 兼容网关）。"
else
  echo "[AI] 未检测到任何大模型 Key，AI 接口以「降级模式」运行（仍按薄弱点排优先级，前端功能不受影响）。"
  echo "     接入真实大模型：DEEPSEEK_API_KEY=你的Key LLM_PROVIDER=deepseek ./start.sh"
fi

echo ""
echo "启动服务中… 访问地址："
echo "   前端页面： http://localhost:${PORT}/coach.html"
echo "   健康检查： http://localhost:${PORT}/api/health"
echo "   按 Ctrl+C 停止服务"
echo "============================================================"

python3 main.py

# 审计智能一体化运维平台 · 镜像构建
# 用法：docker compose up -d --build   （见 docker-compose.yml）
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 先装依赖层（利用缓存）
COPY requirements.txt .
RUN pip install -r requirements.txt

# 复制源码
COPY . .

# 暴露服务端口
EXPOSE 8000

# 若缺少 SFT 冷启动数据则生成（不影响主服务启动）
RUN python sft/dataset.py --out sft/data --n 500 || true

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health').status==200 else 1)"

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

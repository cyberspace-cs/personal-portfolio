# 专属刷题教练 · 后端镜像
# 构建上下文：项目根目录（../），这样可同时拷入 server/ 与 coach.html
FROM python:3.11-slim
WORKDIR /app

COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY server/ /app/
# 把项目根的 H5 平台一并拷入，供 web-view / 静态访问
COPY coach.html /app/coach.html

ENV STATIC_DIR=/app
EXPOSE 8000
CMD ["gunicorn", "main:app", "-k", "uvicorn.workers.UvicornWorker", \
     "-b", "0.0.0.0:8000", "--workers", "2", "--timeout", "120"]

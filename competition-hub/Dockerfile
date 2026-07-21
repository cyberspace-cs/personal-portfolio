# ---- 阶段 1：构建前端 ----
FROM node:20-alpine AS web
WORKDIR /web
COPY web/package*.json ./
RUN npm install
COPY web/ ./
RUN npm run build

# ---- 阶段 2：后端运行（同时托管已构建的前端）----
FROM python:3.11-slim
WORKDIR /app
COPY server/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY server/ ./
COPY --from=web /web/dist ./web/dist
RUN python seed.py
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

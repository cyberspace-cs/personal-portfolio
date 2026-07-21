# API 文档

基础路径：`/api`。认证接口返回 `token`，后续请求在 Header 携带 `Authorization: Bearer <token>`。
完整在线文档（Swagger）：启动后端后访问 `/docs`。

通用响应：成功返回 JSON；失败返回 `{ "detail": "错误信息" }` 与对应 HTTP 状态码（400/401/404/409）。

---

## 健康检查

`GET /health`
```json
{ "status": "ok", "service": "competition-hub", "time": "2026-07-22T00:00:00" }
```

---

## 分类

### 列表 `GET /categories`
返回分类数组，每项含 `count`（该分类竞赛数）。
```json
[
  { "id": 1, "name": "黑客松", "slug": "hackathon", "icon": "🚀",
    "description": "…", "sort_order": 1, "count": 6 }
]
```

### 创建 `POST /categories`（需登录）
Body：`{ "name": "新分类", "slug": "newcat", "icon": "✨", "description": "…", "sort_order": 9 }`
冲突返回 409。

---

## 竞赛

### 列表 `GET /competitions`
查询参数：

| 参数 | 说明 | 示例 |
| --- | --- | --- |
| `q` | 关键词（标题/简介/主办方/描述/标签） | `Kaggle` |
| `category` | 分类 slug | `hackathon` |
| `status` | `upcoming` / `ongoing` / `ended` | `ongoing` |
| `mode` | `online` / `offline` / `hybrid` | `online` |
| `tag` | 标签名 | `AI` |
| `sort` | `latest` / `prize` / `deadline` / `views` | `prize` |
| `page` | 页码（从 1） | `1` |
| `page_size` | 每页数量（≤60） | `12` |

响应：
```json
{
  "items": [
    { "id": 1, "title": "2026 腾讯云 AI 游戏开发黑客松", "slug": "…", "summary": "…",
      "category_id": 1, "category_name": "黑客松", "organizer": "腾讯云开发者社区",
      "location": "深圳", "mode": "offline", "prize": "¥ 150,000", "prize_amount": 150000,
      "status": "ongoing", "start_date": "2026-06-14", "end_date": "2026-08-19",
      "reg_deadline": "2026-07-30", "tags": ["AI游戏","实时渲染"], "cover": "",
      "source_url": "https://…", "featured": true, "views": 12,
      "created_at": "…", "updated_at": "…", "is_favorited": false }
  ],
  "total": 24, "page": 1, "page_size": 12, "total_pages": 2
}
```

### 详情 `GET /competitions/{id}`
返回单条竞赛（自动浏览量 +1）。携带 Token 时 `is_favorited` 反映当前用户状态。404 返回错误。

### 创建 `POST /competitions`（需登录）
Body（与 `CompetitionIn` 一致）：
```json
{
  "title": "示例赛", "slug": "demo-2026", "summary": "简介",
  "description": "详细介绍\n第二段", "category_id": 1, "organizer": "主办方",
  "location": "线上", "mode": "online", "prize": "¥ 50,000", "prize_amount": 50000,
  "status": "upcoming", "start_date": "2026-09-01", "end_date": "2026-09-03",
  "reg_deadline": "2026-08-25", "tags": ["AI","青年"], "cover": "",
  "source_url": "https://…", "featured": false
}
```
`slug` 重复返回 409。

### 更新 `PUT /competitions/{id}`（需登录）
Body 同创建（需含 `slug`）。返回更新后的竞赛。

### 删除 `DELETE /competitions/{id}`（需登录）
返回 `{ "ok": true, "deleted": <id> }`。

---

## 统计

`GET /stats`
```json
{
  "total": 24, "ongoing": 8, "upcoming": 11, "ended": 5,
  "categories": 8, "users": 3,
  "top_viewed": [ { "id": 1, "title": "…", "views": 42 } ]
}
```

---

## 用户认证

### 注册 `POST /auth/register`
Body：`{ "username": "alice", "password": "secret123", "email": "a@b.com" }`
返回：`{ "token": "<jwt-like>", "user": { "id": 1, "username": "alice", "role": "user", … } }`
用户名已存在返回 409。

### 登录 `POST /auth/login`
Body：`{ "username": "alice", "password": "secret123" }`，返回同上。凭证错误返回 401。

### 当前用户 `GET /auth/me`（需登录）
返回 `UserOut`。

### 退出 `POST /auth/logout`（需登录）
使当前 token 失效，返回 `{ "ok": true }`。

---

## 收藏

### 列表 `GET /favorites`（需登录）
返回当前用户收藏的竞赛数组（结构同竞赛列表项）。

### 添加 `POST /favorites`（需登录）
Body：`{ "competition_id": 1 }` → `{ "ok": true, "favorited": true }`。

### 取消 `DELETE /favorites/{competition_id}`（需登录）
→ `{ "ok": true, "favorited": false }`。

### 检查 `GET /favorites/check/{competition_id}`
匿名返回 `{ "favorited": false }`；登录用户返回真实状态。

---

## 认证示例（curl）

```bash
# 注册
curl -X POST http://localhost:8000/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"secret123"}'

# 携带 token 收藏
curl -X POST http://localhost:8000/api/favorites \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{"competition_id":1}'
```

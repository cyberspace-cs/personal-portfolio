# 实习 Show 后端（server/）

轻量后端：**FastAPI + SQLAlchemy 2.0 + SQLite**，零外部服务即可跑通，作为「人定方向 + AI 补后端」的第 2 步。

## 运行

```bash
cd shixi-show/server
pip install -r requirements.txt
python seed.py          # 首次插入示例数据（可重复执行，已存在则跳过）
uvicorn main:app --reload --port 5000
# 或：python main.py
```

启动后自动建表；若库为空会自动 seed。接口文档：http://localhost:5000/docs

> 小程序端 `utils/request.js` 默认 `baseUrl=http://localhost:5000/api`。真机调试需在微信开发者工具勾选「不校验合法域名」，或部署到 https 域名。

## 接口一览

### 用户端
| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/companies/rank?page=&size=` | 热门排行榜（按评论数降序） |
| GET | `/api/companies/search?q=` | 公司名/行业模糊搜索 |
| GET | `/api/companies/{id}` | 公司详情 + 通过的点评 |
| POST | `/api/reviews` | 提交点评（进入审核中） |
| GET | `/api/users/my-reviews?userId=` | 我的点评（带状态） |
| POST | `/api/favorites` | 收藏公司 |
| POST | `/api/reports` | 举报点评 |

### 管理端（审核状态机）
| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/admin/reviews?status=` | 列表（status 缺省=全部；0审核中/1通过/2拒绝） |
| POST | `/api/admin/reviews/{id}/audit` | 审核 `{action:'approve'|'reject', reason?, adminId?}` |

审核状态机：
```
提交 ──▶ 0 审核中 ──approve──▶ 1 通过（重算公司 avg_score / review_count）
                 └──reject──▶ 2 拒绝（用户可见 reason）
拒绝审核不可重复操作。
```

## 字段约定（与前端对齐）
- 响应统一 **camelCase**：`avgScore` / `reviewCount` / `companyId` / `auditReason` / `createdAt` 等。
- `scores`：`{mentor, growth, 转正, 薪资, wlb}`（1-5 分）
- `stamps`：`['推荐' | '还想来' | '一般' | '避雷' | ...]`
- `status`：`0 审核中 / 1 通过 / 2 拒绝`

## 数据表
`companies / departments / users / reviews / favorites / reports / audits`
（模型见 `models.py`，建模思路来自公众号文章中 Kimi K3 的设计）

# 实习 Show（实习点评小程序）

> 灵感来源：公众号「居丽叶的大模型视界」文章《我把做了一半的实习点评小程序交给 kimi k3，结果前后端都补齐了》（2026-07-21）。
> 本文先**梳理小程序的方法与设计**，再作为本仓库的蓝图，逐步落地一个可运行的实习点评小程序。

---

## 1. 项目定位

建立一个**实习经历点评平台**，收集各大公司 / 部门 / 岗位的真实实习感受，帮助用户「避雷避坑」。

点评维度（参考文章）：
- mentor 质量、团队节奏、学习资源、转正机会、薪资待遇、工作生活平衡
- 用「盖章」方式做定性结论（例如：还想来 / 拉；避雷 / 推荐）

核心用户价值：**信息不对称 → 透明化**。

---

## 2. 功能模块拆解

### 2.1 用户端（微信小程序）
| 模块 | 功能 |
| --- | --- |
| 首页 / 排行榜 | 热门公司排行（火焰标识、评分、标签、印章），品牌主视觉 |
| 搜索 | 按公司 / 部门 / 岗位搜索 |
| 公司详情 | 公司信息、Logo、各维度评分、点评列表 |
| 写点评 | 多维度打分 + 盖印章 + 提交 |
| 个人中心 | 我的点评（审核中 / 通过 / 拒绝）、收藏、消息、举报记录 |
| 小彩蛋 | 写完点评后的隐藏彩蛋（产品留存钩子） |

### 2.2 后端 / 数据层
- 用户登录 / 匿名身份
- 点评入库、审核流程（审核中 → 通过 / 拒绝）
- 公司 / 部门 / Logo 维护
- 收藏 / 评论 / 举报 / 消息逻辑

### 2.3 管理后台（Web）
- 审核用户提交的点评（通过 / 拒绝 + 理由）
- 查看提交内容、公司 / 部门维护

---

## 3. 技术选型（方法对比 + 本仓库决策）

| 方案 | 优点 | 缺点 | 适用 |
| --- | --- | --- | --- |
| **原生小程序** (WXML/WXSS/JS) | 零构建、微信开发者工具直接跑、上手快 | 复用性差、无组件化工程化 | MVP / 快速验证 ✅ |
| Vue3 框架 (uni-app / Taro) | 组件化、可多端、工程化好 | 需 node 构建、调试链路长 | 成长期 / 多端 |

**本仓库决策**：先用**原生微信小程序**落地 MVP（与文章初版一致，最简单可跑），后端先以**本地 mock 数据 + 轻量接口**跑通主流程，后续可平滑迁移到 Vue3 或云开发。

> 文章中 Kimi K3 将前端迁到 Vue3 并补了后端数据表（companies / departments / users / reviews / favorites / comments / reports / audits）。本仓库会吸收其数据建模思路。

---

## 4. 小程序前端方法

### 4.1 页面与路由（原生小程序）
```
pages/
  index/        首页 + 热门排行榜        (首页)
  search/       搜索公司/部门/岗位
  company/      公司详情 + 点评列表       (需 companyId)
  review/       写点评（多维度 + 盖章）
  profile/      个人中心
  myReviews/    我的点评（审核状态）
  favorites/    我的收藏
  messages/     消息 / 举报记录
```
`app.json` 的 `pages` 数组注册，`tabBar` 放首页 / 搜索 / 写点评 / 我的。

### 4.2 数据流转
- 初版：`getHotCompanies()` 直接读本地数据（最快出界面）。
- 升级：`api.getRankedCompanies(page, size)` 调服务端 REST 接口。
- 统一封装 `utils/request.js`（wx.request 封装 + 登录态注入）。

### 4.3 组件化（关键方法）
- `components/company-logo`：**缺图自动用文字 Logo**（取公司名首字 + 固定底色），解决外链 Logo 不稳定。
- `components/score-badge`：评分星 / 印章组件。
- `components/tag-chip`：标签截断与折行。

### 4.4 登录与身份
- `wx.login()` 拿 code → 后端换 openid → 本地存 `token`（wx.setStorageSync）。
- 匿名也可浏览；写点评需登录。

### 4.5 视觉与异常兜底
- 首页品牌主视觉（渐变 + 大字标题）。
- 列表空态、加载失败兜底（文章实战中踩过的坑）。
- 图片加载失败 → 回退 `company-logo` 文字 Logo。

---

## 5. 后端 / 数据层方法

### 5.1 数据表建模（吸收 Kimi K3 设计）
| 表 | 关键字段 |
| --- | --- |
| companies | id, name, logo, industry, avg_score, review_count |
| departments | id, company_id, name |
| users | id, openid, nickname |
| reviews | id, user_id, company_id, dept_id, scores(JSON), stamps(JSON), status(0审核中/1通过/2拒绝), created_at |
| favorites | id, user_id, company_id |
| comments | id, review_id, user_id, content |
| reports | id, review_id, user_id, reason, status |
| audits | id, review_id, admin_id, action, reason, created_at |

### 5.2 接口设计（REST）
- `GET  /api/companies/rank?page=&size=` 热门排行
- `GET  /api/companies/search?q=` 搜索
- `GET  /api/companies/:id` 公司详情 + 点评
- `POST /api/reviews` 提交点评
- `GET  /api/users/my-reviews` 我的点评（带状态）
- `POST /api/favorites` 收藏
- `POST /api/reports` 举报
- 管理端：`GET /api/admin/reviews?status=` / `POST /api/admin/reviews/:id/audit`

### 5.3 审核状态机
```
提交 ──▶ 审核中(0) ──审核通过──▶ 通过(1) ──▶ 计入公司评分
                 └──审核拒绝──▶ 拒绝(2) ──▶ 用户可见原因
```

---

## 6. 管理后台方法
- 独立 Web 页面（原生 HTML + 简单后端即可），登录后：
  - 列表展示待审点评（含公司、维度分、印章、原文）。
  - 通过 / 拒绝（填理由）→ 写 `audits` 表，更新 `reviews.status`。
  - 通过的点评重新聚合到 `companies.avg_score`。

---

## 7. 开发流程（含 AI 辅助）
参考文章「人定方向 + AI 补码」：
1. 原型：先出纯前端页面与交互（本地数据），定产品逻辑。
2. 补后端：建表 + 写接口，打通存储。
3. 管理后台：闭环审核。
4. 前端迁移 / 打磨：组件化、视觉、异常兜底。
5. 人验收：定义业务规则（如「还想来」不能盖「拉」章），AI 改码后人工测 bug 迭代。

---

## 8. 本仓库目录规划
```
shixi-show/
├── README.md                 # 本文（方法梳理 + 蓝图）
├── miniprogram/              # 原生微信小程序前端
│   ├── app.js / app.json / app.wxss
│   ├── pages/                # 各页面
│   ├── components/           # company-logo / score-badge / tag-chip
│   ├── utils/request.js      # 请求封装
│   └── mock/                 # 本地 mock 数据（先跑通界面）
├── server/                   # 轻量后端（Flask/FastAPI 或云函数）
│   ├── models.py             # 数据表
│   ├── api.py                # 接口
│   └── seed.py               # 示例数据
└── admin/                    # 管理后台
    └── index.html
```

> 下一步：按此蓝图先搭 `miniprogram/` 页面骨架 + `mock/` 数据，用微信开发者工具即可预览主流程。

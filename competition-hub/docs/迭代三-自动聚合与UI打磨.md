# 迭代三 · 自动聚合引擎 + 前端效果打磨

> 目标（用户明确优先级）：**「重点是自动搜寻赛事加入进去」** + **「完善赛事和网页效果第一」**。
> 本迭代把平台从「手动发布」升级为「自动聚合为主、手动补充为辅」，并补齐赛博风格的前端动效。

---

## 1. 需求与设计

### 1.1 自动聚合（核心）
- 建设可插拔的**数据源适配器**体系：抽象基类 `SourceAdapter`（`fetch` / `parse`），新增具体适配器：
  - `HeikeSongAdapter`：解析 [heikesong.cn](https://heikesong.cn/) 首页赛博轮播区块（`cyber-carousel-*`），实时抓取精选赛事实时入库。
  - `BundleAdapter`：读取 `collector_sources.json` 多源聚合数据集（Kaggle / 天池 / 华为云 / 腾讯 / 字节 / 强网杯 / 天府杯 / 京东 / 百度 / 研究生数模 / Google / 微软 / AWS / 工业设计 等 16+ 来源）。
- **幂等入库**：`database.import_competitions(rows)` 按 `slug` upsert，重复执行 `created` 归零、`updated` 递增，不污染数据。
- **自动归类**：`classify_category(text)` 关键词分类 → 缺失分类由 `_ensure_category` 自动创建（含默认图标）。
- **网络容错**：单源失败不影响其他源；`run_collection()` 返回每个源的 `fetched` 与 `error`，整体不抛未捕获异常。
- **管理员一键触发**：新增 `GET /api/collect/sources`（公开，列数据源）与 `POST /api/collect`（管理员，触发聚合）。导航栏对 `role==='admin'` 显示「一键聚合」按钮，结果以 toast 反馈。

### 1.2 前端效果
- 列表卡片**交错入场动画**（`--i` 自定义属性 + `cardEnter` 关键帧，55ms 阶梯延迟）。
- **骨架屏**加载态（6 张 shimmer 占位卡，替代原 spinner）。
- 卡片新增 **「聚合自 {source}」** 来源徽标（左下，带脉冲点）、**标签胶囊**（前 3 个 tag）、浏览量（`Eye` 图标）。
- `Hero` 文案升级为「AI 自动聚合 · 实时更新赛事库」，强调自动搜寻能力。
- `source` 字段贯穿后端模型 → 前端 `types` → `api` 客户端 → 卡片展示，端到端打通。
- 「我的收藏」卡片同样应用交错动画。

---

## 2. 代码审查要点

| 项 | 处理 |
| --- | --- |
| 聚合引擎无单测 | 新增 `tests/test_collector.py`：heikesong 真实夹具解析、bundle 加载、分类/slug、幂等导入、stub 适配器端到端、collect 端点鉴权。 |
| 管理端点仅 `require_user` | 收紧为 `require_admin`（新增依赖），非管理员 403，未登录 401。 |
| 无默认管理员 | `seed.ensure_admin()` 在启动时确保存在管理员（env `ADMIN_USERNAME/ADMIN_PASSWORD` 可覆盖，默认 `admin/Admin@2026`）。 |
| `source` 列缺失 | `init_db()` 增加幂等迁移 `ALTER TABLE ... ADD COLUMN source`；`import_competitions`、响应模型、前端类型同步补齐。 |

> 历史安全项（R1–R7）保持：CORS 收敛、安全响应头、统一错误响应、限流等。R2 的 `X-Frame-Options: DENY` 会导致内置 iframe 预览面板无法直接嵌入，故预览改用自包含 `preview.html`（不含安全头）。

---

## 3. 测试结果

- **后端单测：28 passed, 19 warnings**（pytest，临时库隔离）。
- **Live 链路验证（端口 8210，新构建 dist）**：
  - `GET /api/health` → 200
  - `GET /api/competitions` → 18 条，全部带 `source`
  - `GET /api/collect/sources` → 返回 2 个数据源
  - `POST /api/collect`（无 token）→ **401**
  - `POST /api/collect`（管理员 token）→ **200**，`created:0, updated:18, total:18`，两源分别 `fetched:2 / 16`
  - `POST /api/collect`（普通用户 token）→ **403**
  - 幂等复核：二次触发 `created:0 / updated:18`
  - 前端静态资源（`/assets/*.js|css`）→ 200；SPA 回退 `/competition/1` → 200

---

## 4. 交付物

- `server/collector.py`、`server/collector_sources.json`、`server/database.py`（`import_competitions`）、`server/seed.py`（`ensure_admin`）、`server/main.py`（collect 端点 + admin 依赖）。
- `web/src`：`CompetitionCard`（来源徽标/标签/动画）、`index.css`（动画/骨架/胶囊）、`Hero`/`Navbar`（一键聚合）/ `FavoritesPage`（index）/`types`/`api` 同步。
- `preview.html`：自包含前端效果预览（18 张真实卡片，无 CSP 限制，任意浏览器可开）。
- 本迭代文档 + README 更新。

---

## 5. 后续（未阻塞本迭代）
- R2 跟进：CSP 移除 `unsafe-inline`（内联样式需哈希/nonce）。
- R6：标签精确匹配经由关系表（当前为 `LIKE` 模糊）。
- 可继续扩充 `collector_sources.json` 与新增适配器（如 jikezhen、各高校官网 RSS）。

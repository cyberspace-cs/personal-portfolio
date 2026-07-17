# 专属刷题教练 · 微信小程序（B+C 方案）

手机刷题首选入口。核心刷题流用**小程序原生**实现（体验最佳），AI 讲题 / 变式 / 押题报告等重交互页面用 **web-view 承载 H5**（`coach.html`），二者复用同一套 FastAPI 后端。

## 目录结构

```
miniprogram/
├── app.js / app.json / app.wxss      # 全局配置与请求封装
├── project.config.json / sitemap.json
└── pages/
    ├── index/   首页（分类入口、统计、打卡、深度版入口）
    ├── quiz/    答题页（单选/多选/判断，调用后端题库）
    ├── wrong/   错题本（调用后端错题接口）
    ├── mine/    我的（打卡、数据、web-view 入口）
    ├── chat/    问教练（Hermes Agent 驱动的多轮智能答疑）
    └── webview/ web-view 承载完整 H5 平台（C 方案核心）
```

## 页面与后端接口对应关系

| 小程序页面 | 调用的后端接口 |
|-----------|---------------|
| index 首页 | `GET /api/questions`、`/api/streak/{uid}`、`/api/wrong-book/{uid}` |
| quiz 答题 | `GET /api/questions?cat=`、`POST /api/quiz/record`、`POST /api/wrong-book` |
| wrong 错题本 | `GET /api/wrong-book/{uid}` |
| mine 我的 | `GET /api/streak/{uid}`、`POST /api/checkin/{uid}`、`GET /api/quiz/history/{uid}` |
| webview 深度版 | 打开 `coach.html`（H5 端完整 AI 能力） |
| chat 问教练 | `POST /api/chat`（转发给后端代理的 Hermes Agent 做智能答疑） |

## 三步跑起来

### 1. 后端部署（已有 FastAPI 服务）
```bash
cd server
pip install -r requirements.txt
python3 main.py        # 监听 0.0.0.0:8000，已 seed 60 道题库
```
需让手机可访问该地址：本地调试用电脑局域网 IP（如 `http://192.168.1.100:8000`）；正式发布需**公网 HTTPS 域名**并配置 CORS。

### 2. 配置后端地址
打开 `miniprogram/app.js`，修改：
```js
globalData: {
  baseUrl: 'https://YOUR_SERVER_DOMAIN'   // 改成你的后端地址
}
```
> 注意：微信小程序要求 `request` 域名必须 **HTTPS 且 ICP 备案**。本地预览可在开发者工具勾选「不校验合法域名」。

### 3. 用微信开发者工具导入
- 打开微信开发者工具 → 导入项目 → 选择 `miniprogram/` 目录。
- AppID 可用「测试号」(touristappid) 快速预览；正式发布需自有小程序 AppID。
- 真机预览：编译后点「预览」用手机扫码，配合本地 IP 或公网域名即可刷题。

## web-view 深度版说明
`pages/webview` 通过 `<web-view src=".../coach.html">` 打开完整 H5 平台。
使用前需把 `coach.html` 部署到与 `baseUrl` 同域的 HTTPS 地址，否则 web-view 会被微信拦截。

## 已验证
- 后端 `/api/questions` 返回 **60 道**（考研/考公/大厂各 20 道）。
- 小程序页面逻辑、接口字段与后端 `models.py` 完全一致。

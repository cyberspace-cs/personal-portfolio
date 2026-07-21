"""竞赛信息聚合平台 · 后端自动化测试（测试工程师阶段）

覆盖：健康检查 / 安全头 / 分类 / 列表筛选搜索 / 详情 / 认证 / 收藏 / CRUD / 限流 / 输入校验
运行：在 server/ 下执行  .venv/Scripts/python.exe -m pytest tests/ -q
"""
import random
import string


def _rand_user():
    s = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return "u_" + s


def _auth_headers(token):
    return {"Authorization": "Bearer " + token}


# ---------------- 健康检查 & 安全头 ----------------
def test_health_ok(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["service"] == "competition-hub"


def test_security_headers_present(client):
    r = client.get("/api/health")
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"
    assert r.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "Content-Security-Policy" in r.headers
    assert "Permissions-Policy" in r.headers


# ---------------- CORS 收敛 ----------------
def test_cors_allowed_origin_echoed(client):
    r = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    assert r.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"


def test_cors_untrusted_origin_not_echoed(client):
    r = client.get("/api/health", headers={"Origin": "http://evil.example.com"})
    assert (r.headers.get("Access-Control-Allow-Origin") or "") != "http://evil.example.com"


# ---------------- 分类 ----------------
def test_categories_listed(client):
    r = client.get("/api/categories")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list) and len(data) >= 8
    assert all("count" in c for c in data)


# ---------------- 列表 / 筛选 / 搜索 / 分页 ----------------
def test_competitions_list_paginated(client):
    r = client.get("/api/competitions", params={"page": 1, "page_size": 5})
    assert r.status_code == 200
    body = r.json()
    assert body["page"] == 1
    assert body["page_size"] == 5
    assert body["total"] >= 1
    assert len(body["items"]) <= 5
    assert body["total_pages"] >= 1


def test_competitions_search(client):
    # 先取一条已知标题做关键词搜索
    first = client.get("/api/competitions", params={"page_size": 1}).json()["items"][0]
    kw = first["title"][:3]
    r = client.get("/api/competitions", params={"q": kw})
    assert r.status_code == 200
    assert r.json()["total"] >= 1


def test_competitions_filter_status(client):
    r = client.get("/api/competitions", params={"status": "ongoing"})
    assert r.status_code == 200
    items = r.json()["items"]
    assert all(it["status"] == "ongoing" for it in items)


def test_competitions_filter_mode(client):
    r = client.get("/api/competitions", params={"mode": "online"})
    assert r.status_code == 200
    items = r.json()["items"]
    assert all(it["mode"] == "online" for it in items)


def test_competitions_unknown_category_404(client):
    r = client.get("/api/competitions", params={"category": "no-such-slug"})
    assert r.status_code == 404


# ---------------- 详情 ----------------
def test_competition_detail_and_views_increment(client):
    cid = client.get("/api/competitions", params={"page_size": 1}).json()["items"][0]["id"]
    before = client.get(f"/api/competitions/{cid}").json()["views"]
    after = client.get(f"/api/competitions/{cid}").json()["views"]
    assert after == before + 1


def test_competition_detail_404(client):
    r = client.get("/api/competitions/999999")
    assert r.status_code == 404


# ---------------- 认证 ----------------
def test_auth_register_login_me_logout(client):
    u = _rand_user()
    pw = "secret123"
    r = client.post("/api/auth/register", json={"username": u, "password": pw, "email": u + "@ex.com"})
    assert r.status_code == 200
    token = r.json()["token"]
    assert token

    # /me 需登录
    me = client.get("/api/auth/me", headers=_auth_headers(token))
    assert me.status_code == 200
    assert me.json()["username"] == u

    # 登录
    login = client.post("/api/auth/login", json={"username": u, "password": pw})
    assert login.status_code == 200
    assert login.json()["token"]

    # 错误密码
    bad = client.post("/api/auth/login", json={"username": u, "password": "wrong"})
    assert bad.status_code == 401

    # 登出后 /me 失效
    lo = client.post("/api/auth/logout", headers=_auth_headers(token))
    assert lo.status_code == 200
    me2 = client.get("/api/auth/me", headers=_auth_headers(token))
    assert me2.status_code == 401


# ---------------- 收藏 ----------------
def test_favorites_flow(client):
    u = _rand_user()
    token = client.post("/api/auth/register", json={"username": u, "password": "secret123"}).json()["token"]
    h = _auth_headers(token)
    cid = client.get("/api/competitions", params={"page_size": 1}).json()["items"][0]["id"]

    add = client.post("/api/favorites", json={"competition_id": cid}, headers=h)
    assert add.status_code == 200 and add.json().get("favorited") is True

    chk = client.get(f"/api/favorites/check/{cid}", headers=h)
    assert chk.status_code == 200 and chk.json()["favorited"] is True

    lst = client.get("/api/favorites", headers=h)
    assert lst.status_code == 200 and any(it["id"] == cid for it in lst.json())

    rem = client.delete(f"/api/favorites/{cid}", headers=h)
    assert rem.status_code == 200 and rem.json().get("favorited") is False

    chk2 = client.get(f"/api/favorites/check/{cid}", headers=h)
    assert chk2.json()["favorited"] is False


def test_favorites_add_missing_competition(client):
    u = _rand_user()
    token = client.post("/api/auth/register", json={"username": u, "password": "secret123"}).json()["token"]
    r = client.post("/api/favorites", json={"competition_id": 999999}, headers=_auth_headers(token))
    assert r.status_code == 404


# ---------------- 竞赛 CRUD（需登录） ----------------
def test_competition_crud(client):
    u = _rand_user()
    token = client.post("/api/auth/register", json={"username": u, "password": "secret123"}).json()["token"]
    h = _auth_headers(token)

    # 需要一个分类 id
    cat = client.get("/api/categories").json()[0]
    slug = "test-" + "".join(random.choices(string.ascii_lowercase, k=6))
    payload = {
        "title": "测试竞赛", "slug": slug, "summary": "摘要", "description": "描述",
        "category_id": cat["id"], "organizer": "主办方", "location": "线上", "mode": "online",
        "prize": "10000元", "status": "upcoming", "tags": ["ai", "web"], "featured": True,
    }
    created = client.post("/api/competitions", json=payload, headers=h)
    assert created.status_code == 200
    cid = created.json()["id"]
    assert created.json()["title"] == "测试竞赛"

    # 更新
    upd = client.put(f"/api/competitions/{cid}", json={**payload, "title": "测试竞赛改"}, headers=h)
    assert upd.status_code == 200 and upd.json()["title"] == "测试竞赛改"

    # 删除
    dele = client.delete(f"/api/competitions/{cid}", headers=h)
    assert dele.status_code == 200
    assert client.get(f"/api/competitions/{cid}").status_code == 404


def test_create_competition_requires_auth(client):
    r = client.post("/api/competitions", json={"title": "x", "slug": "y", "status": "upcoming", "mode": "online"})
    assert r.status_code == 401


# ---------------- 限流（R3） ----------------
def test_auth_rate_limit(client):
    # 同一 IP 连续注册超过上限应返回 429
    hit_429 = False
    for i in range(12):
        r = client.post("/api/auth/register",
                        json={"username": _rand_user() + str(i), "password": "secret123"})
        if r.status_code == 429:
            hit_429 = True
            assert "Retry-After" in r.headers
            break
    assert hit_429, "认证限流未触发 429"


# ---------------- 输入校验（R4） ----------------
def test_validation_rejects_bad_competition(client):
    u = _rand_user()
    token = client.post("/api/auth/register", json={"username": u, "password": "secret123"}).json()["token"]
    h = _auth_headers(token)
    cat = client.get("/api/categories").json()[0]

    # 超长 title
    bad = client.post("/api/competitions", json={
        "title": "x" * 300, "slug": "bad1", "status": "upcoming", "mode": "online",
        "category_id": cat["id"],
    }, headers=h)
    assert bad.status_code == 422

    # 非法 mode / status
    assert client.post("/api/competitions", json={
        "title": "正常", "slug": "bad2", "status": "upcoming", "mode": "teleport",
        "category_id": cat["id"],
    }, headers=h).status_code == 422
    assert client.post("/api/competitions", json={
        "title": "正常", "slug": "bad3", "status": "weird", "mode": "online",
        "category_id": cat["id"],
    }, headers=h).status_code == 422

    # tags 超量
    assert client.post("/api/competitions", json={
        "title": "正常", "slug": "bad4", "status": "upcoming", "mode": "online",
        "category_id": cat["id"], "tags": ["t%d" % i for i in range(15)],
    }, headers=h).status_code == 422


def test_validation_rejects_bad_register(client):
    # 短密码
    assert client.post("/api/auth/register",
                       json={"username": "okuser", "password": "123"}).status_code == 422
    # 超长用户名
    assert client.post("/api/auth/register",
                       json={"username": "x" * 40, "password": "secret1"}).status_code == 422

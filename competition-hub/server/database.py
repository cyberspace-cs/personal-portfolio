"""竞赛信息聚合平台 · 数据库初始化与连接管理
FastAPI + SQLite（原生 sqlite3，零额外 ORM 依赖，与仓库内 shuati-coach 架构一致）
"""
import sqlite3
import os
import json
import re
import logging

logger = logging.getLogger("competition_hub")

# 分类默认图标（聚合写入时自动补齐缺失分类用）
_CATEGORY_ICONS = {
    "hackathon": "🚀", "data": "📊", "algorithm": "🧮", "ctf": "🛡️",
    "ai": "🤖", "innovation": "💡", "dev": "💻", "design": "🎨",
}


def _slugify(s: str) -> str:
    """生成 URL 友好的 slug：保留中文与字母数字，其余替换为连字符。"""
    s = re.sub(r"[^\w\u4e00-\u9fff]+", "-", (s or "").strip().lower())
    return (s or "item").strip("-")[:180]


def _ensure_category(conn, slug: str, name: str = None) -> int:
    """确保分类存在，缺失时按默认图标自动创建，返回 id。"""
    row = conn.execute("SELECT id FROM categories WHERE slug=?", (slug,)).fetchone()
    if row:
        return row["id"]
    icon = _CATEGORY_ICONS.get(slug, "🏷️")
    conn.execute(
        "INSERT INTO categories (name, slug, icon, description, sort_order) VALUES (?,?,?,?,?)",
        (name or slug, slug, icon, "", 99),
    )
    return conn.execute("SELECT id FROM categories WHERE slug=?", (slug,)).fetchone()["id"]


def import_competitions(rows: list) -> dict:
    """幂等写入聚合结果：按 slug 去重，已存在则更新字段，返回统计。"""
    conn = get_db()
    stats = {"created": 0, "updated": 0, "skipped": 0, "failed": 0}
    for r in rows:
        try:
            slug = r.get("slug") or _slugify(r.get("title", ""))
            if not slug:
                stats["failed"] += 1
                continue
            cat_id = _ensure_category(conn, r.get("category_slug") or "hackathon", r.get("category_name"))
            tags_json = json.dumps(r.get("tags") or [], ensure_ascii=False)
            vals = (
                r.get("title", ""), slug, r.get("summary", ""), r.get("description", ""),
                cat_id, r.get("organizer", ""), r.get("location", ""), r.get("mode", "offline"),
                r.get("prize", ""), int(r.get("prize_amount") or 0), r.get("status", "upcoming"),
                r.get("start_date"), r.get("end_date"), r.get("reg_deadline"), tags_json,
                r.get("cover", ""), r.get("source_url", ""), r.get("source", ""),
                r.get("image", ""),
                1 if r.get("featured") else 0,
            )
            existing = conn.execute("SELECT id FROM competitions WHERE slug=?", (slug,)).fetchone()
            if existing:
                conn.execute(
                    """UPDATE competitions SET title=?,slug=?,summary=?,description=?,category_id=?,
                       organizer=?,location=?,mode=?,prize=?,prize_amount=?,status=?,start_date=?,
                       end_date=?,reg_deadline=?,tags=?,cover=?,source_url=?,source=?,image=?,featured=?,updated_at=CURRENT_TIMESTAMP
                       WHERE slug=?""",
                    vals + (slug,),
                )
                stats["updated"] += 1
            else:
                conn.execute(
                    """INSERT INTO competitions
                       (title,slug,summary,description,category_id,organizer,location,mode,prize,prize_amount,
                        status,start_date,end_date,reg_deadline,tags,cover,source_url,source,image,featured)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    vals,
                )
                stats["created"] += 1
        except Exception:
            logger.exception("聚合写入失败: %s", r.get("title"))
            stats["failed"] += 1
    conn.commit()
    conn.close()
    return stats

# 数据库文件目录：默认放在 server/data 下，可通过环境变量 DB_DIR 覆盖
DB_DIR = os.getenv("DB_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"))
DB_PATH = os.path.join(DB_DIR, os.getenv("DB_NAME", "competition.db"))
os.makedirs(DB_DIR, exist_ok=True)


def get_db():
    """获取一个数据库连接（启用 WAL + 外键约束）"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """初始化全部数据表（幂等，可重复执行）"""
    conn = get_db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS categories (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            slug        TEXT UNIQUE NOT NULL,
            icon        TEXT DEFAULT '',
            description TEXT DEFAULT '',
            sort_order  INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS competitions (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            title         TEXT NOT NULL,
            slug          TEXT UNIQUE NOT NULL,
            summary       TEXT DEFAULT '',
            description   TEXT DEFAULT '',
            category_id   INTEGER,
            organizer     TEXT DEFAULT '',
            location      TEXT DEFAULT '',
            mode          TEXT DEFAULT 'offline',   -- online / offline / hybrid
            prize         TEXT DEFAULT '',
            prize_amount  INTEGER DEFAULT 0,
            status        TEXT DEFAULT 'upcoming',  -- upcoming / ongoing / ended
            start_date    TEXT,
            end_date      TEXT,
            reg_deadline  TEXT,
            tags          TEXT DEFAULT '[]',         -- JSON 数组
            cover         TEXT DEFAULT '',
            source_url    TEXT DEFAULT '',
            featured      INTEGER DEFAULT 0,
            views         INTEGER DEFAULT 0,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        );

        CREATE TABLE IF NOT EXISTS tags (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS competition_tags (
            competition_id INTEGER NOT NULL,
            tag_id         INTEGER NOT NULL,
            PRIMARY KEY (competition_id, tag_id),
            FOREIGN KEY (competition_id) REFERENCES competitions(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS users (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            username     TEXT UNIQUE NOT NULL,
            email        TEXT DEFAULT '',
            password_hash TEXT NOT NULL,
            avatar       TEXT DEFAULT '',
            role         TEXT DEFAULT 'user',   -- admin / user
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS auth_tokens (
            token      TEXT PRIMARY KEY,
            user_id    INTEGER NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS favorites (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL,
            competition_id INTEGER NOT NULL,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (user_id, competition_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (competition_id) REFERENCES competitions(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_competitions_category ON competitions(category_id);
        CREATE INDEX IF NOT EXISTS idx_competitions_status   ON competitions(status);
        CREATE INDEX IF NOT EXISTS idx_competitions_featured ON competitions(featured);
        CREATE INDEX IF NOT EXISTS idx_favorites_user        ON favorites(user_id);
        """
    )
    conn.commit()
    # 迁移：聚合来源字段（幂等，兼容旧库）
    _cols = [r["name"] for r in conn.execute("PRAGMA table_info(competitions)").fetchall()]
    if "source" not in _cols:
        conn.execute("ALTER TABLE competitions ADD COLUMN source TEXT DEFAULT ''")
        conn.commit()
    # 迁移：官网横幅图字段（幂等，兼容旧库）
    _cols = [r["name"] for r in conn.execute("PRAGMA table_info(competitions)").fetchall()]
    if "image" not in _cols:
        conn.execute("ALTER TABLE competitions ADD COLUMN image TEXT DEFAULT ''")
        conn.commit()
    conn.close()

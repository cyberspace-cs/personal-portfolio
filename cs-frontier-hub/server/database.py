"""数据库初始化、连接管理与种子数据写入。

前沿 CS / AI 知识聚合平台 —— 数据访问层。
参考 shuati-coach 的 sqlite3 + Row + WAL 模式，封装常用读写函数。
"""
import sqlite3
import os

DB_DIR = os.getenv("DB_DIR", os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(DB_DIR, "frontier.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS categories (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    slug        TEXT UNIQUE NOT NULL,
    icon        TEXT NOT NULL DEFAULT 'sparkles',
    description TEXT NOT NULL DEFAULT '',
    sort_order  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS tags (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    slug TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS items (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    title        TEXT NOT NULL,
    slug         TEXT UNIQUE NOT NULL,
    summary      TEXT NOT NULL DEFAULT '',
    content      TEXT NOT NULL DEFAULT '',
    category_id  INTEGER,
    source_type  TEXT NOT NULL DEFAULT 'repo',   -- repo|paper|blog|tool|conference|framework|product|course
    source_url   TEXT NOT NULL DEFAULT '',
    github_stars INTEGER,
    author_org   TEXT NOT NULL DEFAULT '',
    language     TEXT NOT NULL DEFAULT '',
    status       TEXT NOT NULL DEFAULT 'active', -- active|trending|archived
    featured     INTEGER NOT NULL DEFAULT 0,
    views        INTEGER NOT NULL DEFAULT 0,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE TABLE IF NOT EXISTS item_tags (
    item_id INTEGER NOT NULL,
    tag_id  INTEGER NOT NULL,
    PRIMARY KEY (item_id, tag_id),
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id)  REFERENCES tags(id)  ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sessions (
    id         TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS favorites (
    session_id TEXT NOT NULL,
    item_id    INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (session_id, item_id),
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id)    REFERENCES items(id)    ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_items_category     ON items(category_id);
CREATE INDEX IF NOT EXISTS idx_items_source_type  ON items(source_type);
CREATE INDEX IF NOT EXISTS idx_items_status       ON items(status);
CREATE INDEX IF NOT EXISTS idx_items_featured     ON items(featured);
CREATE INDEX IF NOT EXISTS idx_items_title        ON items(title);
CREATE INDEX IF NOT EXISTS idx_item_tags_tag      ON item_tags(tag_id);
CREATE INDEX IF NOT EXISTS idx_item_tags_item     ON item_tags(item_id);
"""


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    conn = get_db()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def _slug(text: str) -> str:
    import re
    s = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    s = re.sub(r"[\s_-]+", "-", s)
    return s or "item"


def insert_category(name, slug, icon, description, sort_order):
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO categories (name, slug, icon, description, sort_order) VALUES (?,?,?,?,?) "
        "ON CONFLICT(slug) DO UPDATE SET name=excluded.name, icon=excluded.icon, "
        "description=excluded.description, sort_order=excluded.sort_order",
        (name, slug, icon, description, sort_order),
    )
    cid = cur.lastrowid
    conn.commit()
    conn.close()
    return cid


def get_category_by_slug(slug):
    conn = get_db()
    row = conn.execute("SELECT id FROM categories WHERE slug=?", (slug,)).fetchone()
    conn.close()
    return dict(row) if row else None


def ensure_tag_conn(conn, name):
    slug = _slug(name)
    row = conn.execute("SELECT id FROM tags WHERE slug=?", (slug,)).fetchone()
    if row:
        return row["id"]
    cur = conn.execute("INSERT INTO tags (name, slug) VALUES (?,?)", (name, slug))
    return cur.lastrowid


def insert_item(data: dict, tags: list):
    conn = get_db()
    cur = conn.execute(
        """INSERT INTO items
           (title, slug, summary, content, category_id, source_type, source_url,
            github_stars, author_org, language, status, featured)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            data["title"], data["slug"], data.get("summary", ""),
            data.get("content", ""), data.get("category_id"),
            data.get("source_type", "repo"), data.get("source_url", ""),
            data.get("github_stars"), data.get("author_org", ""),
            data.get("language", ""), data.get("status", "active"),
            int(bool(data.get("featured", False))),
        ),
    )
    iid = cur.lastrowid
    for t in tags:
        tid = ensure_tag_conn(conn, t)
        conn.execute("INSERT OR IGNORE INTO item_tags (item_id, tag_id) VALUES (?,?)", (iid, tid))
    conn.commit()
    conn.close()
    return iid


def count_items():
    conn = get_db()
    n = conn.execute("SELECT COUNT(*) AS c FROM items").fetchone()["c"]
    conn.close()
    return n

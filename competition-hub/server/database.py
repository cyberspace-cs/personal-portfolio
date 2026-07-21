"""竞赛信息聚合平台 · 数据库初始化与连接管理
FastAPI + SQLite（原生 sqlite3，零额外 ORM 依赖，与仓库内 shuati-coach 架构一致）
"""
import sqlite3
import os

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
    conn.close()

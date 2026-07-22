"""数据库初始化与连接管理"""
import sqlite3
import os

DB_DIR = os.getenv("DB_DIR", os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(DB_DIR, "coach.db")


def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """初始化数据库表"""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cat TEXT NOT NULL DEFAULT '',
            src TEXT NOT NULL DEFAULT '',
            type TEXT NOT NULL DEFAULT '单选题',
            stem TEXT NOT NULL,
            opts TEXT NOT NULL,
            answer TEXT NOT NULL,
            explain TEXT NOT NULL DEFAULT '',
            topic TEXT NOT NULL DEFAULT '',
            difficulty TEXT NOT NULL DEFAULT 'medium'
        );

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS quiz_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            cat TEXT NOT NULL DEFAULT '',
            total INTEGER NOT NULL DEFAULT 0,
            correct INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS wrong_book (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            error_count INTEGER NOT NULL DEFAULT 1,
            last_error_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (question_id) REFERENCES questions(id),
            UNIQUE(user_id, question_id)
        );

        CREATE TABLE IF NOT EXISTS daily_streaks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            check_date TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, check_date)
        );

        CREATE TABLE IF NOT EXISTS exam_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            exam_type TEXT NOT NULL DEFAULT '',
            total INTEGER NOT NULL DEFAULT 0,
            correct INTEGER NOT NULL DEFAULT 0,
            duration INTEGER NOT NULL DEFAULT 0,
            time_used TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        -- 学习计划：每个用户仅一条 is_active=1（AI 生成的周/阶段计划）
        CREATE TABLE IF NOT EXISTS study_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            cat TEXT NOT NULL DEFAULT '',
            plan_json TEXT NOT NULL,
            week_start TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        -- 题库版本：每次自动化更新落一条记录，支持审计与回滚
        CREATE TABLE IF NOT EXISTS question_bank_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version INTEGER NOT NULL,
            count INTEGER NOT NULL DEFAULT 0,
            sources_json TEXT NOT NULL DEFAULT '{}',
            summary TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'draft',
            checksum TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_questions_cat ON questions(cat);
        CREATE INDEX IF NOT EXISTS idx_quiz_records_user ON quiz_records(user_id);
        CREATE INDEX IF NOT EXISTS idx_wrong_book_user ON wrong_book(user_id);
        CREATE INDEX IF NOT EXISTS idx_daily_streaks_user ON daily_streaks(user_id);
        CREATE INDEX IF NOT EXISTS idx_exam_records_user ON exam_records(user_id);
        CREATE INDEX IF NOT EXISTS idx_study_plans_user_active ON study_plans(user_id, is_active);
        CREATE INDEX IF NOT EXISTS idx_wrong_book_qid ON wrong_book(question_id);
        CREATE INDEX IF NOT EXISTS idx_quiz_records_created ON quiz_records(created_at);
        CREATE INDEX IF NOT EXISTS idx_bank_versions_status ON question_bank_versions(status);
    """)
    conn.commit()
    conn.close()


def record_bank_version(version: int, count: int, sources: dict, summary: str, status: str, checksum: str) -> int:
    """写入一条题库版本记录，返回新行 id。"""
    import json as _json
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO question_bank_versions (version, count, sources_json, summary, status, checksum) VALUES (?,?,?,?,?,?)",
        (version, count, _json.dumps(sources, ensure_ascii=False), summary, status, checksum),
    )
    conn.commit()
    row_id = cur.lastrowid
    conn.close()
    return row_id


def get_active_study_plan(user_id: int) -> dict | None:
    """读取用户当前活跃学习计划（is_active=1）。"""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM study_plans WHERE user_id=? AND is_active=1 ORDER BY id DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def save_study_plan(user_id: int, cat: str, plan_json: str, week_start: str) -> int:
    """UPSERT 当前活跃计划：先把旧计划置为非活跃，再插入新计划。"""
    conn = get_db()
    conn.execute("UPDATE study_plans SET is_active=0 WHERE user_id=? AND is_active=1", (user_id,))
    cur = conn.execute(
        "INSERT INTO study_plans (user_id, cat, plan_json, week_start, is_active) VALUES (?,?,?,?,1)",
        (user_id, cat, plan_json, week_start),
    )
    conn.commit()
    row_id = cur.lastrowid
    conn.close()
    return row_id
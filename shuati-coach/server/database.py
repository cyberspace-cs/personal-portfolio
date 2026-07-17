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

        CREATE INDEX IF NOT EXISTS idx_questions_cat ON questions(cat);
        CREATE INDEX IF NOT EXISTS idx_quiz_records_user ON quiz_records(user_id);
        CREATE INDEX IF NOT EXISTS idx_wrong_book_user ON wrong_book(user_id);
        CREATE INDEX IF NOT EXISTS idx_daily_streaks_user ON daily_streaks(user_id);
        CREATE INDEX IF NOT EXISTS idx_exam_records_user ON exam_records(user_id);
    """)
    conn.commit()
    conn.close()
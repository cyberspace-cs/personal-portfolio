"""数据库初始化与连接管理"""
import sqlite3
import os

DB_DIR = os.getenv("DB_DIR", os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(DB_DIR, "coach.db")


def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=15000")
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

        -- 逐题作答明细：支撑薄弱知识点知识图谱诊断 / 自适应计划 / 自适应考场
        CREATE TABLE IF NOT EXISTS quiz_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            topic TEXT NOT NULL DEFAULT '',
            cat TEXT NOT NULL DEFAULT '',
            correct INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (question_id) REFERENCES questions(id)
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
        CREATE INDEX IF NOT EXISTS idx_quiz_attempts_user ON quiz_attempts(user_id);
        CREATE INDEX IF NOT EXISTS idx_quiz_attempts_qid ON quiz_attempts(question_id);
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


def add_quiz_attempt(user_id: int, question_id: int, topic: str, cat: str, correct: int) -> None:
    """记录一条逐题作答明细（弱项诊断 / 知识图谱 / 自适应的数据底座）。匿名用户跳过。"""
    if user_id is None:
        return
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO quiz_attempts (user_id, question_id, topic, cat, correct) VALUES (?,?,?,?,?)",
            (user_id, question_id, topic or "", cat or "", 1 if correct else 0),
        )
        conn.commit()
    finally:
        conn.close()


def add_quiz_attempt_batch(user_id: int, items: list) -> None:
    """批量记录逐题作答：items=[{question_id, topic, cat, correct}]。"""
    if user_id is None or not items:
        return
    conn = get_db()
    try:
        conn.executemany(
            "INSERT INTO quiz_attempts (user_id, question_id, topic, cat, correct) VALUES (?,?,?,?,?)",
            [(user_id, it.get("question_id"), it.get("topic") or "", it.get("cat") or "", 1 if it.get("correct") else 0) for it in items],
        )
        conn.commit()
    finally:
        conn.close()


def get_topic_mastery(user_id: int) -> dict:
    """基于逐题作答明细，计算每个知识点的 总次数 / 正确数 / 掌握度。无记录返回空 dict。"""
    conn = get_db()
    rows = conn.execute(
        "SELECT topic, COUNT(*) AS total, SUM(correct) AS correct "
        "FROM quiz_attempts WHERE user_id=? GROUP BY topic",
        (user_id,),
    ).fetchall()
    conn.close()
    out = {}
    for r in rows:
        total = r["total"] or 0
        correct = r["correct"] or 0
        out[r["topic"]] = {
            "total": total,
            "correct": correct,
            "mastery": round(correct / total * 100) if total else 0,
        }
    return out


def compute_profile(user_id: int) -> dict:
    """计算用户成长画像：经验值 / 等级 / 段位 / 徽章 / 准确率。"""
    conn = get_db()
    # 连续打卡
    streak_row = conn.execute(
        "SELECT COUNT(*) AS c FROM daily_streaks WHERE user_id=?", (user_id,)
    ).fetchone()
    streak = streak_row["c"] if streak_row else 0
    # 刷题总量 / 正确量
    qr = conn.execute(
        "SELECT COALESCE(SUM(total),0) AS total, COALESCE(SUM(correct),0) AS correct "
        "FROM quiz_records WHERE user_id=?", (user_id,)
    ).fetchone()
    total = qr["total"] or 0
    correct = qr["correct"] or 0
    # 错题本规模
    wb = conn.execute("SELECT COUNT(*) AS c FROM wrong_book WHERE user_id=?", (user_id,)).fetchone()
    wrong = wb["c"] if wb else 0
    # 模拟考场次数
    ex = conn.execute("SELECT COUNT(*) AS c FROM exam_records WHERE user_id=?", (user_id,)).fetchone()
    exams = ex["c"] if ex else 0
    conn.close()

    accuracy = round(correct / total * 100) if total else 0
    exp = streak * 10 + total * 2 + correct * 1 + wrong * 1 + exams * 15

    # 等级阶梯（每级所需经验递增）
    levels = [
        (0, "萌新备考生"), (120, "入门刷题手"), (320, "进阶打怪人"),
        (650, "题海战术师"), (1100, "考点掌控者"), (1700, "冲刺王者"), (2500, "上岸传说"),
    ]
    cur_level = 0
    next_exp = None
    level_name = levels[0][1]
    for i, (thr, name) in enumerate(levels):
        if exp >= thr:
            cur_level = i + 1
            level_name = name
            next_exp = levels[i + 1][0] if i + 1 < len(levels) else None
        else:
            break
    # 本级进度
    if next_exp is None:
        progress = 100
        cur_exp = exp
        span = 1
    else:
        prev = levels[cur_level - 1][0] if cur_level > 0 else 0
        span = next_exp - prev
        cur_exp = exp - prev
        progress = round(cur_exp / span * 100) if span else 100

    badges = []
    if streak >= 3: badges.append({"name": "连续打卡 3 天", "icon": "🔥"})
    if streak >= 7: badges.append({"name": "连续打卡 7 天", "icon": "⚡"})
    if total >= 50: badges.append({"name": "刷题 50+", "icon": "📚"})
    if accuracy >= 80 and total >= 20: badges.append({"name": "正确率 80%+", "icon": "🎯"})
    if wrong >= 10: badges.append({"name": "错题复盘 10+", "icon": "🧠"})
    if exams >= 1: badges.append({"name": "完成模拟考", "icon": "🏟️"})
    if exp >= 2500: badges.append({"name": "上岸传说", "icon": "👑"})

    return {
        "user_id": user_id, "exp": exp, "level": cur_level, "level_name": level_name,
        "cur_exp": cur_exp, "next_exp": next_exp, "progress": progress,
        "streak": streak, "total": total, "correct": correct, "wrong": wrong,
        "exams": exams, "accuracy": accuracy, "badges": badges,
    }
import sqlite3
from datetime import datetime, date
from contextlib import contextmanager

DB_PATH = "bot.db"


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                username    TEXT,
                first_name  TEXT,
                is_premium  INTEGER DEFAULT 0,
                premium_until TEXT,
                msgs_today  INTEGER DEFAULT 0,
                msgs_total  INTEGER DEFAULT 0,
                last_msg_date TEXT,
                created_at  TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS messages (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER,
                role        TEXT,
                content     TEXT,
                created_at  TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
        """)


def get_or_create_user(user_id: int, username: str, first_name: str) -> sqlite3.Row:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if not row:
            conn.execute(
                "INSERT INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
                (user_id, username, first_name),
            )
            row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return row


def reset_daily_if_needed(user_id: int):
    today = date.today().isoformat()
    with get_conn() as conn:
        row = conn.execute("SELECT last_msg_date FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if row and row["last_msg_date"] != today:
            conn.execute(
                "UPDATE users SET msgs_today = 0, last_msg_date = ? WHERE user_id = ?",
                (today, user_id),
            )


def increment_message_count(user_id: int):
    today = date.today().isoformat()
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET msgs_today = msgs_today + 1, msgs_total = msgs_total + 1, last_msg_date = ? WHERE user_id = ?",
            (today, user_id),
        )


def get_msg_count_today(user_id: int) -> int:
    with get_conn() as conn:
        row = conn.execute("SELECT msgs_today, last_msg_date FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if not row:
            return 0
        today = date.today().isoformat()
        return row["msgs_today"] if row["last_msg_date"] == today else 0


def is_premium(user_id: int) -> bool:
    with get_conn() as conn:
        row = conn.execute("SELECT is_premium, premium_until FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if not row or not row["is_premium"]:
            return False
        if row["premium_until"]:
            return row["premium_until"] >= date.today().isoformat()
        return True


def set_premium(user_id: int, until_date: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET is_premium = 1, premium_until = ? WHERE user_id = ?",
            (until_date, user_id),
        )


def save_message(user_id: int, role: str, content: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO messages (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content),
        )


def get_history(user_id: int, limit: int = 20) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


def get_stats() -> dict:
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        premium = conn.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1").fetchone()[0]
        msgs = conn.execute("SELECT SUM(msgs_total) FROM users").fetchone()[0] or 0
        today = date.today().isoformat()
        active_today = conn.execute(
            "SELECT COUNT(*) FROM users WHERE last_msg_date = ?", (today,)
        ).fetchone()[0]
    return {"total_users": total, "premium_users": premium, "total_msgs": msgs, "active_today": active_today}

from pathlib import Path
import sqlite3


def _legacy_db_path() -> Path:
    # 复用原 Node 后端数据库文件
    return Path(__file__).resolve().parents[2] / "data" / "elderly_monitoring.db"


def get_conn():
    conn = sqlite3.connect(_legacy_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def fetch_one(sql: str, params=()):
    with get_conn() as conn:
        row = conn.execute(sql, params).fetchone()
        return dict(row) if row else None


def fetch_all(sql: str, params=()):
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]


def execute(sql: str, params=()):
    with get_conn() as conn:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid, cur.rowcount

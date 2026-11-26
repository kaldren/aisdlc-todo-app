"""SQLite storage for tasks (stdlib sqlite3, parameterised SQL)."""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY,
    text TEXT NOT NULL,
    done INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
)
"""


@contextmanager
def connect(path: str):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as conn:
        conn.execute(SCHEMA)


def list_tasks(conn) -> list[sqlite3.Row]:
    return conn.execute("SELECT id, text, done FROM tasks ORDER BY id").fetchall()


def add_task(conn, text: str) -> int:
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.execute("INSERT INTO tasks (text, created_at) VALUES (?, ?)", (text, now))
    return cur.lastrowid


def mark_done(conn, task_id: int) -> bool:
    cur = conn.execute("UPDATE tasks SET done = 1 WHERE id = ?", (task_id,))
    return cur.rowcount > 0


def delete_task(conn, task_id: int) -> bool:
    cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    return cur.rowcount > 0

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass

from timer.paths import CONFIG_DIR, DB_PATH


@dataclass(slots=True)
class TimerRow:
    id: int
    message: str
    due_ts: int
    duration_ms: int
    email_targets: str


def init_db() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS timers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL,
                due_ts INTEGER NOT NULL,
                duration_ms INTEGER NOT NULL DEFAULT 0,
                email_targets TEXT NOT NULL DEFAULT '',
                created_ts INTEGER NOT NULL,
                updated_ts INTEGER NOT NULL
            )
            """
        )
        columns = {
            str(row[1]) for row in conn.execute("PRAGMA table_info(timers)").fetchall()
        }
        if "email_targets" not in columns:
            conn.execute(
                "ALTER TABLE timers ADD COLUMN email_targets TEXT NOT NULL DEFAULT ''"
            )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_timers_due_ts ON timers(due_ts)")


def add_timer(
    message: str, due_ts: int, duration_ms: int = 0, email_targets: str = ""
) -> int:
    now = int(time.time())
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            """
            INSERT INTO timers(message, due_ts, duration_ms, email_targets, created_ts, updated_ts)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (message, due_ts, duration_ms, email_targets, now, now),
        )
        row_id = cur.lastrowid
        if row_id is None:
            raise RuntimeError("Failed to insert timer row.")
        return int(row_id)


def delete_timer(timer_id: int) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("DELETE FROM timers WHERE id = ?", (timer_id,))
        return cur.rowcount > 0


def list_timers() -> list[TimerRow]:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "SELECT id, message, due_ts, duration_ms, email_targets FROM timers ORDER BY due_ts ASC"
        )
        return [TimerRow(*row) for row in cur.fetchall()]


def next_due_ts() -> int | None:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("SELECT due_ts FROM timers ORDER BY due_ts ASC LIMIT 1")
        row = cur.fetchone()
        return None if row is None else int(row[0])


def due_timers(now_ts: int) -> list[TimerRow]:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "SELECT id, message, due_ts, duration_ms, email_targets FROM timers WHERE due_ts <= ? ORDER BY due_ts ASC",
            (now_ts,),
        )
        return [TimerRow(*row) for row in cur.fetchall()]


def shift_timer(timer_id: int, delta_seconds: int) -> bool:
    now = int(time.time())
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            """
            UPDATE timers
            SET due_ts = due_ts + ?, updated_ts = ?
            WHERE id = ?
            """,
            (delta_seconds, now, timer_id),
        )
        return cur.rowcount > 0

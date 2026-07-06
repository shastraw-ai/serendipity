"""SQLite persistence (stdlib) for interaction history and interests.

A fresh connection per call keeps this thread-safe under FastAPI's threadpool without
any global locking — fine at this scale.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

from .config import settings

DEFAULT_INTERESTS = ["Technology", "Finance"]


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill TEXT NOT NULL,
                title TEXT NOT NULL,
                output TEXT NOT NULL,
                steps TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS interests (
                user_id TEXT PRIMARY KEY,
                items TEXT NOT NULL
            );
            """
        )


def save_interaction(skill: str, title: str, output: str, steps: list[dict[str, Any]]) -> int:
    created_at = datetime.now(timezone.utc).isoformat()
    with _conn() as conn:
        cur = conn.execute(
            "INSERT INTO interactions (skill, title, output, steps, created_at) VALUES (?, ?, ?, ?, ?)",
            (skill, title, output, json.dumps(steps), created_at),
        )
        return int(cur.lastrowid)


def skills_run_since(cutoff_iso: str) -> set[str]:
    """Names of skills with at least one interaction at/after cutoff_iso (UTC ISO-8601)."""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT skill FROM interactions WHERE created_at >= ?",
            (cutoff_iso,),
        ).fetchall()
    return {r["skill"] for r in rows}


def list_interactions(limit: int = 50) -> list[dict[str, Any]]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT id, skill, title, created_at FROM interactions ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_interaction(interaction_id: int) -> dict[str, Any] | None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM interactions WHERE id = ?", (interaction_id,)
        ).fetchone()
    if row is None:
        return None
    data = dict(row)
    data["steps"] = json.loads(data["steps"])
    return data


def get_interests(user_id: str) -> list[str]:
    with _conn() as conn:
        row = conn.execute(
            "SELECT items FROM interests WHERE user_id = ?", (user_id,)
        ).fetchone()
    if row is None:
        return list(DEFAULT_INTERESTS)
    return json.loads(row["items"])


def set_interests(user_id: str, items: list[str]) -> list[str]:
    cleaned = [s.strip() for s in items if s and s.strip()]
    with _conn() as conn:
        conn.execute(
            "INSERT INTO interests (user_id, items) VALUES (?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET items = excluded.items",
            (user_id, json.dumps(cleaned)),
        )
    return cleaned

"""
audit/logger.py
===============
SQLite-backed audit logger for Argus.

Three tables:
  plans        — every capture_plan() call
  delegations  — every delegate() call
  invocations  — every invoke() call (ALLOWED / BLOCKED / EXPIRED / ERROR)

The DB file is placed at <project_root>/audit.db so it is shared across
all processes (coordinator + sub-agents) running concurrently.
"""

import os
import json
import time
import sqlite3
from datetime import datetime, timezone
from typing import List, Optional

# ── resolve DB path relative to project root ──────────────────────────
_HERE    = os.path.dirname(os.path.abspath(__file__))
_ROOT    = os.path.dirname(_HERE)
DB_PATH  = os.environ.get("ARGUS_DB", os.path.join(_ROOT, "audit.db"))

# SQLite WAL mode lets multiple processes write concurrently
_PRAGMAS = "PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS plans (
    plan_id        TEXT    PRIMARY KEY,
    timestamp      TEXT    NOT NULL,
    description    TEXT,
    declared_tools TEXT,          -- JSON array
    user_email     TEXT,
    coordinator    TEXT
);

CREATE TABLE IF NOT EXISTS delegations (
    delegation_id  TEXT    PRIMARY KEY,
    plan_id        TEXT    NOT NULL,
    agent_id       TEXT    NOT NULL,
    scope          TEXT    NOT NULL,   -- JSON array
    ttl_seconds    INTEGER NOT NULL,
    issued_by      TEXT    NOT NULL,
    issued_at      TEXT    NOT NULL,
    expires_at     TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS invocations (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp      TEXT    NOT NULL,
    agent_id       TEXT    NOT NULL,
    tool_name      TEXT    NOT NULL,
    args           TEXT,               -- JSON object
    status         TEXT    NOT NULL,   -- ALLOWED | BLOCKED | EXPIRED | ERROR
    reason         TEXT,
    plan_id        TEXT,
    delegation_id  TEXT,
    scope          TEXT,               -- JSON array
    ttl_remaining  REAL
);
"""


class AuditLogger:
    """Thread-safe, multi-process SQLite audit logger."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.environ.get("ARGUS_DB", os.path.join(_ROOT, "audit.db"))
        self._init_db()

    # ── schema bootstrap ──────────────────────────────────────────────
    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.executescript(_PRAGMAS + _SCHEMA)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # ── public write methods ──────────────────────────────────────────

    def log_plan(
        self,
        plan_id:     str,
        description: str,
        tools:       List[str],
        user_email:  str,
        coordinator: str,
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO plans VALUES (?,?,?,?,?,?)",
                (plan_id, self._now(), description, json.dumps(tools), user_email, coordinator),
            )

    def log_delegation(
        self,
        delegation_id: str,
        plan_id:       str,
        agent_id:      str,
        scope:         List[str],
        ttl_seconds:   int,
        issued_by:     str,
    ) -> None:
        issued_ts  = time.time()
        expires_ts = issued_ts + ttl_seconds
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO delegations VALUES (?,?,?,?,?,?,?,?)",
                (
                    delegation_id, plan_id, agent_id, json.dumps(scope), ttl_seconds, issued_by,
                    datetime.fromtimestamp(issued_ts,  timezone.utc).isoformat(),
                    datetime.fromtimestamp(expires_ts, timezone.utc).isoformat(),
                ),
            )

    def log_invoke(
        self,
        agent_id:      str,
        tool_name:     str,
        args:          dict,
        status:        str,       # ALLOWED | BLOCKED | EXPIRED | ERROR
        reason:        str,
        plan_id:       Optional[str],
        delegation_id: Optional[str],
        scope:         List[str],
        ttl_remaining: float,
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO invocations
                   (timestamp,agent_id,tool_name,args,status,reason,
                    plan_id,delegation_id,scope,ttl_remaining)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    self._now(), agent_id, tool_name, json.dumps(args),
                    status, reason, plan_id, delegation_id,
                    json.dumps(scope), round(ttl_remaining, 2),
                ),
            )

    # ── read helpers used by the dashboard ───────────────────────────

    def get_plans(self) -> List[dict]:
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM plans ORDER BY timestamp DESC").fetchall()
        return [dict(r) for r in rows]

    def get_delegations(self) -> List[dict]:
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM delegations ORDER BY issued_at DESC").fetchall()
        return [dict(r) for r in rows]

    def get_invocations(self) -> List[dict]:
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM invocations ORDER BY timestamp DESC").fetchall()
        return [dict(r) for r in rows]

    def get_stats(self) -> dict:
        with self._conn() as conn:
            total   = conn.execute("SELECT COUNT(*) FROM invocations").fetchone()[0]
            allowed = conn.execute("SELECT COUNT(*) FROM invocations WHERE status='ALLOWED'").fetchone()[0]
            blocked = conn.execute("SELECT COUNT(*) FROM invocations WHERE status='BLOCKED'").fetchone()[0]
            expired = conn.execute("SELECT COUNT(*) FROM invocations WHERE status='EXPIRED'").fetchone()[0]
        return {"total": total, "allowed": allowed, "blocked": blocked, "expired": expired}

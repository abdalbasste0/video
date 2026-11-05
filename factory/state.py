"""Shared queue + status store (SQLite). Survives crashes → enables resume.

Video status lifecycle:
    QUEUED → IN_PROGRESS → PENDING_APPROVAL → (APPROVED → PUBLISHING → PUBLISHED)
                                           ↘ REVISING → IN_PROGRESS → PENDING_APPROVAL …
                                           ↘ REJECTED
    any → FAILED (after retries are exhausted; you are notified)

A video NEVER leaves PENDING_APPROVAL by itself. Only an owner decision recorded
in the `approvals` table (written by approval_bot after verifying the Telegram
user id) can move it forward.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any

TASK_STATUSES = ("PENDING", "RUNNING", "DONE", "FAILED")
VIDEO_STATUSES = (
    "QUEUED", "IN_PROGRESS", "PENDING_APPROVAL", "REVISING",
    "APPROVED", "PUBLISHING", "PUBLISHED", "REJECTED", "FAILED",
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS videos (
    id TEXT PRIMARY KEY,
    idea TEXT NOT NULL,
    fmt TEXT NOT NULL,
    language TEXT NOT NULL,
    status TEXT NOT NULL,
    title TEXT DEFAULT '',
    revision INTEGER DEFAULT 0,
    meta TEXT DEFAULT '{}',
    created REAL, updated REAL
);
CREATE TABLE IF NOT EXISTS tasks (
    video_id TEXT, agent TEXT, status TEXT, attempts INTEGER DEFAULT 0,
    error TEXT DEFAULT '', notes TEXT DEFAULT '', updated REAL,
    PRIMARY KEY (video_id, agent)
);
CREATE TABLE IF NOT EXISTS approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT, decision TEXT, decided_by TEXT, notes TEXT,
    render_sha256 TEXT, platforms TEXT DEFAULT '[]', at REAL
);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT, agent TEXT, level TEXT, message TEXT, at REAL
);
"""


class Store:
    def __init__(self, db_path: Path):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(db_path), check_same_thread=False, timeout=30)
        self._db.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        with self._lock:
            self._db.executescript(_SCHEMA)
            self._db.execute("PRAGMA journal_mode=WAL")
            self._db.commit()

    # ---------- helpers ----------
    def _exec(self, sql: str, args: tuple = ()) -> sqlite3.Cursor:
        with self._lock:
            cur = self._db.execute(sql, args)
            self._db.commit()
            return cur

    def _one(self, sql: str, args: tuple = ()) -> dict | None:
        with self._lock:
            row = self._db.execute(sql, args).fetchone()
            return dict(row) if row else None

    def _all(self, sql: str, args: tuple = ()) -> list[dict]:
        with self._lock:
            return [dict(r) for r in self._db.execute(sql, args).fetchall()]

    # ---------- videos ----------
    def create_video(self, idea: str, fmt: str, language: str) -> str:
        vid = time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
        now = time.time()
        self._exec(
            "INSERT INTO videos(id, idea, fmt, language, status, created, updated) VALUES (?,?,?,?,?,?,?)",
            (vid, idea, fmt, language, "QUEUED", now, now),
        )
        return vid

    def video(self, vid: str) -> dict | None:
        v = self._one("SELECT * FROM videos WHERE id=?", (vid,))
        if v:
            v["meta"] = json.loads(v.get("meta") or "{}")
        return v

    def videos(self, status: str | None = None) -> list[dict]:
        if status:
            return self._all("SELECT * FROM videos WHERE status=? ORDER BY created", (status,))
        return self._all("SELECT * FROM videos ORDER BY created DESC LIMIT 50")

    def set_video_status(self, vid: str, status: str) -> None:
        assert status in VIDEO_STATUSES, status
        if status in ("APPROVED", "PUBLISHING", "PUBLISHED"):
            # Defence in depth: these states require a recorded owner approval.
            if not self.latest_approval(vid, "APPROVE"):
                raise PermissionError(f"{vid}: cannot enter {status} without owner approval")
        self._exec("UPDATE videos SET status=?, updated=? WHERE id=?", (status, time.time(), vid))

    def update_video(self, vid: str, **fields: Any) -> None:
        if "status" in fields:
            raise ValueError("use set_video_status()")
        if "meta" in fields:
            fields["meta"] = json.dumps(fields["meta"], ensure_ascii=False)
        cols = ", ".join(f"{k}=?" for k in fields)
        self._exec(f"UPDATE videos SET {cols}, updated=? WHERE id=?", (*fields.values(), time.time(), vid))

    def merge_meta(self, vid: str, **meta: Any) -> None:
        v = self.video(vid) or {"meta": {}}
        m = v["meta"]
        m.update(meta)
        self.update_video(vid, meta=m)

    # ---------- tasks ----------
    def task(self, vid: str, agent: str) -> dict | None:
        return self._one("SELECT * FROM tasks WHERE video_id=? AND agent=?", (vid, agent))

    def tasks(self, vid: str) -> list[dict]:
        return self._all("SELECT * FROM tasks WHERE video_id=?", (vid,))

    def set_task(self, vid: str, agent: str, status: str, error: str = "", notes: str | None = None,
                 bump_attempt: bool = False) -> None:
        assert status in TASK_STATUSES, status
        t = self.task(vid, agent)
        attempts = (t["attempts"] if t else 0) + (1 if bump_attempt else 0)
        n = notes if notes is not None else (t["notes"] if t else "")
        self._exec(
            "INSERT OR REPLACE INTO tasks(video_id, agent, status, attempts, error, notes, updated) VALUES (?,?,?,?,?,?,?)",
            (vid, agent, status, attempts, error, n, time.time()),
        )

    def reset_tasks(self, vid: str, agents: list[str], notes: str = "") -> None:
        for a in agents:
            t = self.task(vid, a)
            self._exec(
                "INSERT OR REPLACE INTO tasks(video_id, agent, status, attempts, error, notes, updated) VALUES (?,?,?,?,?,?,?)",
                (vid, a, "PENDING", 0, "", notes or (t["notes"] if t else ""), time.time()),
            )

    # ---------- approvals ----------
    def record_decision(self, vid: str, decision: str, decided_by: str, notes: str = "",
                        render_sha256: str = "", platforms: list[str] | None = None) -> None:
        assert decision in ("APPROVE", "REVISE", "REJECT")
        self._exec(
            "INSERT INTO approvals(video_id, decision, decided_by, notes, render_sha256, platforms, at) VALUES (?,?,?,?,?,?,?)",
            (vid, decision, str(decided_by), notes, render_sha256, json.dumps(platforms or []), time.time()),
        )

    def latest_approval(self, vid: str, decision: str | None = None) -> dict | None:
        row = self._one("SELECT * FROM approvals WHERE video_id=? ORDER BY id DESC LIMIT 1", (vid,))
        if row and decision and row["decision"] != decision:
            return None
        if row:
            row["platforms"] = json.loads(row["platforms"] or "[]")
        return row

    # ---------- shared log ----------
    def log(self, vid: str, agent: str, message: str, level: str = "INFO") -> None:
        self._exec("INSERT INTO events(video_id, agent, level, message, at) VALUES (?,?,?,?,?)",
                   (vid, agent, level, message, time.time()))

    def events(self, vid: str, limit: int = 30) -> list[dict]:
        return self._all("SELECT * FROM events WHERE video_id=? ORDER BY id DESC LIMIT ?", (vid, limit))

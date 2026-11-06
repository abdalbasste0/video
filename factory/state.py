"""Daily job state: one JSON file per day that holds everything.

Every bot writes its output here, and the manager (bot 9) reads it to decide the next step.
The file lives at workspace/<date>/job.json, so it can be reviewed and edited by hand.
"""
from __future__ import annotations

import json
import threading
from datetime import date
from pathlib import Path
from typing import Any

from .config import settings

_lock = threading.RLock()


class Job:
    def __init__(self, day: date | None = None):
        self.day = day or settings.now().date()
        self.dir: Path = settings.day_dir(self.day)
        self.path = self.dir / "job.json"
        with _lock:
            if self.path.exists():
                self.data: dict[str, Any] = json.loads(self.path.read_text(encoding="utf-8"))
            else:
                self.data = {
                    "date": self.day.isoformat(),
                    "brief": {},          # owner instructions for today (category, topic, notes...)
                    "stages": {},         # status of each stage
                    "artifacts": {},      # outputs: topic, script, audio, media, video...
                    "approvals": {},      # owner decisions
                    "events": [],         # event log
                }
                self.save()

    # ---------------------------------------------------------------
    def save(self) -> None:
        with _lock:
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(self.path)

    def reload(self) -> None:
        with _lock:
            self.data = json.loads(self.path.read_text(encoding="utf-8"))

    def event(self, who: str, msg: str) -> None:
        with _lock:
            self.data["events"].append({"t": settings.now().strftime("%H:%M:%S"), "who": who, "msg": msg})
            self.save()

    def set_stage(self, key: str, **fields: Any) -> None:
        with _lock:
            self.data["stages"].setdefault(key, {}).update(fields)
            self.save()

    def stage(self, key: str) -> dict[str, Any]:
        return self.data["stages"].get(key, {})

    def put(self, key: str, value: Any) -> None:
        with _lock:
            self.data["artifacts"][key] = value
            self.save()

    def get(self, key: str, default: Any = None) -> Any:
        return self.data["artifacts"].get(key, default)

    @property
    def brief(self) -> dict[str, Any]:
        return self.data["brief"]

    def reset_run(self) -> None:
        """Clear the results of a previous run on the same day (keeps the owner's instructions) before a fresh start."""
        with _lock:
            self.data.update(stages={}, artifacts={}, halt_reason="")
            self.save()
        for f in (self.dir / "approvals").glob("*.json"):
            f.unlink(missing_ok=True)

    def update_brief(self, **fields: Any) -> None:
        with _lock:
            self.data["brief"].update({k: v for k, v in fields.items() if v not in (None, "")})
            self.save()


# ---------------------------------------------------------------------------
# Publishing history across days (so the bots don't repeat the same idea)
# ---------------------------------------------------------------------------
def history() -> list[dict]:
    p = settings.workspace / "history.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def add_history(entry: dict) -> None:
    with _lock:
        items = history() + [entry]
        settings.workspace.mkdir(parents=True, exist_ok=True)
        (settings.workspace / "history.json").write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# The active workday: if a run started late at night and continued past midnight, the panel and approvals
# keep following the same day instead of jumping to a new, empty one.
# ---------------------------------------------------------------------------
def _active_file() -> Path:
    return settings.workspace / "active_day.txt"


def set_active(day: date) -> None:
    settings.workspace.mkdir(parents=True, exist_ok=True)
    _active_file().write_text(day.isoformat(), encoding="utf-8")


def clear_active() -> None:
    _active_file().unlink(missing_ok=True)


def current_job() -> "Job":
    """The job running now if there is one; otherwise today's job."""
    try:
        return Job(date.fromisoformat(_active_file().read_text(encoding="utf-8").strip()))
    except (OSError, ValueError):
        return Job()

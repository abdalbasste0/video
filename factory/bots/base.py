"""Base for every production bot (1 to 6).

Each bot splits its job into small "work units" placed on a shared board (WorkBoard).
The bot processes units one at a time, and when it falls behind schedule the manager sends a helper bot
(7 or 8), which pulls from the same board in parallel. That is how the helpers actually speed up the work.
"""
from __future__ import annotations

import threading
import time as _time
import traceback
from typing import Any, Callable

from ..log import log
from ..state import Job

MAX_RETRIES = 2


class WorkBoard:
    def __init__(self, stage: str, units: list[dict], worker: Callable[[dict], Any]):
        self.stage = stage
        self.units = units
        self.worker = worker
        self.results: dict[int, Any] = {}
        self.errors: dict[int, str] = {}
        self.attempts: dict[int, int] = {}
        self.pending: list[int] = list(range(len(units)))
        self.in_flight: set[int] = set()
        self.workers: set[str] = set()
        self._lock = threading.Lock()
        self._done = threading.Condition(self._lock)

    # -----------------------------------------------------------
    @property
    def progress(self) -> float:
        return 1.0 if not self.units else len(self.results) / len(self.units)

    def _take(self) -> int | None:
        with self._lock:
            if not self.pending:
                return None
            idx = self.pending.pop(0)
            self.in_flight.add(idx)
            return idx

    def _finish(self, idx: int, result: Any = None, error: str | None = None) -> None:
        with self._lock:
            self.in_flight.discard(idx)
            if error is None:
                self.results[idx] = result
                self.errors.pop(idx, None)
            else:
                self.attempts[idx] = self.attempts.get(idx, 0) + 1
                self.errors[idx] = error
                if self.attempts[idx] <= MAX_RETRIES:
                    self.pending.append(idx)  # retry (possibly by another bot)
            self._done.notify_all()

    def worker_loop(self, worker_name: str) -> None:
        with self._lock:
            self.workers.add(worker_name)
        while (idx := self._take()) is not None:
            unit = self.units[idx]
            log.info("%s ← unit %d/%d of stage %s", worker_name, idx + 1, len(self.units), self.stage)
            try:
                self._finish(idx, self.worker(unit))
            except Exception as e:  # noqa: BLE001 — record the error and retry
                log.error("%s failed on unit %d: %s", worker_name, idx + 1, e)
                log.debug(traceback.format_exc())
                self._finish(idx, error=f"{worker_name}: {e}")

    def wait_all(self, timeout: float | None = None) -> bool:
        end = None if timeout is None else _time.monotonic() + timeout
        with self._lock:
            while self.pending or self.in_flight:
                remaining = None if end is None else end - _time.monotonic()
                if remaining is not None and remaining <= 0:
                    return False
                self._done.wait(remaining)
        return True

    def ordered_results(self) -> list[Any]:
        missing = [i for i in range(len(self.units)) if i not in self.results]
        if missing:
            details = "; ".join(self.errors.get(i, "?") for i in missing)
            raise RuntimeError(f"Stage {self.stage}: {len(missing)} units failed — {details}")
        return [self.results[i] for i in range(len(self.units))]


class ProductionBot:
    """Production bot: plan() splits the work, work() runs a single unit, finish() assembles the results."""

    name: str = "bot"
    title_ar: str = ""
    stage: str = ""

    def __init__(self) -> None:
        self.board: WorkBoard | None = None

    def owner_note(self, job: Job) -> str:
        """Instructions the owner sent to this bot specifically through the manager."""
        return job.brief.get("bot_notes", {}).get(self.name, "")

    # ---- methods to override in each bot ----
    def plan(self, job: Job) -> list[dict]:
        return [{}]

    def work(self, job: Job, unit: dict) -> Any:
        raise NotImplementedError

    def finish(self, job: Job, results: list[Any]) -> None:
        pass

    # -----------------------------------------
    def run(self, job: Job) -> None:
        units = self.plan(job)
        job.event(self.name, f"بدأ العمل على {len(units)} وحدة")
        self.board = WorkBoard(self.stage, units, lambda u: self.work(job, u))
        self.board.worker_loop(self.name)
        self.board.wait_all()
        results = self.board.ordered_results()
        self.finish(job, results)
        helpers = sorted(self.board.workers - {self.name})
        job.event(self.name, "أنهى العمل" + (f" بمساعدة {', '.join(helpers)}" if helpers else ""))

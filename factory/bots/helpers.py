"""Bots 7 and 8 — helpers on call.

They do nothing until they are called. The manager (bot 9) calls one when a stage is behind
(it has used a large share of its time budget without finishing) or when its units fail repeatedly.
The helper joins the delayed bot's work board and pulls the remaining units in parallel, so the work
finishes in less time. If the first helper is not enough, the manager sends the second one too.
"""
from __future__ import annotations

import threading

from ..log import log
from ..state import Job
from .base import ProductionBot


class HelperBot:
    def __init__(self, name: str, title_ar: str):
        self.name = name
        self.title_ar = title_ar
        self._thread: threading.Thread | None = None
        self.assisting: str | None = None

    @property
    def busy(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def assist(self, bot: ProductionBot, job: Job, reason: str) -> bool:
        if self.busy or bot.board is None:
            return False
        self.assisting = bot.name
        job.event(self.name, f"تم استدعائي لمساعدة {bot.name} — السبب: {reason}")
        log.info("🆘 %s → helping %s (%s)", self.name, bot.name, reason)

        def _run():
            bot.board.worker_loop(self.name)
            job.event(self.name, f"أنهيت مساعدة {bot.name}")
            self.assisting = None

        self._thread = threading.Thread(target=_run, name=self.name, daemon=True)
        self._thread.start()
        return True


def make_helpers() -> list[HelperBot]:
    return [
        HelperBot("bot7_helper", "البوت السابع — مساعد الطوارئ (أ)"),
        HelperBot("bot8_helper", "البوت الثامن — مساعد الطوارئ (ب)"),
    ]

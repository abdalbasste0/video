"""Per-agent logging: one file per agent per project + a global factory log."""
from __future__ import annotations

import logging
from pathlib import Path

_FMT = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def setup_root(log_file: Path) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    if any(getattr(h, "_factory", False) for h in root.handlers):
        return
    root.setLevel(logging.INFO)
    for h in (logging.StreamHandler(), logging.FileHandler(log_file, encoding="utf-8")):
        h.setFormatter(_FMT)
        h._factory = True  # type: ignore[attr-defined]
        root.addHandler(h)


def agent_logger(agent: str, project_logs_dir: Path) -> logging.Logger:
    name = f"agent.{agent}.{project_logs_dir.parent.name}"
    log = logging.getLogger(name)
    if not log.handlers:
        project_logs_dir.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(project_logs_dir / f"{agent}.log", encoding="utf-8")
        fh.setFormatter(_FMT)
        log.addHandler(fh)
    return log

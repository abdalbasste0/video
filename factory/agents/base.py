"""Common agent plumbing."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from ..config import Settings
from ..logging_setup import agent_logger
from ..project import Project
from ..state import Store


@dataclass
class QAIssue:
    agent: str          # responsible agent the task is routed back to
    reason: str
    severity: str = "error"   # error → retry; warning → reported only

    def __str__(self) -> str:
        return f"[{self.severity}] {self.agent}: {self.reason}"


@dataclass
class AgentContext:
    settings: Settings
    store: Store
    project: Project
    video: dict[str, Any]
    notes: str = ""                 # revision notes / QA error routed to this agent
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def video_id(self) -> str:
        return self.video["id"]

    @property
    def fmt(self) -> str:
        return self.video["fmt"]

    @property
    def language(self) -> str:
        return self.video["language"]

    def overrides(self, agent: str) -> dict[str, Any]:
        """Persistent per-video parameter tweaks accumulated from revision notes."""
        return (self.video.get("meta") or {}).get("overrides", {}).get(agent, {})


class BaseAgent:
    name = "base"

    def __init__(self, ctx: AgentContext):
        self.ctx = ctx
        self.s = ctx.settings
        self.p = ctx.project
        self.log: logging.Logger = agent_logger(self.name, ctx.project.dir("logs"))

    def info(self, msg: str) -> None:
        self.log.info(msg)
        self.ctx.store.log(self.ctx.video_id, self.name, msg)

    def warn(self, msg: str) -> None:
        self.log.warning(msg)
        self.ctx.store.log(self.ctx.video_id, self.name, msg, "WARNING")

    def run(self) -> Any:  # pragma: no cover - interface
        raise NotImplementedError

"""Loads config.yaml + .env and detects the runtime (Windows PC / Android Termux / Linux)."""
from __future__ import annotations

import json
import os
import platform
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

ROOT = Path(__file__).resolve().parent.parent


def detect_runtime() -> str:
    if os.environ.get("TERMUX_VERSION") or Path("/data/data/com.termux").exists():
        return "termux"
    if platform.system() == "Windows":
        return "windows"
    return "linux"


def expand(p: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(p)))


@dataclass
class Settings:
    raw: dict[str, Any]
    root: Path = ROOT
    runtime: str = "linux"
    effects: dict[str, Any] = field(default_factory=dict)

    def get(self, dotted: str, default: Any = None) -> Any:
        node: Any = self.raw
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    # ---- derived paths ----
    @property
    def projects_dir(self) -> Path:
        p = Path(self.get("runtime.projects_dir", "projects"))
        return p if p.is_absolute() else self.root / p

    @property
    def db_path(self) -> Path:
        p = Path(self.get("runtime.db_path", "factory.db"))
        return p if p.is_absolute() else self.root / p

    @property
    def drafts_dir(self) -> Path:
        if self.runtime == "windows":
            return expand(self.get("capcut.drafts_dir"))
        p = Path(self.get("capcut.phone_drafts_dir", "projects/_capcut_drafts"))
        return p if p.is_absolute() else self.root / p

    @property
    def render_backend(self) -> str:
        b = self.get("render.backend", "auto")
        if b != "auto":
            return b
        return "manual" if self.runtime == "windows" else "ffmpeg"

    def resolution(self, fmt: str) -> tuple[int, int]:
        w, h = self.get(f"resolutions.{fmt}", [1080, 1920])
        return int(w), int(h)

    @staticmethod
    def env(name: str, default: str = "") -> str:
        return os.environ.get(name, default)


def load_settings(config_path: str | Path | None = None) -> Settings:
    if load_dotenv:
        load_dotenv(ROOT / ".env")
    path = Path(config_path) if config_path else ROOT / "config.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    mode = (raw.get("runtime") or {}).get("mode", "auto")
    runtime = detect_runtime() if mode == "auto" else mode
    eff_path = ROOT / "effects_library.json"
    effects = json.loads(eff_path.read_text(encoding="utf-8")) if eff_path.exists() else {}
    return Settings(raw=raw, runtime=runtime, effects=effects)

"""Per-video project folder: /projects/{video_id}/{script,voice,assets,draft,renders,logs}."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SUBDIRS = ("script", "voice", "assets", "draft", "renders", "logs")


@dataclass
class Project:
    video_id: str
    root: Path

    @classmethod
    def open(cls, projects_dir: Path, video_id: str) -> "Project":
        p = cls(video_id, projects_dir / video_id)
        for d in SUBDIRS:
            (p.root / d).mkdir(parents=True, exist_ok=True)
        return p

    def dir(self, name: str) -> Path:
        return self.root / name

    def path(self, name: str, filename: str) -> Path:
        return self.root / name / filename

    def write_json(self, name: str, filename: str, data: Any) -> Path:
        p = self.path(name, filename)
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(p)  # atomic → crash-safe resume
        return p

    def read_json(self, name: str, filename: str, default: Any = None) -> Any:
        p = self.path(name, filename)
        if not p.exists():
            if default is not None:
                return default
            raise FileNotFoundError(p)
        return json.loads(p.read_text(encoding="utf-8"))

    # canonical artefacts shared between agents
    @property
    def script_file(self) -> Path: return self.path("script", "script.json")
    @property
    def timestamps_file(self) -> Path: return self.path("voice", "timestamps.json")
    @property
    def voice_file(self) -> Path: return self.path("voice", "voice.wav")
    @property
    def assets_file(self) -> Path: return self.path("assets", "assets.json")
    @property
    def timeline_file(self) -> Path: return self.path("draft", "timeline.json")
    @property
    def final_file(self) -> Path: return self.path("renders", "final.mp4")
    @property
    def preview_file(self) -> Path: return self.path("renders", "preview.mp4")
    @property
    def thumb_file(self) -> Path: return self.path("renders", "thumbnail.jpg")

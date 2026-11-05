"""ffmpeg / ffprobe helpers shared by the voice, editing, and QA bots."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import requests

from .log import log


def run(cmd: list[str], timeout: int = 1800) -> subprocess.CompletedProcess:
    log.debug("ffmpeg: %s", " ".join(map(str, cmd)))
    p = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, timeout=timeout)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd[0]} …\n{p.stderr[-1500:]}")
    return p


def ffmpeg(*args: str | Path, timeout: int = 1800) -> subprocess.CompletedProcess:
    return run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *args], timeout=timeout)


def probe(path: str | Path) -> dict:
    p = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path])
    return json.loads(p.stdout)


def duration(path: str | Path) -> float:
    return float(probe(path)["format"]["duration"])


def download(url: str, dest: Path, headers: dict | None = None) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, headers=headers, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
    return dest

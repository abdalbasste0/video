"""FFmpeg / FFprobe helpers shared by agents."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
FFPROBE = shutil.which("ffprobe") or "ffprobe"


class MediaError(RuntimeError):
    pass


def run(cmd: list[str], timeout: int | None = None) -> str:
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                          encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise MediaError(f"{Path(cmd[0]).name} failed ({proc.returncode}): {proc.stderr[-1500:]}")
    return proc.stdout + proc.stderr


def ffmpeg(*args: str, timeout: int | None = None) -> str:
    return run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", *args], timeout=timeout)


def probe(path: Path) -> dict:
    out = run([FFPROBE, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)])
    return json.loads(out)


def duration(path: Path) -> float:
    return float(probe(path)["format"].get("duration", 0.0))


def video_info(path: Path) -> dict:
    info = probe(path)
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    fps = 0.0
    if v and v.get("avg_frame_rate", "0/0") != "0/0":
        n, d = v["avg_frame_rate"].split("/")
        fps = float(n) / float(d) if float(d) else 0.0
    return {
        "duration": float(info["format"].get("duration", 0.0)),
        "width": int(v["width"]) if v else 0,
        "height": int(v["height"]) if v else 0,
        "fps": round(fps, 2),
        "vcodec": v.get("codec_name") if v else None,
        "has_audio": a is not None,
        "size_mb": round(int(info["format"].get("size", 0)) / 1e6, 2),
    }


def loudness(path: Path) -> float | None:
    """Integrated loudness (LUFS) via ebur128."""
    try:
        out = run([FFMPEG, "-hide_banner", "-nostats", "-i", str(path), "-filter_complex", "ebur128=peak=true",
                   "-f", "null", "-"])
    except MediaError:
        return None
    m = re.findall(r"I:\s+(-?[\d.]+)\s+LUFS", out)
    return float(m[-1]) if m else None


def mean_luma(path: Path, at: float = 0.5) -> float | None:
    """Average luma (0-255) of one frame — used by the Colorist for shot matching."""
    try:
        out = run([FFMPEG, "-hide_banner", "-ss", f"{at:.2f}", "-i", str(path), "-frames:v", "1",
                   "-vf", "scale=160:-2,signalstats,metadata=print:key=lavfi.signalstats.YAVG", "-f", "null", "-"])
    except MediaError:
        return None
    m = re.findall(r"YAVG=([\d.]+)", out)
    return float(m[-1]) if m else None


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def is_image(path: Path) -> bool:
    return path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

"""Bot 4 — media hunter: finds the right videos and images for each scene and prepares them for editing.

- stickman scenes: draws a stickman frame in the scene's pose and mood.
- stock scenes: searches Pexels videos → Pexels images → Pixabay videos → Pixabay images,
  picks a clip long enough for the scene's narration, and avoids repeating the same clip in one video.
Records the source of each clip (credits) in the job so it can go in the video description.
"""
from __future__ import annotations

import threading

import requests

from .. import stickman
from ..config import settings
from ..log import log
from ..media_tools import download
from ..state import Job
from .base import ProductionBot

PEXELS_VIDEOS = "https://api.pexels.com/videos/search"
PEXELS_PHOTOS = "https://api.pexels.com/v1/search"
PIXABAY_VIDEOS = "https://pixabay.com/api/videos/"
PIXABAY_PHOTOS = "https://pixabay.com/api/"


class MediaHunter(ProductionBot):
    name = "bot4_media_hunter"
    title_ar = "البوت الرابع — جلب الفيديوهات والصور"
    stage = "media"

    def __init__(self) -> None:
        super().__init__()
        self._used: set[str] = set()
        self._lock = threading.Lock()

    def _claim(self, key: str) -> bool:
        with self._lock:
            if key in self._used:
                return False
            self._used.add(key)
            return True

    # ------------------------------------------------------------------
    def plan(self, job: Job) -> list[dict]:
        scenes = job.get("script")["scenes"]
        audio = {a["index"]: a["duration"] for a in job.get("audio")}
        (job.dir / "media").mkdir(exist_ok=True)
        # On a redo, skip clips that were already used so the owner sees new footage
        self._used.update(job.get("media_used", []))
        return [dict(index=i, need=audio[i] + 0.5, **s) for i, s in enumerate(scenes)]

    def work(self, job: Job, unit: dict) -> dict:
        i = unit["index"]
        base = job.dir / "media" / f"scene_{i:03d}"
        if unit["visual_type"] == "stickman" or settings.dry_run:
            pose = unit.get("stickman_pose", "standing") if unit["visual_type"] == "stickman" else "standing"
            path = stickman.render(pose, unit.get("mood", "suspense"), base.with_suffix(".png"), settings.resolution, seed=i)
            return {"index": i, "kind": "image", "path": str(path), "credit": "stickman (generated)"}

        query = unit["visual_query_en"]
        for finder in (self._pexels_video, self._pexels_photo, self._pixabay_video, self._pixabay_photo):
            try:
                found = finder(query, unit["need"])
            except requests.RequestException as e:
                log.warning("%s: %s failed: %s", self.name, finder.__name__, e)
                continue
            if found:
                kind, url, credit = found
                ext = ".mp4" if kind == "video" else ".jpg"
                path = download(url, base.with_suffix(ext))
                return {"index": i, "kind": kind, "path": str(path), "credit": credit}
        # Last resort: a stickman frame instead of an empty scene
        log.warning("%s: no media found for «%s», using a stickman frame", self.name, query)
        path = stickman.render("thinking", unit.get("mood", "suspense"), base.with_suffix(".png"), settings.resolution, seed=i)
        return {"index": i, "kind": "image", "path": str(path), "credit": "stickman (fallback)"}

    def finish(self, job: Job, results: list[dict]) -> None:
        job.put("media", results)
        job.put("media_used", sorted(self._used))

    # ------------------------------------------------------------------
    @property
    def _orientation(self) -> str:
        return "portrait" if settings.video_format == "vertical" else "landscape"

    def _pexels_video(self, q: str, need: float):
        if not settings.pexels_key:
            return None
        r = requests.get(PEXELS_VIDEOS, headers={"Authorization": settings.pexels_key},
                         params={"query": q, "orientation": self._orientation, "per_page": 15}, timeout=30)
        r.raise_for_status()
        want_w, want_h = settings.resolution
        for v in sorted(r.json().get("videos", []), key=lambda v: -v.get("duration", 0)):
            if v.get("duration", 0) < min(need, 30) or not self._claim(f"pexels-v-{v['id']}"):
                continue
            files = [f for f in v["video_files"] if f.get("file_type") == "video/mp4" and f.get("width")]
            if not files:
                continue
            # The closest quality to the target resolution (without going over 4K)
            best = min(files, key=lambda f: abs(f["width"] * f["height"] - want_w * want_h))
            return "video", best["link"], f"Pexels — {v['user']['name']} ({v['url']})"
        return None

    def _pexels_photo(self, q: str, need: float):
        if not settings.pexels_key:
            return None
        r = requests.get(PEXELS_PHOTOS, headers={"Authorization": settings.pexels_key},
                         params={"query": q, "orientation": self._orientation, "per_page": 15}, timeout=30)
        r.raise_for_status()
        for p in r.json().get("photos", []):
            if self._claim(f"pexels-p-{p['id']}"):
                return "image", p["src"]["large2x"], f"Pexels — {p['photographer']} ({p['url']})"
        return None

    def _pixabay_video(self, q: str, need: float):
        if not settings.pixabay_key:
            return None
        r = requests.get(PIXABAY_VIDEOS, params={"key": settings.pixabay_key, "q": q, "per_page": 15}, timeout=30)
        r.raise_for_status()
        for h in r.json().get("hits", []):
            if h.get("duration", 0) < min(need, 30) or not self._claim(f"pixabay-v-{h['id']}"):
                continue
            vids = h["videos"]
            f = vids.get("large") if vids.get("large", {}).get("url") else vids.get("medium")
            if f and f.get("url"):
                return "video", f["url"], f"Pixabay — {h['user']} ({h['pageURL']})"
        return None

    def _pixabay_photo(self, q: str, need: float):
        if not settings.pixabay_key:
            return None
        orient = "vertical" if settings.video_format == "vertical" else "horizontal"
        r = requests.get(PIXABAY_PHOTOS, params={"key": settings.pixabay_key, "q": q, "image_type": "photo",
                                                 "orientation": orient, "per_page": 15}, timeout=30)
        r.raise_for_status()
        for h in r.json().get("hits", []):
            if self._claim(f"pixabay-p-{h['id']}"):
                return "image", h["largeImageURL"], f"Pixabay — {h['user']} ({h['pageURL']})"
        return None

"""Assets Agent — images/clips per scene, music, SFX, with a consistent naming convention:

    assets/s01_main.mp4 | s01_main.jpg     main visual of scene s01
    assets/music_01.mp3                     background music bed
    assets/sfx_whoosh.wav                   transition sound effect
"""
from __future__ import annotations

import random
import shutil
from pathlib import Path

import requests

from .. import media
from .base import BaseAgent

PALETTE = ["0x1d3557", "0x264653", "0x3a0ca3", "0x6a040f", "0x2b2d42", "0x0b525b", "0x5a189a"]
AUDIO_EXT = {".mp3", ".wav", ".m4a", ".aac", ".ogg"}
IMG_EXT = {".jpg", ".jpeg", ".png", ".webp"}
VID_EXT = {".mp4", ".mov", ".mkv", ".webm"}


class AssetsAgent(BaseAgent):
    name = "assets"

    def run(self) -> dict:
        script = self.p.read_json("script", "script.json")
        adir = self.p.dir("assets")
        w, h = self.s.resolution(self.ctx.fmt)
        provider = self.s.get("assets.provider", "pexels")
        key = self.s.env("PEXELS_API_KEY")
        lib = self.s.root / self.s.get("assets.local_dir", "library")
        local_media = sorted(p for p in (lib / "images").glob("*") if p.suffix.lower() in IMG_EXT | VID_EXT) \
            if (lib / "images").exists() else []

        scenes = {}
        for i, sc in enumerate(script["scenes"]):
            path = None
            if provider == "pexels" and key:
                try:
                    path = self._pexels(sc["search_query"], sc["id"], key, w, h, sc["duration_sec"])
                except Exception as e:
                    self.warn(f"pexels failed for {sc['id']} ({e}) → fallback")
            if path is None and local_media:
                src = local_media[i % len(local_media)]
                path = adir / f"{sc['id']}_main{src.suffix.lower()}"
                shutil.copy2(src, path)
            if path is None:
                path = self._generated(sc["id"], i, w, h)
            scenes[sc["id"]] = {"path": str(path), "kind": "image" if media.is_image(path) else "video",
                                "duration": None if media.is_image(path) else media.duration(path)}

        music = self._pick(lib / "music", AUDIO_EXT, adir / "music_01") or self._gen_music(adir / "music_01.wav")
        sfx = self._pick(lib / "sfx", AUDIO_EXT, adir / "sfx_whoosh") or self._gen_whoosh(adir / "sfx_whoosh.wav")
        data = {"scenes": scenes, "music": str(music), "sfx": {"whoosh": str(sfx)}}
        self.p.write_json("assets", "assets.json", data)
        self.info(f"assets ready: {len(scenes)} visuals, music={Path(music).name}")
        return data

    # ---------- providers ----------
    def _pexels(self, query: str, sid: str, key: str, w: int, h: int, min_dur: float) -> Path | None:
        orient = "portrait" if h > w else "landscape"
        r = requests.get("https://api.pexels.com/videos/search", headers={"Authorization": key},
                         params={"query": query, "orientation": orient, "per_page": 8}, timeout=20)
        r.raise_for_status()
        for v in r.json().get("videos", []):
            if v.get("duration", 0) < min_dur:
                continue
            files = sorted((f for f in v["video_files"] if f.get("height") and f["file_type"] == "video/mp4"),
                           key=lambda f: abs(max(f["width"], f["height"]) - max(w, h)))
            if files:
                return self._download(files[0]["link"], self.p.dir("assets") / f"{sid}_main.mp4")
        r = requests.get("https://api.pexels.com/v1/search", headers={"Authorization": key},
                         params={"query": query, "orientation": orient, "per_page": 3}, timeout=20)
        r.raise_for_status()
        photos = r.json().get("photos", [])
        if photos:
            return self._download(photos[0]["src"]["large2x"], self.p.dir("assets") / f"{sid}_main.jpg")
        return None

    @staticmethod
    def _download(url: str, out: Path) -> Path:
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(out, "wb") as f:
                for chunk in r.iter_content(1 << 16):
                    f.write(chunk)
        return out

    @staticmethod
    def _pick(folder: Path, exts: set[str], dest_stem: Path) -> Path | None:
        if not folder.exists():
            return None
        files = [p for p in folder.iterdir() if p.suffix.lower() in exts]
        if not files:
            return None
        src = random.choice(files)
        dest = dest_stem.with_suffix(src.suffix.lower())
        shutil.copy2(src, dest)
        return dest

    def _generated(self, sid: str, i: int, w: int, h: int) -> Path:
        """Offline fallback: animated-friendly gradient still."""
        out = self.p.dir("assets") / f"{sid}_main.png"
        c1, c2 = PALETTE[i % len(PALETTE)], PALETTE[(i + 3) % len(PALETTE)]
        try:
            media.ffmpeg("-f", "lavfi", "-i", f"gradients=s={w}x{h}:c0={c1}:c1={c2}:x0=0:y0=0:x1={w}:y1={h}:d=1",
                         "-frames:v", "1", str(out))
        except media.MediaError:   # FFmpeg < 6.1 has no gradients source
            media.ffmpeg("-f", "lavfi", "-i", f"color=c={c1}:s={w}x{h}:d=1", "-vf", "vignette=PI/4",
                         "-frames:v", "1", str(out))
        return out

    @staticmethod
    def _gen_music(out: Path) -> Path:
        """Offline fallback: soft ambient pad (60 s) so ducking/mixing always has a bed."""
        expr = ("0.10*sin(2*PI*220*t)*(0.6+0.4*sin(2*PI*0.25*t))+0.08*sin(2*PI*277.18*t)"
                "+0.07*sin(2*PI*329.63*t)+0.05*sin(2*PI*110*t)")
        media.ffmpeg("-f", "lavfi", "-i", f"aevalsrc={expr}:s=48000:d=60", "-ac", "2", str(out))
        return out

    @staticmethod
    def _gen_whoosh(out: Path) -> Path:
        media.ffmpeg("-f", "lavfi", "-i", "anoisesrc=d=0.45:c=pink:a=0.5:r=48000",
                     "-af", "afade=t=in:d=0.2,afade=t=out:st=0.2:d=0.25,highpass=f=400", str(out))
        return out

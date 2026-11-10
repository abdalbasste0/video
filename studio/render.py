"""
Renderer: shot JSON -> frames (Pillow) -> FFmpeg -> shot .mp4 (cached),
then all shots -> one video, then video + audio -> final .mp4.

Speed notes
- Backgrounds are drawn once per shot and only cropped/scaled per frame.
- Characters are drawn on small supersampled canvases.
- Shots render in parallel (one process per CPU core).
- Each finished shot is cached by a hash of its content: re-running only
  renders shots that changed.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from . import backgrounds as BG
from . import effects as FX
from . import rig, shots as SH
from .config import CACHE, StudioError, settings
from .text import draw_text

RENDER_VERSION = "3"  # bump to invalidate every cached shot after a drawing change


def ffmpeg_bin() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        raise StudioError("FFmpeg is not installed or not on PATH. See README 'Install FFmpeg', then run `python make.py doctor`.")
    return exe


def run(cmd: list, what: str):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise StudioError(f"FFmpeg failed while {what}.\n--- last lines ---\n" + "\n".join(r.stderr.strip().splitlines()[-8:]))
    return r


# ── one frame ─────────────────────────────────────────────────
class ShotRenderer:
    def __init__(self, shot: dict, cast: dict, lang: dict, W: int, H: int, fps: int, ss: int, on_twos: bool):
        self.shot, self.cast, self.lang = shot, cast, lang
        self.W, self.H, self.fps, self.ss, self.on_twos = W, H, fps, ss, on_twos
        bg = shot.get("bg", {"preset": "void", "mood": "night"})
        self.layers = BG.build(bg.get("preset", "void"), bg.get("mood", "night"), int(bg.get("seed", 0)), W, H)
        self.world_w = SH.WORLD_W * W  # in screen pixels at zoom 1

    def _layer_crop(self, name, cx, cy, z):
        """Crop a parallax layer for camera centre (cx, cy) in world px, zoom z."""
        img = self.layers[name]
        LW, LH = self.layers["size"]
        p = BG.PARALLAX[name]
        k = LW / self.world_w  # layer pixels per world pixel
        zl = 1 + (z - 1) * p
        ccx = self.world_w / 2 + (cx - self.world_w / 2) * p
        ccy = self.H / 2 + (cy - self.H / 2) * p
        w, h = self.W / zl, self.H / zl
        x0 = min(max(ccx - w / 2, 0), self.world_w - w)
        y0 = min(max(ccy - h / 2, 0), self.H - h)
        box = (x0 * k, y0 * k, (x0 + w) * k, (y0 + h) * k)
        return img.resize((self.W, self.H), Image.BILINEAR, box=box), (x0, y0, zl)

    def frame(self, n: int) -> Image.Image:
        W, H, fps = self.W, self.H, self.fps
        t = n / fps
        t_anim = (n // 2) * 2 / fps if self.on_twos else t   # characters on twos
        shot = self.shot
        cx, cy, z, shx, shy = SH.camera_at(shot.get("camera"), t, shot["duration"])
        cxw, cyw = cx * self.world_w + shx, cy * H + shy
        frame, _ = self._layer_crop("far", cxw, cyw, z)
        mid, _ = self._layer_crop("mid", cxw, cyw, z)
        frame.alpha_composite(mid)
        near, (x0, y0, zl) = self._layer_crop("near", cxw, cyw, z)
        frame.alpha_composite(near)
        ground_world = self.layers["ground"] * H

        lights = []
        chars = Image.new("RGBA", (W, H), (0, 0, 0, 0))   # characters get their own layer (lit separately)
        # draw actors back-to-front (smaller "depth" first)
        for actor in sorted(shot.get("actors", []), key=lambda a: a.get("depth", 0)):
            ch = self.cast.get(actor["char"], {"color": "steel"})
            pose, xf, facing, emotion = SH.actor_at(actor, t_anim, W / H)
            mouth = SH.mouth_at(shot.get("speech"), actor["char"], t_anim, fps)
            blink = rig.blink_at(actor["char"] + shot.get("id", ""), t_anim)
            hpx = actor.get("height", 0.30) * H * zl
            img, (ax, ay), info = rig.render_character(ch, pose, hpx, facing, emotion, mouth, blink, t_anim,
                                                       prop=actor.get("prop"), ss=self.ss)
            wx = xf * self.world_w
            wy = ground_world + actor.get("y_offset", 0) * H
            sx, sy = (wx - x0) * zl, (wy - y0) * zl
            chars.alpha_composite(img, (int(round(sx - ax)), int(round(sy - ay))))
            if info["prop"] and actor.get("prop") in ("flashlight", "lantern"):
                px, py, ang = info["prop"]
                lights.append((sx + px, sy + py, ang, actor["prop"]))
            if actor.get("label") and actor["label"].get("t0", 0) <= t <= actor["label"].get("t1", 1e9):
                hx, hy = info["head"]
                draw_text(chars, (sx + hx, sy + hy - info["head_r"] * 2.1), actor["label"]["text"], self.lang,
                          int(H * 0.04), fill=(255, 255, 255), stroke=4, stroke_fill=(20, 20, 28), body=True)

        fx = shot.get("fx", {})
        arr = np.asarray(frame.convert("RGB"), dtype=np.float32)
        lit, dark = FX.lighting(W, H, fx, t, lights)
        if lit is not None:
            arr *= lit
            frame_floor = max(FX.CHARACTER_MIN_LIGHT, 1 - 0.85 * dark)
        ch = np.asarray(chars, dtype=np.float32)
        a = ch[..., 3:4] / 255.0
        if a.any():
            rgb = ch[..., :3] * (np.maximum(lit, frame_floor) if lit is not None else 1.0)
            arr = arr * (1 - a) + rgb * a
        arr = FX.post(arr, fx, t)
        out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")
        if fx.get("rain"):
            FX.draw_rain(ImageDraw.Draw(out), W, H, t, float(fx.get("rain", 1)), seed=hash(shot.get("id", "")) % 1000)
        for tx in shot.get("text", []):
            if tx.get("t0", 0) <= t <= tx.get("t1", shot["duration"]):
                fade = min(1.0, (t - tx.get("t0", 0)) / 0.3, (tx.get("t1", shot["duration"]) - t) / 0.3)
                col = tuple(int(c * max(0.0, fade)) for c in tx.get("color", (255, 255, 255)))
                draw_text(out, (tx.get("x", 0.5) * W, tx.get("y", 0.5) * H), tx["text"], self.lang,
                          int(tx.get("size", 80) * H / 1080), fill=col, stroke=int(tx.get("stroke", 0)),
                          body=tx.get("body", False), max_chars=tx.get("max_chars"))
        # fade in/out
        fin, fout = shot.get("fade_in", 0), shot.get("fade_out", 0)
        k = 1.0
        if fin and t < fin:
            k = t / fin
        if fout and t > shot["duration"] - fout:
            k = min(k, (shot["duration"] - t) / fout)
        if k < 1.0:
            out = Image.fromarray((np.asarray(out, np.float32) * max(0.0, k)).astype(np.uint8))
        return out


def shot_frames(shot: dict, fps: int) -> int:
    return max(1, int(round(shot["duration"] * fps)))


def shot_hash(shot, cast, lang, vcfg) -> str:
    blob = json.dumps([RENDER_VERSION, shot, cast, lang.get("code"), lang.get("font"), vcfg], sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(blob.encode()).hexdigest()[:16]


def render_shot(shot: dict, cast: dict, lang: dict, out_path: str, vcfg: dict, threads: int = 2) -> str:
    """Render one shot to an mp4 (video only). Uses the cache when possible."""
    W, H, fps = vcfg["width"], vcfg["height"], vcfg["fps"]
    h = shot_hash(shot, cast, lang, vcfg)
    cache_file = CACHE / "shots" / f"{h}.mp4"
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if vcfg.get("cache", True) and cache_file.exists():
        shutil.copyfile(cache_file, out_path)
        return f"{shot.get('id')} (cached)"
    r = ShotRenderer(shot, cast, lang, W, H, fps, vcfg.get("supersample", 2), vcfg.get("animate_on_twos", True))
    cmd = [ffmpeg_bin(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", vcfg.get("preset", "medium"),
           "-crf", str(vcfg.get("crf", 18)), "-pix_fmt", "yuv420p", "-threads", str(threads), str(out_path)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for n in range(shot_frames(shot, fps)):
            proc.stdin.write(r.frame(n).tobytes())
        proc.stdin.close()
    except BrokenPipeError:
        pass
    err = proc.stderr.read().decode(errors="ignore")
    if proc.wait() != 0:
        raise StudioError(f"FFmpeg could not encode shot {shot.get('id')}: {err[-400:]}")
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(out_path, cache_file)
    return f"{shot.get('id')} rendered"


def _render_job(args):
    return render_shot(*args)


def render_shots(shots: list, cast: dict, lang: dict, out_dir: Path, log=print) -> list:
    """Render all shots in parallel; returns list of shot file paths in order."""
    s = settings()
    vcfg = dict(s["video"])
    vcfg["cache"] = s.get("render", {}).get("cache", True)
    workers = s.get("render", {}).get("workers", 0) or os.cpu_count() or 2
    workers = max(1, min(workers, len(shots)))
    paths = [str(Path(out_dir) / f"{sh['id']}.mp4") for sh in shots]
    jobs = [(sh, cast, lang, p, vcfg, max(1, (os.cpu_count() or 2) // workers)) for sh, p in zip(shots, paths)]
    if workers == 1:
        for j in jobs:
            log("  ✓ " + _render_job(j))
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(_render_job, j) for j in jobs]
            for f in as_completed(futs):
                log("  ✓ " + f.result())
    return paths


def concat(paths: list, out: Path) -> Path:
    lst = Path(out).with_suffix(".txt")
    lst.write_text("".join(f"file '{Path(p).resolve().as_posix()}'\n" for p in paths), encoding="utf-8")
    run([ffmpeg_bin(), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out)],
        "joining shots")
    lst.unlink(missing_ok=True)
    return Path(out)


def mux(video: Path, audio: Path, out: Path) -> Path:
    run([ffmpeg_bin(), "-y", "-loglevel", "error", "-i", str(video), "-i", str(audio), "-map", "0:v", "-map", "1:a",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out)],
        "adding the sound track")
    return Path(out)


def still(shot: dict, cast: dict, lang: dict, t: float, out_png: Path) -> Path:
    """Render a single frame as PNG (for previews / doctor / contact sheets)."""
    v = settings()["video"]
    r = ShotRenderer(shot, cast, lang, v["width"], v["height"], v["fps"], v.get("supersample", 2), False)
    r.frame(int(t * v["fps"])).save(out_png)
    return Path(out_png)

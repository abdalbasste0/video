"""Bot 5 — editor: assembles the audio, videos, and images into a polished final video.

Per scene (a work unit a helper can take over):
  - video: crop/fit to the frame + loop if too short + trim to the narration length
  - image: Ken Burns effect (slow zoom/pan)
  - burned-in Arabic subtitles (ASS/libass with proper Arabic shaping) + on-screen text
  - short fade in/out between scenes
Final assembly: join the scenes → background music with automatic ducking under the voice
→ loudness normalised to YouTube's standard (-14 LUFS) → thumbnail.
"""
from __future__ import annotations

import os
import random
import re
from pathlib import Path

from ..config import ROOT, settings
from ..media_tools import duration, ffmpeg
from ..state import Job
from .base import ProductionBot

FPS = 30
TAIL = 0.4  # breathing room after each sentence
FONT_NAME = os.environ.get("FACTORY_FONT", "DejaVu Sans")
FONTS_DIR = ROOT / "assets" / "fonts"


def _ass_time(t: float) -> str:
    h, rem = divmod(max(t, 0), 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def _clean(text: str) -> str:
    return re.sub(r"[{}\\]", "", text).replace("\n", " ").strip()


def _chunks(text: str, words_per_chunk: int) -> list[str]:
    words = _clean(text).split()
    return [" ".join(words[i:i + words_per_chunk]) for i in range(0, len(words), words_per_chunk)] or [""]


def write_ass(path: Path, narration: str, on_screen: str, total: float, size: tuple[int, int]) -> Path:
    w, h = size
    vertical = h > w
    fs = int(h * (0.045 if vertical else 0.055))
    style_common = f"{FONT_NAME},{{fs}},&H00FFFFFF,&H000000FF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,{{ol}},2"
    header = (
        "[Script Info]\nScriptType: v4.00+\n"
        f"PlayResX: {w}\nPlayResY: {h}\nWrapStyle: 0\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Sub,{style_common.format(fs=fs, ol=4)},2,60,60,{int(h * (0.18 if vertical else 0.08))},1\n"
        f"Style: Top,{style_common.format(fs=int(fs * 1.25), ol=5).replace('&H00FFFFFF', '&H0000D7FF', 1)},8,60,60,{int(h * 0.08)},1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    lines = []
    chunks = _chunks(narration, 5 if vertical else 7)
    weights = [max(len(c), 1) for c in chunks]
    speak = max(total - TAIL, 0.5)
    t = 0.0
    for c, wgt in zip(chunks, weights):
        d = speak * wgt / sum(weights)
        lines.append(f"Dialogue: 0,{_ass_time(t)},{_ass_time(t + d)},Sub,,0,0,0,,{c}")
        t += d
    if on_screen.strip():
        lines.append(f"Dialogue: 1,{_ass_time(0)},{_ass_time(total)},Top,,0,0,0,,{{\\fad(250,250)}}{_clean(on_screen)}")
    path.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")
    return path


def _escape_filter_path(p: Path) -> str:
    return str(p).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")


class Editor(ProductionBot):
    name = "bot5_editor"
    title_ar = "البوت الخامس — المونتاج وتركيب الصوت"
    stage = "edit"

    def plan(self, job: Job) -> list[dict]:
        scenes = job.get("script")["scenes"]
        audio = {a["index"]: a for a in job.get("audio")}
        media = {m["index"]: m for m in job.get("media")}
        (job.dir / "clips").mkdir(exist_ok=True)
        return [{"index": i, "scene": s, "audio": audio[i], "media": media[i]} for i, s in enumerate(scenes)]

    def work(self, job: Job, unit: dict) -> dict:
        i = unit["index"]
        w, h = settings.resolution
        total = unit["audio"]["duration"] + TAIL
        frames = int(round(total * FPS))
        clips = job.dir / "clips"
        ass = write_ass(clips / f"scene_{i:03d}.ass", unit["scene"]["narration"],
                        unit["scene"].get("on_screen_text", ""), total, (w, h))
        subs = f"subtitles='{_escape_filter_path(ass)}'"
        if FONTS_DIR.exists():
            subs += f":fontsdir='{_escape_filter_path(FONTS_DIR)}'"
        fade = f"fade=t=in:st=0:d=0.25,fade=t=out:st={max(total - 0.3, 0):.2f}:d=0.3"
        out = clips / f"scene_{i:03d}.mp4"
        media = unit["media"]

        if media["kind"] == "video":
            vin = ["-stream_loop", "-1", "-i", media["path"]]
            vf = (f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps={FPS},"
                  f"setsar=1,eq=contrast=1.05:saturation=1.08,{subs},{fade}")
        else:
            # Ken Burns: alternate between a centred zoom-in and a slow sideways pan
            zoom_in = i % 2 == 0
            z = "min(zoom+0.0009,1.18)" if zoom_in else "1.12"
            x = "iw/2-(iw/zoom/2)" if zoom_in else f"(iw-iw/zoom)*on/{max(frames, 1)}"
            vin = ["-loop", "1", "-framerate", str(FPS), "-i", media["path"]]
            vf = (f"scale={w * 2}:{h * 2}:force_original_aspect_ratio=increase,crop={w * 2}:{h * 2},"
                  f"zoompan=z='{z}':x='{x}':y='ih/2-(ih/zoom/2)':d=1:s={w}x{h}:fps={FPS},"
                  f"setsar=1,{subs},{fade}")

        ffmpeg(*vin, "-i", unit["audio"]["path"],
               "-filter_complex", f"[0:v]{vf}[v];[1:a]aresample=48000,apad=pad_dur={TAIL}[a]",
               "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}",
               "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", out)
        return {"index": i, "path": str(out), "duration": total}

    def finish(self, job: Job, results: list[dict]) -> None:
        clips = job.dir / "clips"
        concat_list = clips / "list.txt"
        concat_list.write_text("".join(f"file '{Path(r['path']).name}'\n" for r in results), encoding="utf-8")
        joined = clips / "joined.mp4"
        ffmpeg("-f", "concat", "-safe", "0", "-i", concat_list, "-c", "copy", joined)

        final = job.dir / "final.mp4"
        music = self._pick_music(job)
        if music:
            # Background music at a low level with ducking: it drops automatically whenever the narrator speaks
            fc = ("[1:a]volume=0.25,aresample=48000[m];"
                  "[0:a]asplit=2[voice][sc];"
                  "[m][sc]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[duck];"
                  "[voice][duck]amix=inputs=2:duration=first:normalize=0,"
                  "loudnorm=I=-14:TP=-1.5:LRA=11[a]")
            ffmpeg("-i", joined, "-stream_loop", "-1", "-i", music, "-filter_complex", fc,
                   "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                   "-shortest", "-movflags", "+faststart", final)
        else:
            ffmpeg("-i", joined, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:v", "copy",
                   "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", final)

        thumb = self._thumbnail(job, final)
        vertical = self._vertical_version(job, final)
        job.put("video", {"path": str(final), "duration": round(duration(final), 2), "vertical": str(vertical),
                          "thumbnail": str(thumb), "music": str(music) if music else None})

    def _vertical_version(self, job: Job, final: Path) -> Path:
        """A 9:16 version for TikTok and Instagram Reels: the video centred over a blurred copy of itself as the background."""
        if settings.video_format == "vertical":
            return final
        out = job.dir / "final_vertical.mp4"
        fc = ("[0:v]split=2[bg][fg];"
              "[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:2,eq=brightness=-0.12[b];"
              "[fg]scale=1080:-2[f];[b][f]overlay=(W-w)/2:(H-h)/2,setsar=1[v]")
        ffmpeg("-i", final, "-filter_complex", fc, "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "medium",
               "-crf", "21", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", out)
        return out

    # ------------------------------------------------------------------
    def _pick_music(self, job: Job) -> Path | None:
        files = sorted(p for p in settings.music_dir.glob("*") if p.suffix.lower() in {".mp3", ".wav", ".m4a", ".ogg"})
        if not files:
            return None
        mood = job.get("script")["scenes"][0].get("mood", "")
        matching = [f for f in files if mood and mood in f.stem.lower()]
        return random.Random(job.day.toordinal()).choice(matching or files)

    def _thumbnail(self, job: Job, video: Path) -> Path:
        """Thumbnail: a clean frame (no subtitles) from the first scene + large, attention-grabbing text."""
        w, h = settings.resolution
        first = job.get("media")[0]
        frame = job.dir / "thumb_frame.png"
        crop = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}"
        if first["kind"] == "video":
            ffmpeg("-ss", "1", "-i", first["path"], "-frames:v", "1", "-vf", crop, frame)
        else:
            ffmpeg("-i", first["path"], "-frames:v", "1", "-vf", crop, frame)
        text = _clean(job.get("script").get("thumbnail_text", ""))
        fs = int(h * (0.09 if h > w else 0.13))
        ass = job.dir / "thumb.ass"
        ass.write_text(
            "[Script Info]\nScriptType: v4.00+\n"
            f"PlayResX: {w}\nPlayResY: {h}\nWrapStyle: 0\n\n[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
            "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            f"Style: T,{FONT_NAME},{fs},&H0000E5FF,&H000000FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,{max(6, fs // 12)},4,5,80,80,0,1\n\n"
            "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
            f"Dialogue: 0,0:00:00.00,0:00:10.00,T,,0,0,0,,{text}\n",
            encoding="utf-8",
        )
        thumb = job.dir / "thumbnail.jpg"
        subs = f"subtitles='{_escape_filter_path(ass)}'"
        if FONTS_DIR.exists():
            subs += f":fontsdir='{_escape_filter_path(FONTS_DIR)}'"
        ffmpeg("-i", frame, "-vf", f"eq=contrast=1.25:saturation=1.35:brightness=-0.05,{subs}",
               "-frames:v", "1", "-q:v", "2", thumb)
        return thumb

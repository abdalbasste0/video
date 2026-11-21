"""Local media tools: Arabic text drawing, scene cards, thumbnails, voices, ffmpeg."""
import asyncio
import base64
import json
import random
import shutil
import subprocess
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, features

from .settings import ROOT

FONTS = ROOT / "assets" / "fonts"
MUSIC = ROOT / "assets" / "music"
FONT_BOLD = FONTS / "Cairo-Bold.ttf"
FONT_BLACK = FONTS / "Cairo-Black.ttf"

PALETTE = {
    "bg": (237, 227, 209),      # muted beige
    "ink": (34, 34, 40),
    "navy": (27, 42, 74),       # chapter cards
    "red": (205, 52, 48),
    "green": (46, 140, 87),
    "blue": (40, 102, 184),
    "dark": (27, 42, 74),
    "white": (255, 255, 255),
}

_RAQM = features.check("raqm")


# ---------------------------------------------------------------- Arabic text
def _shape(text):
    from . import lang
    if _RAQM or not lang.rtl():
        return text
    import arabic_reshaper
    from bidi.algorithm import get_display
    return get_display(arabic_reshaper.reshape(text))


def _font(size, black=False):
    path = FONT_BLACK if black else FONT_BOLD
    try:
        return ImageFont.truetype(str(path), size, layout_engine=ImageFont.Layout.RAQM if _RAQM else ImageFont.Layout.BASIC)
    except OSError:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size)


def _text_kwargs():
    from . import lang
    if not _RAQM:
        return {}
    return {"direction": "rtl", "language": "ar"} if lang.rtl() else {"direction": "ltr", "language": "en"}


def _width(draw, text, font):
    return draw.textlength(_shape(text), font=font, **_text_kwargs())


def wrap(draw, text, font, max_w):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and _width(draw, trial, font) > max_w:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def draw_block(draw, text, box, size, color, black=False, stroke=0, stroke_color=None, min_size=28):
    """Fit `text` inside box=(x0,y0,x1,y1), centred, shrinking the font if needed."""
    x0, y0, x1, y1 = box
    while True:
        font = _font(size, black)
        lines = wrap(draw, text, font, x1 - x0)
        line_h = int(size * 1.45)
        if len(lines) * line_h <= (y1 - y0) or size <= min_size:
            break
        size -= 4
    y = y0 + ((y1 - y0) - len(lines) * line_h) // 2
    for line in lines:
        w = _width(draw, line, font)
        draw.text((x0 + ((x1 - x0) - w) / 2, y), _shape(line), font=font, fill=color,
                  stroke_width=stroke, stroke_fill=stroke_color, **_text_kwargs())
        y += line_h


# ---------------------------------------------------------------- illustrations (optional image API)
def fetch_illustration(scene, settings, w, h, seed=None):
    """Generate the scene picture with the image service chosen in settings (see image_providers.py)."""
    from . import image_providers
    cfg = settings["images"]
    style = cfg.get("story_style_prompt") if settings["channel"].get("format") == "story" else cfg.get("style_prompt")
    prompt = f"{scene.get('visual_prompt', '')}. Style: {style or ''}"
    return image_providers.generate(prompt, cfg, w, h, seed)


def thumbnail(path, text, sub, accent_name, bg_image=None, w=1280, h=720):
    accent = PALETTE.get(accent_name, PALETTE["red"])
    if bg_image and Path(bg_image).exists():
        img = Image.open(bg_image).convert("RGB").resize((w, h))
        img = ImageEnhance.Brightness(img.filter(ImageFilter.GaussianBlur(3))).enhance(0.45)
    else:
        img = Image.new("RGB", (w, h), PALETTE["navy"])
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, 26, h), fill=accent)
    d.rectangle((w - 26, 0, w, h), fill=accent)
    draw_block(d, text, (70, 60, w - 70, h * 0.68), 150, PALETTE["white"], black=True, stroke=8, stroke_color=(0, 0, 0))
    if sub:
        sf = _font(56, black=True)
        sw = _width(d, sub, sf) + 80
        x0 = (w - sw) / 2
        d.rounded_rectangle((x0, h * 0.73, x0 + sw, h * 0.73 + 100), radius=24, fill=accent)
        draw_block(d, sub, (x0, h * 0.73, x0 + sw, h * 0.73 + 100), 56, PALETTE["white"], black=True)
    img.save(path, quality=92)


# ---------------------------------------------------------------- audio
def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {' '.join(map(str, cmd[:6]))}…\n{p.stderr[-1500:]}")
    return p.stdout


def duration(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)])
    return float(json.loads(out)["format"]["duration"])


def tts(path, text, settings):
    v = settings["voice"]
    provider = v.get("provider", "edge")
    if provider == "edge":
        import edge_tts
        async def _go():
            await edge_tts.Communicate(text, v.get("edge_voice", "ar-EG-ShakirNeural"), rate=v.get("edge_rate", "+0%")).save(str(path))
        asyncio.run(_go())
    elif provider == "elevenlabs":
        r = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{v['elevenlabs_voice_id']}",
            headers={"xi-api-key": v["elevenlabs_api_key"], "accept": "audio/mpeg"},
            json={"text": text, "model_id": v.get("elevenlabs_model", "eleven_multilingual_v2")},
            timeout=300,
        )
        r.raise_for_status()
        Path(path).write_bytes(r.content)
    elif provider == "piper":  # free, offline neural voice (https://github.com/rhasspy/piper)
        import sys
        wav = Path(path).with_suffix(".wav")
        p = subprocess.run([sys.executable, "-m", "piper", "-m", v["piper_model"], "-f", str(wav),
                            "--length-scale", str(v.get("piper_length_scale", 1.0)), "--sentence-silence", "0.35"],
                           input=text, capture_output=True, text=True)
        if p.returncode:
            raise RuntimeError(f"piper failed: {p.stderr[-500:]}")
        run(["ffmpeg", "-y", "-i", str(wav), "-b:a", "160k", str(path)])
        wav.unlink()
    elif provider == "silent":  # testing without a voice service: ~2.4 words/second
        secs = max(2.0, len(text.split()) / 2.4)
        run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", f"{secs:.2f}", "-q:a", "9", str(path)])
    else:
        raise ValueError(f"unknown voice provider {provider}")
    return duration(path)


GAP = 0.35          # breath after each scene (the reference pauses ~0.6s on average)
CARD = 2.0          # chapter card length (reference: ~2s navy card between chapters)


def segments(scenes):
    """Timeline: each scene = [chapter card lead][voice][gap]. Returns (start_of_segment, voice_start)."""
    t, out = 0.0, []
    for sc in scenes:
        lead = sc.get("lead", 0.0)
        out.append((t, t + lead))
        t += lead + sc["duration"] + sc.get("gap", GAP)
    return out


def build_audio(job_dir, scenes, settings, music=True):
    """Voice per scene (with silence under chapter cards), joined, optional quiet ducked music,
    then loudness-normalised to -14 LUFS like the reference."""
    parts = []
    for i, sc in enumerate(scenes):
        out = job_dir / "audio" / f"pad_{i:03d}.wav"
        lead_ms = int(sc.get("lead", 0) * 1000)
        af = (f"adelay={lead_ms}:all=1," if lead_ms else "") + "apad"
        run(["ffmpeg", "-y", "-i", str(sc["audio"]), "-af", af, "-t", f"{sc.get('lead', 0) + sc['duration'] + sc.get('gap', GAP):.3f}",
             "-ar", "44100", "-ac", "2", str(out)])
        parts.append(out)
    lst = job_dir / "audio" / "list.txt"
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))
    voice = job_dir / "audio" / "voice.wav"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(voice)])

    final = job_dir / "audio" / "mix.m4a"
    norm = "loudnorm=I=-14:TP=-1.5:LRA=7"
    tracks = sorted([p for p in MUSIC.glob("*") if p.suffix.lower() in (".mp3", ".wav", ".m4a", ".ogg")]) if music and MUSIC.exists() else []
    if not tracks:
        run(["ffmpeg", "-y", "-i", str(voice), "-af", norm, "-ar", "44100", "-c:a", "aac", "-b:a", "192k", str(final)])
        return final, None
    track = random.choice(tracks)
    total = duration(voice)
    story = settings["channel"].get("format") == "story"
    vol = settings["video"].get("story_music_volume", 0.14) if story else settings["video"].get("music_volume", 0.06)
    fc = (f"[1:a]volume={vol},afade=t=in:d=2,afade=t=out:st={max(0, total - 3):.2f}:d=3[m];"
          f"[0:a]asplit[v1][v2];[m][v1]sidechaincompress=threshold=0.04:ratio=6:attack=20:release=400[duck];"
          f"[v2][duck]amix=inputs=2:duration=first:normalize=0,{norm}[out]")
    run(["ffmpeg", "-y", "-i", str(voice), "-stream_loop", "-1", "-i", str(track), "-filter_complex", fc,
         "-map", "[out]", "-ar", "44100", "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.2f}", str(final)])
    return final, track.name


# ---------------------------------------------------------------- video
def _enc(fps):
    return ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(fps)]


def build_clip(states, out, secs, fps, xf=0.3):
    """Scene clip where elements appear one after another (soft cross-fades between build states).
    The first state shows briefly, later states arrive during the first ~70% of the narration."""
    n = len(states)
    if n == 1 or secs < 1.5:
        run(["ffmpeg", "-y", "-loop", "1", "-framerate", str(fps), "-t", f"{secs:.3f}", "-i", str(states[-1])] + _enc(fps) + [str(out)])
        return
    build = secs * 0.7
    first = min(1.2, build / n)
    rest = (build - first) / (n - 1)
    shown = [first] + [rest] * (n - 2) + [secs - first - rest * (n - 2)]
    cmd = ["ffmpeg", "-y"]
    for i, (img, t) in enumerate(zip(states, shown)):
        cmd += ["-loop", "1", "-framerate", str(fps), "-t", f"{t + (xf if i < n - 1 else 0):.3f}", "-i", str(img)]
    chain, prev, off = [], "0:v", 0.0
    for i in range(1, n):
        off += shown[i - 1]
        tag = f"x{i}"
        chain.append(f"[{prev}][{i}:v]xfade=transition=fade:duration={xf}:offset={off:.3f}[{tag}]")
        prev = tag
    run(cmd + ["-filter_complex", ";".join(chain), "-map", f"[{prev}]", "-t", f"{secs:.3f}"] + _enc(fps) + [str(out)])


def zoom_clip(img, out, secs, fps, idx=0, amount=0.05):
    """Story shots: one illustration with a slow, gentle push-in (alternating in/out)."""
    with Image.open(img) as im:
        w, h = im.size
    frames = max(1, int(secs * fps))
    z = f"1+{amount}*on/{frames}" if idx % 2 == 0 else f"{1 + amount}-{amount}*on/{frames}"
    vf = (f"scale={int(w * 1.25)}:-2,zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
          f":d=1:s={w}x{h}:fps={fps}")
    run(["ffmpeg", "-y", "-loop", "1", "-framerate", str(fps), "-i", str(img), "-vf", vf,
         "-t", f"{secs:.3f}"] + _enc(fps) + [str(out)])


def card_clip(img, out, secs, fps):
    """Chapter card with a short fade in/out."""
    run(["ffmpeg", "-y", "-loop", "1", "-framerate", str(fps), "-t", f"{secs:.3f}", "-i", str(img), "-vf",
         f"fade=t=in:d=0.35,fade=t=out:st={secs - 0.3:.2f}:d=0.3"] + _enc(fps) + [str(out)])


def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def _cues(scenes, words_per_line=4):
    """Short caption chunks (the reference shows 3-5 words at a time) with per-word timings."""
    cues = []
    for sc, (_, v0) in zip(scenes, segments(scenes)):
        words = sc["narration"].split()
        chunks = [words[i:i + words_per_line] for i in range(0, len(words), words_per_line)] or [[""]]
        total_chars = sum(len(w) + 1 for c in chunks for w in c) or 1
        t = v0
        for c in chunks:
            wt = [sc["duration"] * (len(w) + 1) / total_chars for w in c]
            cues.append((t, t + sum(wt), c, wt))
            t += sum(wt)
    return cues


def write_srt(path, scenes):
    cues = _cues(scenes, 7)
    Path(path).write_text("\n".join(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{' '.join(c)}\n" for i, (a, b, c, _) in enumerate(cues, 1)),
                          encoding="utf-8")


def write_ass(path, scenes, w, h, words_per_line=4, center_y=0.9, size=0.045):
    """Short caption chunks on a dark box centred in the sand band under the ground line
    (as in the reference). Per-word karaoke tags are not used: libass breaks Arabic word
    order and the box when a line is split into karaoke segments."""
    def ts(t):
        cs = int(round(t * 100))
        return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"
    fs = int(h * size)
    margin_v = int(h * (1 - center_y) - fs * 0.65)
    head = (f"[Script Info]\nScriptType: v4.00+\nPlayResX: {w}\nPlayResY: {h}\nWrapStyle: 0\n\n[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, "
            "StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            # primary = spoken (white), secondary = not yet spoken (grey), box = dark grey
            f"Style: Default,Cairo,{fs},&H00FFFFFF,&H00A0A0A0,&H1E3A3A3C,&H1E3A3A3C,-1,0,0,0,100,100,0,0,3,"
            f"{max(4, int(fs * 0.38))},0,2,{int(w * 0.1)},{int(w * 0.1)},{margin_v},-1\n\n"
            "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    lines = []
    for a, b, words, wt in _cues(scenes, words_per_line):
        text = "{\\fad(120,0)}" + " ".join(words)
        lines.append(f"Dialogue: 0,{ts(a)},{ts(b)},Default,,0,0,0,,{text}\n")
    Path(path).write_text(head + "".join(lines), encoding="utf-8")


def assemble(job_dir, clips, audio, ass, out, burn, fps):
    lst = job_dir / "clips" / "list.txt"
    lst.write_text("".join(f"file '{Path(c).resolve()}'\n" for c in clips))
    silent = job_dir / "clips" / "joined.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(silent)])
    cmd = ["ffmpeg", "-y", "-i", str(silent), "-i", str(audio)]
    if burn:
        esc = lambda p: str(Path(p).resolve()).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
        # complex shaping = correct joined Arabic letters
        cmd += ["-vf", f"ass='{esc(ass)}':fontsdir='{esc(FONTS)}':shaping=complex",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p"]
    else:
        cmd += ["-c:v", "copy"]
    cmd += ["-c:a", "aac", "-b:a", "192k", "-map", "0:v", "-map", "1:a", "-shortest", "-r", str(fps),
            "-movflags", "+faststart", str(out)]
    run(cmd)


def make_short(silent_video, audio, ass, out, seconds):
    """Vertical 9:16: blurred background + centred picture + big captions under it."""
    esc = lambda p: str(Path(p).resolve()).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    fc = ("[0:v]split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=24:2[bg];"
          "[b]scale=1300:-2,crop=1080:ih[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,"
          f"ass='{esc(ass)}':fontsdir='{esc(FONTS)}':shaping=complex,format=yuv420p[v]")
    run(["ffmpeg", "-y", "-i", str(silent_video), "-i", str(audio), "-t", f"{seconds:.2f}", "-filter_complex", fc,
         "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-c:a", "aac", "-b:a", "160k",
         "-movflags", "+faststart", str(out)])


def have_ffmpeg():
    return bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))

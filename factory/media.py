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
    if _RAQM:
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
    return {"direction": "rtl", "language": "ar"} if _RAQM else {}


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


# ---------------------------------------------------------------- scene images
def scene_card(path, scene, idx, total, chapter_title, is_chapter_start, w, h):
    """Offline 2D explainer card in the reference palette."""
    rnd = random.Random(idx * 7919)
    accent = PALETTE.get(scene.get("accent", "blue"), PALETTE["blue"])
    if is_chapter_start:
        img = Image.new("RGB", (w, h), PALETTE["navy"])
        d = ImageDraw.Draw(img)
        for _ in range(6):
            r = rnd.randint(h // 10, h // 3)
            cx, cy = rnd.randint(0, w), rnd.randint(0, h)
            d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(52, 70, 110), width=6)
        d.rectangle((w * 0.42, h * 0.30, w * 0.58, h * 0.31), fill=accent)
        draw_block(d, chapter_title, (w * 0.1, h * 0.33, w * 0.9, h * 0.62), int(h * 0.11), PALETTE["white"], black=True)
        draw_block(d, scene.get("on_screen_text", ""), (w * 0.15, h * 0.64, w * 0.85, h * 0.80), int(h * 0.05), (210, 216, 230))
    else:
        img = Image.new("RGB", (w, h), PALETTE["bg"])
        d = ImageDraw.Draw(img)
        # soft decorative shapes so cards don't look identical
        for _ in range(5):
            r = rnd.randint(h // 12, h // 4)
            cx, cy = rnd.randint(0, w), rnd.randint(0, h)
            tint = tuple(int(c * 0.12 + b * 0.88) for c, b in zip(accent, PALETTE["bg"]))
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=tint)
        for _ in range(3):
            y = rnd.randint(int(h * 0.15), int(h * 0.85))
            d.line((0, y, w, y + rnd.randint(-80, 80)), fill=(222, 210, 188), width=4)
        # chapter pill (top-right, RTL)
        pill_font = _font(int(h * 0.035))
        pw = _width(d, chapter_title, pill_font) + 60
        d.rounded_rectangle((w - pw - 50, 40, w - 50, 40 + h * 0.07), radius=30, fill=PALETTE["navy"])
        draw_block(d, chapter_title, (w - pw - 50, 40, w - 50, 40 + h * 0.07), int(h * 0.035), PALETTE["white"])
        # main statement box
        box = (w * 0.12, h * 0.30, w * 0.88, h * 0.70)
        d.rounded_rectangle((box[0] + 14, box[1] + 14, box[2] + 14, box[3] + 14), radius=40, fill=(205, 192, 168))
        d.rounded_rectangle(box, radius=40, fill=PALETTE["white"], outline=accent, width=10)
        d.rectangle((box[2] - 40, box[1] + 40, box[2] - 22, box[3] - 40), fill=accent)
        draw_block(d, scene.get("on_screen_text", ""), (box[0] + 60, box[1] + 30, box[2] - 80, box[3] - 30),
                   int(h * 0.085), PALETTE["ink"], black=True)
    # progress bar
    d.rectangle((0, h - 12, w * (idx + 1) / total, h), fill=accent)
    img.save(path)


def scene_from_api(path, scene, settings, w, h):
    """Use any image API you connect. POST JSON {prompt,width,height}; accepts image bytes or JSON with b64/url."""
    cfg = settings["images"]
    headers = {"Content-Type": "application/json"}
    if cfg.get("http_auth_header"):
        name, _, value = cfg["http_auth_header"].partition(":")
        headers[name.strip()] = value.strip()
    prompt = f"{cfg.get('style_prompt', '')}. {scene.get('visual_prompt', '')}"
    r = requests.post(cfg["http_url"], json={"prompt": prompt, "width": w, "height": h}, headers=headers, timeout=180)
    r.raise_for_status()
    if r.headers.get("content-type", "").startswith("image/"):
        data = r.content
    else:
        j = r.json()
        j = j.get("data", [j])[0] if isinstance(j.get("data"), list) else j
        if j.get("b64_json") or j.get("image_base64") or j.get("b64"):
            data = base64.b64decode(j.get("b64_json") or j.get("image_base64") or j.get("b64"))
        else:
            data = requests.get(j.get("url") or j["image_url"], timeout=120).content
    raw = Path(path).with_suffix(".raw")
    raw.write_bytes(data)
    img = Image.open(raw).convert("RGB")
    raw.unlink()
    # cover-fit, then lay the on-screen text in a band at the bottom
    scale = max(w / img.width, h / img.height)
    img = img.resize((int(img.width * scale) + 1, int(img.height * scale) + 1))
    left, top = (img.width - w) // 2, (img.height - h) // 2
    img = img.crop((left, top, left + w, top + h))
    text = scene.get("on_screen_text")
    if text:
        d = ImageDraw.Draw(img, "RGBA")
        accent = PALETTE.get(scene.get("accent", "blue"), PALETTE["blue"])
        d.rounded_rectangle((w * 0.2, h * 0.74, w * 0.8, h * 0.92), radius=30, fill=accent + (235,))
        draw_block(d, text, (w * 0.22, h * 0.75, w * 0.78, h * 0.91), int(h * 0.06), PALETTE["white"], black=True)
    img.save(path)


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
    elif provider == "silent":  # testing without a voice service: ~2.4 words/second
        secs = max(2.0, len(text.split()) / 2.4)
        run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", f"{secs:.2f}", "-q:a", "9", str(path)])
    else:
        raise ValueError(f"unknown voice provider {provider}")
    return duration(path)


def build_audio(job_dir, scenes, settings, gap=0.35, music=True):
    """Pad each narration clip to its scene length, join them, add ducked music."""
    parts = []
    for i, sc in enumerate(scenes):
        out = job_dir / "audio" / f"pad_{i:03d}.wav"
        run(["ffmpeg", "-y", "-i", str(sc["audio"]), "-af", "apad", "-t", f"{sc['duration'] + gap:.3f}",
             "-ar", "44100", "-ac", "2", str(out)])
        parts.append(out)
    lst = job_dir / "audio" / "list.txt"
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))
    voice = job_dir / "audio" / "voice.wav"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(voice)])

    final = job_dir / "audio" / "mix.m4a"
    tracks = sorted([p for p in MUSIC.glob("*") if p.suffix.lower() in (".mp3", ".wav", ".m4a", ".ogg")]) if music and MUSIC.exists() else []
    if not tracks:
        run(["ffmpeg", "-y", "-i", str(voice), "-c:a", "aac", "-b:a", "192k", str(final)])
        return final, None
    track = random.choice(tracks)
    total = duration(voice)
    vol = settings["video"].get("music_volume", 0.22)
    fc = (f"[1:a]volume={vol},afade=t=in:d=2,afade=t=out:st={max(0, total - 3):.2f}:d=3[m];"
          f"[0:a]asplit[v1][v2];[m][v1]sidechaincompress=threshold=0.04:ratio=6:attack=20:release=400[duck];"
          f"[v2][duck]amix=inputs=2:duration=first:normalize=0[out]")
    run(["ffmpeg", "-y", "-i", str(voice), "-stream_loop", "-1", "-i", str(track), "-filter_complex", fc,
         "-map", "[out]", "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.2f}", str(final)])
    return final, track.name


# ---------------------------------------------------------------- video
def scene_clip(img, out, secs, idx, w, h, fps):
    frames = max(1, int(secs * fps))
    zoom_in = idx % 2 == 0
    z = f"min(1+0.10*on/{frames},1.10)" if zoom_in else f"max(1.10-0.10*on/{frames},1.0)"
    vf = (f"scale={int(w * 1.5)}:-2,zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
          f":d=1:s={w}x{h}:fps={fps},format=yuv420p")
    run(["ffmpeg", "-y", "-loop", "1", "-framerate", str(fps), "-i", str(img), "-vf", vf, "-t", f"{secs:.3f}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-r", str(fps), str(out)])


def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def _cues(scenes, gap=0.35, words_per_line=7):
    cues, t = [], 0.0
    for sc in scenes:
        words = sc["narration"].split()
        chunks = [" ".join(words[i:i + words_per_line]) for i in range(0, len(words), words_per_line)] or [""]
        total_chars = sum(len(c) for c in chunks) or 1
        start = t
        for c in chunks:
            dur = sc["duration"] * len(c) / total_chars
            cues.append((start, start + dur, c))
            start += dur
        t += sc["duration"] + gap
    return cues


def write_srt(path, scenes):
    cues = _cues(scenes)
    Path(path).write_text("\n".join(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{c}\n" for i, (a, b, c) in enumerate(cues, 1)),
                          encoding="utf-8")


def write_ass(path, scenes, w, h, words_per_line=7, margin_v=0.05, size=0.048):
    def ts(t):
        cs = int(round(t * 100))
        return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"
    head = (f"[Script Info]\nScriptType: v4.00+\nPlayResX: {w}\nPlayResY: {h}\nWrapStyle: 0\n\n[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, "
            "StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            f"Style: Default,Cairo,{int(h * size)},&H00FFFFFF,&H00FFFFFF,&HB4141414,&HB4141414,-1,0,0,0,100,100,0,0,3,"
            f"{int(h * 0.009)},0,2,{int(w * 0.08)},{int(w * 0.08)},{int(h * margin_v)},1\n\n"
            "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    body = "".join(f"Dialogue: 0,{ts(a)},{ts(b)},Default,,0,0,0,,{c}\n" for a, b, c in _cues(scenes, words_per_line=words_per_line))
    Path(path).write_text(head + body, encoding="utf-8")


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
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "20"]
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

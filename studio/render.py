"""Story JSON -> finished MP4 (voice + animation + music + subtitles) + thumbnail.

usage: python -m studio.render stories/001-zero-viewers.json [--preview] [--vertical]
"""
import argparse
import json
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
import skia
import soundfile as sf

from . import audio, scenes
from . import character as ch

FPS = 30
W, H = 1920, 1080
STAND_Y = scenes.GROUND - ch.THIGH - ch.SHIN - 12
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAXW = [W * 0.9]  # text width limit; narrowed for the 9:16 centre crop

# default hip positions per action (so stories stay short)
ACTION_Y = {"sit_desk": 745, "sit_desk_slump": 745, "sit_edge": 790, "lie": 676,
            "kneel": STAND_Y, "pushup": STAND_Y}


# ------------------------------------------------------------------ timeline
def build_timeline(story, workdir, cache=True):
    os.makedirs(workdir, exist_ok=True)
    voice = story.get("voice", "am_michael")
    speed = story.get("speed", 0.92)
    t = 0.0
    shots = []
    for i, s in enumerate(story["shots"]):
        s = dict(s)
        lead = s.get("lead", 0.35)
        tail = s.get("tail", 0.45)
        if s.get("say"):
            wav = os.path.join(workdir, f"vo_{i:03d}.wav")
            key = os.path.join(workdir, f"vo_{i:03d}.txt")
            sig = f"{voice}|{speed}|{s['say']}"
            if cache and os.path.exists(wav) and open(key).read() == sig:
                vo, _ = sf.read(wav, dtype="float32")
            else:
                vo = audio.tts(s["say"], voice=voice, speed=s.get("speed", speed))
                sf.write(wav, vo, audio.SR)
                open(key, "w").write(sig)
            s["vo"] = wav
            s["vo_len"] = len(vo) / audio.SR
            dur = max(s.get("dur", 0), lead + s["vo_len"] + tail)
        else:
            dur = s.get("dur", 2.0)
            lead = 0
        s.update(start=t, dur=dur, lead=lead)
        t += dur
        shots.append(s)
    return shots, t


# ------------------------------------------------------------------ captions
def subtitle_chunks(text, n=4):
    words = text.split()
    return [" ".join(words[i:i + n]) for i in range(0, len(words), n)]


def draw_text_center(c, text, cx, cy, size, color=0xFFFFFFFF, stroke=14, weight="Black", scale=1.0, alpha=1.0):
    f = scenes.font(size, weight)
    w = f.measureText(text)
    while w > MAXW[0] and size > 20:
        size *= 0.92
        f = scenes.font(size, weight)
        w = f.measureText(text)
    c.save()
    c.translate(cx, cy)
    c.scale(scale, scale)
    st = ch.paint(0xFF000000, stroke)
    st.setAlphaf(alpha)
    fi = ch.paint(color)
    fi.setAlphaf(alpha)
    c.drawString(text, -w / 2, size * 0.36, f, st)
    c.drawString(text, -w / 2, size * 0.36, f, fi)
    c.restore()


def caption_draw(c, s, lt):
    cap = s.get("caption")
    if not cap:
        return
    k = min(1.0, lt / 0.25)
    pop = 1.0 + 0.25 * (1 - k) ** 2
    color = int(s.get("caption_color", "0xFFFFFFFF"), 16) if isinstance(s.get("caption_color"), str) else 0xFFFFFFFF
    y = s.get("caption_y", 170)
    draw_text_center(c, cap, W / 2, y, s.get("caption_size", 120), color, 18, "Black", pop, k)


def subtitles_draw(c, s, lt):
    if not s.get("say") or s.get("no_subs"):
        return
    chunks = subtitle_chunks(s["say"], 2 if MAXW[0] < 1000 else 4)
    total = sum(len(x) for x in chunks)
    p = (lt - s["lead"]) / max(0.1, s["vo_len"])
    if p < 0 or p > 1.02:
        return
    acc = 0
    for chunk in chunks:
        acc += len(chunk) / total
        if p <= acc + 1e-6:
            break
    vert = MAXW[0] < 1000
    draw_text_center(c, chunk.upper(), W / 2, H - (300 if vert else 110), 46 if vert else 54,
                     0xFFFFFF00 if vert else 0xFFFFFFFF, 10, "Black" if vert else "ExtraBold")


# ------------------------------------------------------------------ frame
def vignette(c):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial((W / 2, H / 2), W * 0.72,
                                               [0x00000000, 0x00000000, 0xCC000000], [0, 0.55, 1]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)


def draw_shot(c, s, lt, T):
    o = s.get("bg_opts", {})
    bgname = s.get("bg", "void")
    a = s.get("actor")
    cam = s.get("cam", {})
    k = ch.ease(lt / max(0.01, s["dur"]))
    z0, z1 = cam.get("zoom", [1.0, 1.06])
    zoom = ch.lerp(z0, z1, k)
    fx, fy = cam.get("focus", [W / 2, H / 2])
    if zoom >= 1:  # keep the view inside the world
        hw, hh = W / 2 / zoom, H / 2 / zoom
        fx = min(max(fx, hw), W - hw)
        fy = min(max(fy, hh), H - hh)
    shake = cam.get("shake", 0)
    c.save()
    c.translate(W / 2, H / 2)
    c.scale(zoom, zoom)
    c.translate(-fx + math.sin(T * 40) * shake, -fy + math.cos(T * 33) * shake)
    _, lights = scenes.BACKGROUNDS[bgname](c, T, W, H, o)
    if bgname == "desk":
        lights = lights + scenes.desk_front(c, T, o)
    if a:
        act = a.get("action", "stand")
        x0 = a.get("x", W / 2)
        x1 = a.get("move_to", x0)
        x = ch.lerp(x0, x1, lt / s["dur"])
        y = a.get("y", ACTION_Y.get(act, STAND_Y))
        if bgname == "mountain":
            y = scenes.slope_y(x) - ch.THIGH - ch.SHIN - 12
        pz = ch.ACTIONS[act](T)
        if a.get("then") and lt > a.get("then_at", s["dur"] / 2):
            q = ch.ACTIONS[a["then"]](T)
            pz = ch.blend(pz, q, ch.ease((lt - a.get("then_at", s["dur"] / 2)) / 0.6))
        prop = None
        if a.get("prop") == "phone":
            prop = scenes.phone_prop
        ch.draw(c, pz, x, y, scale=a.get("scale", 1.0), facing=a.get("facing", 1),
                expr=a.get("expr", "neutral"), t=T, look=tuple(a.get("look", (0, 0))),
                prop_hand=prop)
        if a.get("prop") == "phone":
            # phone light on the face
            lights = lights + [(x - 150 if act == "lie" else x + 40, y - 200 if act != "lie" else y - 60,
                                360, 0xFF8EC9FF, 0.9)]
    if bgname == "bedroom" and a and a.get("action") == "lie":
        scenes.blanket(c, o)
    for (lx, ly, r, col, inten) in lights:
        scenes.glow(c, lx, ly, r, col, inten * (0.92 + 0.08 * math.sin(T * 7)))
    if "rain" in s.get("fx", []):
        scenes.rain(c, T, W, H)
    c.restore()
    # overlays (not affected by camera)
    tint = s.get("tint")
    if tint:
        c.drawRect(skia.Rect.MakeWH(W, H), ch.paint(int(tint, 16)))
    vignette(c)
    caption_draw(c, s, lt)
    subtitles_draw(c, s, lt)
    fade_in = s.get("fade_in", 0.0)
    fade_out = s.get("fade_out", 0.0)
    alpha = 0.0
    if fade_in and lt < fade_in:
        alpha = 1 - lt / fade_in
    if fade_out and lt > s["dur"] - fade_out:
        alpha = max(alpha, (lt - (s["dur"] - fade_out)) / fade_out)
    if alpha > 0:
        c.drawRect(skia.Rect.MakeWH(W, H), ch.paint(skia.Color4f(0, 0, 0, alpha).toColor()))


def frame_at(shots, T, surface):
    c = surface.getCanvas()
    c.clear(0xFF000000)
    for s in shots:
        if s["start"] <= T < s["start"] + s["dur"]:
            draw_shot(c, s, T - s["start"], T)
            break
    return surface


def _render_chunk(args):
    shots, f0, f1, path, vertical = args
    surface = skia.Surface(W, H)
    MAXW[0] = 560 if vertical else W * 0.9
    ow, oh = (1080, 1920) if vertical else (W, H)
    vf = ["-vf", "crop=608:1080:656:0,scale=1080:1920:flags=lanczos"] if vertical else []
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", *vf, "-c:v", "libx264",
           "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(f0, f1):
        frame_at(shots, f / FPS, surface)
        p.stdin.write(surface.toarray(colorType=skia.kRGBA_8888_ColorType).tobytes())
    p.stdin.close()
    p.wait()
    return path


# ------------------------------------------------------------------ audio mix
def mix_audio(story, shots, total, path):
    n = int(total * audio.SR) + audio.SR
    vo = np.zeros(n, np.float32)
    fx = np.zeros(n, np.float32)
    for s in shots:
        if s.get("vo"):
            x, _ = sf.read(s["vo"], dtype="float32")
            i = int((s["start"] + s["lead"]) * audio.SR)
            vo[i:i + len(x)] += x[: n - i]
        for name in s.get("sfx", []):
            x = audio.sfx(name, s["dur"] if name in ("rain", "typing", "heartbeat") else None)
            i = int(s["start"] * audio.SR)
            fx[i:i + len(x)] += x[: n - i]
    mus = audio.music(total + 1, story.get("mood", "emotional"), story.get("seed", 1))
    mus = np.pad(mus, (0, max(0, n - len(mus))))[:n]
    env = audio.envelope(vo, 4800)
    env = env / (env.max() + 1e-6)
    duck = 0.22 - 0.12 * np.clip(env * 3, 0, 1)
    out = vo * 1.0 + fx + mus * duck
    out = out / max(1.0, np.max(np.abs(out)) / 0.95)
    sf.write(path, out[: int(total * audio.SR)], audio.SR)


# ------------------------------------------------------------------ thumbnail
def thumbnail(story, shots, path):
    th = story.get("thumbnail", {})
    idx = th.get("shot", 0)
    s = dict(shots[idx])
    s["caption"] = None
    s["no_subs"] = True
    s["fade_in"] = s["fade_out"] = 0
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    c.clear(0xFF000000)
    lt = th.get("t", s["dur"] * 0.6)
    s["cam"] = {"zoom": [th.get("zoom", 1.35)] * 2, "focus": th.get("focus", [W / 2, H / 2 + 60])}
    draw_shot(c, s, lt, s["start"] + lt)
    draw_text_center(c, th.get("text", story["title"]).upper(), W / 2, 150, 190,
                     0xFFFFFFFF, 26, "Black")
    surf.makeImageSnapshot().save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("story")
    ap.add_argument("--preview", action="store_true", help="render stills only")
    ap.add_argument("--vertical", action="store_true", help="also render a 9:16 Shorts cut")
    ap.add_argument("--only-vertical", action="store_true")
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    args = ap.parse_args()
    story = json.load(open(args.story))
    slug = os.path.splitext(os.path.basename(args.story))[0]
    out = os.path.join(ROOT, "output", slug)
    work = os.path.join(out, "work")
    os.makedirs(work, exist_ok=True)
    shots, total = build_timeline(story, work)
    print(f"{len(shots)} shots, {total:.1f}s")
    if args.preview:
        surf = skia.Surface(W, H)
        for i, s in enumerate(shots):
            frame_at(shots, s["start"] + s["dur"] * 0.55, surf)
            surf.makeImageSnapshot().save(os.path.join(work, f"preview_{i:02d}.png"))
        return
    mix_audio(story, shots, total, os.path.join(work, "mix.wav"))
    thumbnail(story, shots, os.path.join(out, "thumbnail.png"))
    nf = int(total * FPS)
    targets = [(False, "video.mp4")] + ([(True, "short.mp4")] if args.vertical else [])
    if args.only_vertical:
        targets = [(True, "short.mp4")]
    for vertical, name in targets:
        k = args.workers
        bounds = [nf * i // k for i in range(k + 1)]
        jobs = [(shots, bounds[i], bounds[i + 1], os.path.join(work, f"part{i}{'v' if vertical else ''}.mp4"), vertical)
                for i in range(k)]
        with Pool(k) as pool:
            parts = pool.map(_render_chunk, jobs)
        lst = os.path.join(work, "parts.txt")
        open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                        "-i", os.path.join(work, "mix.wav"), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                        "-shortest", os.path.join(out, name)], check=True)
        print("wrote", os.path.join(out, name))
    meta = {k: story[k] for k in ("title", "description", "tags") if k in story}
    json.dump(meta, open(os.path.join(out, "metadata.json"), "w"), indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()

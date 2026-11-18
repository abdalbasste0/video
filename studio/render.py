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

from . import audio, scenes, sets_cooper, sets_sea
from . import character as ch

FPS = 30
W, H = 1920, 1080
STAND_Y = scenes.GROUND - ch.THIGH - ch.SHIN - 12
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAXW = [W * 0.9]  # text width limit; narrowed for the 9:16 centre crop

# default hip positions per action (so stories stay short)
ACTION_Y = {"sit_desk": 745, "sit_desk_slump": 745, "sit": 745, "sit_drink": 745, "sit_turn": 745, "sit_edge": 790, "lie": 676,
            "kneel": STAND_Y, "pushup": STAND_Y}


# ------------------------------------------------------------------ timeline
def series_shots(story):
    """For a series episode: add a 'previously' recap, a PART title card and a 'to be continued' end."""
    se = story.get("series")
    if not se:
        return story["shots"]
    n = se["part"]
    head = []
    if se.get("previously"):
        head.append({"bg": "void", "bg_opts": {"color": "0xFF404860"}, "say": "Previously. " + se["previously"],
                     "caption": "PREVIOUSLY...", "caption_size": 80, "cam": {"zoom": [1.0, 1.05]},
                     "fade_in": 0.6, "grade": "noir"})
    head.append({"bg": "void", "bg_opts": {"color": "0xFFFFD08A"}, "say": f"Part {n}. {se['episode_title']}.",
                 "caption": se["name"].upper(), "caption_y": 470, "caption_size": 130,
                 "subtitle_override": f"PART {n}: {se['episode_title'].upper()}", "tail": 0.8, "cut": True})
    tail = [{"bg": "void", "bg_opts": {"color": "0xFF2EE6FF" if se.get("final") else "0xFF6070A0"},
             "say": "The end." if se.get("final") else "To be continued.",
             "caption": "THE END." if se.get("final") else "TO BE CONTINUED...", "caption_y": 540,
             "caption_size": 110, "tail": 1.5, "fade_out": 1.2}]
    return head + story["shots"] + tail


def build_timeline(story, workdir, cache=True):
    os.makedirs(workdir, exist_ok=True)
    voice = story.get("voice", "am_michael")
    speed = story.get("speed", 0.92)
    t = 0.0
    shots = []
    for i, s in enumerate(series_shots(story)):
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
    if s.get("subtitle_override"):
        draw_text_center(c, s["subtitle_override"], W / 2, H - 260 if MAXW[0] >= 1000 else H - 300, 64,
                         0xFFFFFFFF, 12, "Black")
        return
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
    draw_text_center(c, chunk.upper(), W / 2, H - (300 if vert else (60 if STORY[0].get('letterbox') else 110)), 46 if vert else 54,
                     0xFFFFFF00 if vert else 0xFFFFFFFF, 10, "Black" if vert else "ExtraBold")


# ------------------------------------------------------------------ frame
def vignette(c):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial((W / 2, H / 2), W * 0.72,
                                               [0x00000000, 0x00000000, 0xCC000000], [0, 0.55, 1]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)


GRADES = {  # (saturation, r, g, b multipliers)
    "none": (1.0, 1.0, 1.0, 1.0),
    "warm": (1.08, 1.06, 1.0, 0.92),
    "noir": (0.55, 0.88, 0.95, 1.1),
    "cold": (0.85, 0.9, 1.0, 1.12),
}


def grade_filter(name):
    sat, r, g, b = GRADES.get(name, GRADES["none"])
    lr, lg, lb = 0.2126, 0.7152, 0.0722
    m = []
    for row, mul in enumerate((r, g, b)):
        coeffs = [(1 - sat) * lr, (1 - sat) * lg, (1 - sat) * lb]
        coeffs[row] += sat
        m += [x * mul for x in coeffs] + [0, 0]
    m += [0, 0, 0, 1, 0]
    return skia.ColorFilters.Matrix(m)


_GRAIN = []


def grain(c, T):
    if not _GRAIN:
        rng = np.random.default_rng(0)
        for _ in range(6):
            n = rng.integers(0, 255, (270, 480), dtype=np.uint8)
            rgba = np.dstack([n, n, n, np.full_like(n, 255)])
            _GRAIN.append(skia.Image.fromarray(rgba, colorType=skia.kRGBA_8888_ColorType))
    p = skia.Paint()
    p.setAlphaf(0.06)
    p.setBlendMode(skia.BlendMode.kOverlay)
    c.drawImageRect(_GRAIN[int(T * 24) % 6], skia.Rect.MakeWH(W, H),
                    skia.SamplingOptions(skia.FilterMode.kNearest), p)


def letterbox(c, bar=118):
    c.drawRect(skia.Rect.MakeLTRB(0, 0, W, bar), ch.paint(0xFF000000))
    c.drawRect(skia.Rect.MakeLTRB(0, H - bar, W, H), ch.paint(0xFF000000))


def _actor_list(s):
    if s.get("actors"):
        return s["actors"]
    return [s["actor"]] if s.get("actor") else []


def draw_world(c, s, lt, T, story):
    """Everything seen through the camera, plus lighting and grade. Returns nothing."""
    o = dict(s.get("bg_opts", {}), _lt=lt)  # local shot time for animated sets
    bgname = s.get("bg", "void")
    cam = s.get("cam", {})
    k = ch.ease(lt / max(0.01, s["dur"]))
    z0, z1 = cam.get("zoom", [1.0, 1.06])
    zoom = ch.lerp(z0, z1, k)
    f0 = cam.get("focus", [W / 2, H / 2])
    f1 = cam.get("focus_to", f0)
    fx, fy = ch.lerp(f0[0], f1[0], k), ch.lerp(f0[1], f1[1], k)
    if zoom >= 1:  # keep the view inside the world
        hw, hh = W / 2 / zoom, H / 2 / zoom
        fx = min(max(fx, hw), W - hw)
        fy = min(max(fy, hh), H - hh)
    shake = cam.get("shake", 0)
    drift = story.get("handheld", 0)
    grade = s.get("grade", story.get("grade", "none"))
    gp = skia.Paint()
    gp.setColorFilter(grade_filter(grade))
    c.saveLayer(None, gp)
    c.save()
    c.translate(W / 2, H / 2)
    c.scale(zoom, zoom)
    c.translate(-fx + math.sin(T * 40) * shake + math.sin(T * 0.7) * drift,
                -fy + math.cos(T * 33) * shake + math.cos(T * 0.53) * drift)
    cam_m = c.getTotalMatrix()
    dof = s.get("dof", 2.5 if zoom > 1.3 else 0)
    if dof:
        bp = skia.Paint()
        bp.setImageFilter(skia.ImageFilters.Blur(dof * zoom, dof * zoom))
        c.saveLayer(None, bp)
    _, lights = scenes.BACKGROUNDS[bgname](c, T, W, H, o)
    if dof:
        c.restore()
    if bgname == "cabin" and o.get("front_seats"):
        pass
    if bgname in ("desk", "room"):
        lights = lights + scenes.desk_front(c, T, o)
    hands = {}
    for i, a in enumerate(_actor_list(s)):
        ch.set_look(a.get("look_as", story.get("hero", "detective")))
        act = a.get("action", "stand")
        x0 = a.get("x", W / 2)
        x1 = a.get("move_to", x0)
        mk = ch.ease(lt / s["dur"]) if a.get("ease_move") else lt / s["dur"]
        x = ch.lerp(x0, x1, mk)
        stand_y = scenes.GROUND - ch.THIGH - ch.SHIN - 14
        y = a.get("y", ACTION_Y.get(act, stand_y) if act not in ("kneel", "pushup", "dig") else stand_y)
        if bgname == "mountain":
            y = scenes.slope_y(x) - ch.THIGH - ch.SHIN - 12
        if a.get("appear_at") is not None and lt < a["appear_at"]:
            continue
        pz = ch.ACTIONS[act](T)
        if a.get("then") and lt > a.get("then_at", s["dur"] / 2):
            q = ch.ACTIONS[a["then"]](T)
            pz = ch.blend(pz, q, ch.ease((lt - a.get("then_at", s["dur"] / 2)) / 0.6))
        if a.get("prop") == "flashlight":  # arm raised, pointing the light ahead
            pz["shL"] = 78 - pz["torso"] + math.sin(T * 1.9) * 3
            pz["elL"] = -6
        sc = a.get("scale", 1.0)
        if act not in ("lie", "fall", "hang") and bgname not in ("sky", "ocean"):  # soft contact shadow
            sp = skia.Paint(AntiAlias=True)
            sp.setShader(skia.GradientShader.MakeRadial((x, scenes.GROUND), 130 * sc, [0x88000000, 0x00000000]))
            c.save()
            c.scale(1, 0.18)
            c.translate(0, scenes.GROUND / 0.18 - scenes.GROUND)
            c.drawCircle(x, scenes.GROUND, 130 * sc, sp)
            c.restore()
        prop = sets_cooper.PROPS.get(a.get("prop"))
        if a.get("chute"):  # parachute canopy above the jumper
            sets_cooper.parachute(c, x, y - ch.TORSO * sc, sc * 1.5)
        if a.get("prop") == "phone":
            prop = scenes.phone_prop
        elif a.get("prop") == "flashlight":
            def prop(cc, hand, ang, _i=i):
                scenes.flashlight_prop(cc, hand, ang)
                hands[_i] = cc.getTotalMatrix().mapXY(*hand)
        ch.draw(c, pz, x, y, scale=sc, facing=a.get("facing", 1),
                expr=a.get("expr", "neutral"), t=T + i * 1.7, look=tuple(a.get("look", (0, 0))),
                prop_hand=prop, blink_seed=i * 1.3)
        if a.get("prop") == "phone":
            lights = lights + [(x - 150 if act == "lie" else x + 40, y - 200 if act != "lie" else y - 60,
                                360, 0xFF8EC9FF, 0.9)]
    ch.set_look(story.get("hero", "detective"))
    if bgname == "court":
        sets_sea.court_front(c)
    if bgname == "bedroom" and any(a.get("action") == "lie" for a in _actor_list(s)):
        scenes.blanket(c, o)
    for (lx, ly, r, colr, inten) in lights:
        scenes.glow(c, lx, ly, r, colr, inten * (0.92 + 0.08 * math.sin(T * 7)))
    if "rain" in s.get("fx", []):
        scenes.rain(c, T, W, H)
    c.restore()
    # darkness + flashlight beam in screen space
    dark = s.get("dark", 0)
    if dark:
        beam = None
        fl = s.get("flashlight")
        if fl and hands:
            src = list(hands.values())[0]
            t0, t1 = fl.get("to", [[W / 2, H / 2]] * 2) if len(fl.get("to", [])) == 2 else (fl["to"][0], fl["to"][0])
            tx = ch.lerp(t0[0], t1[0], k) + math.sin(T * 1.9) * 25
            ty = ch.lerp(t0[1], t1[1], k) + math.cos(T * 1.4) * 18
            tgt = cam_m.mapXY(tx, ty)
            beam = ((src.x(), src.y()), (tgt.x(), tgt.y()), fl.get("spread", 13))
        holes = [(cam_m.mapXY(hx, hy).x(), cam_m.mapXY(hx, hy).y(), r * zoom) for hx, hy, r in s.get("holes", [])]
        scenes.darkness(c, W, H, dark, beam, holes)
    if "dust" in s.get("fx", []):
        scenes.dust(c, T, W, H)
    tint = s.get("tint")
    if tint:
        c.drawRect(skia.Rect.MakeWH(W, H), ch.paint(int(tint, 16)))
    c.restore()  # grade layer


def draw_shot(c, s, lt, T, story=None, nxt=None):
    story = story or {}
    draw_world(c, s, lt, T, story)
    xf = story.get("xfade", 0)
    if nxt is not None and xf and lt > s["dur"] - xf and not s.get("cut"):
        a = (lt - (s["dur"] - xf)) / xf
        lp = skia.Paint()
        lp.setAlphaf(ch.ease(a))
        c.saveLayer(None, lp)
        draw_world(c, nxt, lt - s["dur"], T, story)
        c.restore()
    vignette(c)
    grain(c, T)
    if story.get("letterbox"):
        letterbox(c)
    caption_draw(c, s, lt)
    subtitles_draw(c, s, lt)
    fade_in = s.get("fade_in", 0.0)
    fade_out = s.get("fade_out", 0.0)
    alpha = 0.0
    if fade_in and lt < fade_in:
        alpha = 1 - lt / fade_in
    if fade_out and lt > s["dur"] - fade_out:
        alpha = max(alpha, (lt - (s["dur"] - fade_out)) / fade_out)
    flash = s.get("flash")
    if flash is not None and flash <= lt < flash + 0.12:
        c.drawRect(skia.Rect.MakeWH(W, H), ch.paint(0xCCFFFFFF))
    if alpha > 0:
        c.drawRect(skia.Rect.MakeWH(W, H), ch.paint(skia.Color4f(0, 0, 0, alpha).toColor()))


STORY = [{}]


def frame_at(shots, T, surface):
    c = surface.getCanvas()
    c.clear(0xFF000000)
    for i, s in enumerate(shots):
        if s["start"] <= T < s["start"] + s["dur"]:
            nxt = shots[i + 1] if i + 1 < len(shots) else None
            draw_shot(c, s, T - s["start"], T, STORY[0], nxt)
            break
    return surface


def _render_chunk(args):
    shots, f0, f1, path, vertical, story = args
    STORY[0] = dict(story, letterbox=False) if vertical else story
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
    st = dict(story)
    st['letterbox'] = False
    draw_shot(c, s, lt, s["start"] + lt, st)
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
    parent = os.path.basename(os.path.dirname(os.path.abspath(args.story)))
    if parent != "stories":  # series/<name>/epNN.json -> <name>-epNN
        slug = f"{parent}-{slug}"
    out = os.path.join(ROOT, "output", slug)
    work = os.path.join(out, "work")
    os.makedirs(work, exist_ok=True)
    shots, total = build_timeline(story, work)
    STORY[0] = story
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
        jobs = [(shots, bounds[i], bounds[i + 1], os.path.join(work, f"part{i}{'v' if vertical else ''}.mp4"), vertical, story)
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
    se = story.get("series")
    if se:
        meta["title"] = f"{se['name'].upper()} | Part {se['part']}: {se['episode_title']}"[:100]
        meta["playlist"] = se["name"]
    json.dump(meta, open(os.path.join(out, "metadata.json"), "w"), indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()

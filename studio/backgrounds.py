"""
Backgrounds drawn entirely in code, as 3 parallax layers:

    far  (sky, mountains, back wall)   moves slowly when the camera pans
    mid  (trees, pillars, furniture)   moves at medium speed
    near (ground / floor + details)    moves with the characters

Each preset is a function  preset(W, H, rng, mood) -> dict(far=, mid=, near=, ground=)
Layers are drawn larger than the screen so the camera can pan and zoom.
Add a new place = add one function + register it in PRESETS.
"""
from __future__ import annotations

import math
import random
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

# How much bigger than the screen each layer is drawn (room for pan + zoom)
OVERSCAN = 1.35

MOODS = {
    #           sky top        sky horizon     far tint        mid tint      ground        light
    "day":   [(96, 160, 220), (196, 226, 240), (120, 150, 170), (52, 92, 70), (88, 120, 64), 1.0],
    "dusk":  [(40, 36, 86), (240, 140, 90), (92, 70, 110), (36, 30, 52), (44, 38, 52), 0.8],
    "night": [(8, 12, 30), (34, 48, 86), (30, 40, 66), (14, 20, 34), (22, 26, 36), 0.6],
    "storm": [(20, 24, 30), (60, 66, 76), (44, 50, 58), (24, 28, 32), (34, 36, 40), 0.55],
}


def _gradient(W, H, top, bottom, power=1.0):
    t = np.linspace(0, 1, H)[:, None] ** power
    a = np.array(top, float)[None, None, :]
    b = np.array(bottom, float)[None, None, :]
    g = a + (b - a) * t[:, :, None]
    g = np.repeat(g, W, axis=1)
    return Image.fromarray(np.clip(g, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


def _ridge(rng, W, base_y, rough, n=9):
    """Midpoint-displacement mountain line -> list of (x, y)."""
    pts = [base_y + rng.uniform(-rough, rough), base_y + rng.uniform(-rough, rough)]
    amp = rough
    for _ in range(n):
        new = []
        for i in range(len(pts) - 1):
            new += [pts[i], (pts[i] + pts[i + 1]) / 2 + rng.uniform(-amp, amp)]
        new.append(pts[-1])
        pts, amp = new, amp * 0.55
    step = W / (len(pts) - 1)
    return [(i * step, y) for i, y in enumerate(pts)]


def _pine(d, x, base, h, color):
    w = h * 0.36
    d.rectangle([x - h * 0.025, base - h * 0.15, x + h * 0.025, base], fill=color)
    for k in range(4):
        top = base - h + k * h * 0.2
        bot = base - h * 0.06 - (3 - k) * h * 0.13
        ww = w * (0.45 + k * 0.2)
        d.polygon([(x, top), (x - ww, bot), (x + ww, bot)], fill=color)


def _mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ── presets ───────────────────────────────────────────────────
def forest(W, H, rng, mood="dusk"):
    sky_t, sky_h, far_c, mid_c, gnd, light = MOODS[mood]
    gy = int(H * 0.80)
    far = _gradient(W, H, sky_t, sky_h, 1.3)
    d = ImageDraw.Draw(far)
    if mood in ("night", "dusk"):
        for _ in range(int(W * H / 9000)):
            x, y = rng.uniform(0, W), rng.uniform(0, H * 0.55)
            b = int(rng.uniform(120, 255) * (1 if mood == "night" else 0.6))
            s = rng.choice([1, 1, 1, 2])
            d.ellipse([x, y, x + s, y + s], fill=(b, b, min(255, b + 20), 255))
        mx, my, mr = W * rng.uniform(0.6, 0.8), H * 0.2, H * 0.07
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(glow).ellipse([mx - mr * 3, my - mr * 3, mx + mr * 3, my + mr * 3], fill=(255, 240, 200, 40))
        far.alpha_composite(glow.filter(ImageFilter.GaussianBlur(mr)))
        d.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=(250, 244, 220, 255))
    for k, (yy, rough, tint) in enumerate([(0.52, 0.10, 0.0), (0.62, 0.07, 0.4)]):
        col = _mix(far_c, mid_c, tint)
        pts = _ridge(rng, W, H * yy, H * rough)
        d.polygon(pts + [(W, H), (0, H)], fill=col + (255,))
    mid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dm = ImageDraw.Draw(mid)
    # the mid layer has its own dark ground so tree trunks never show as a "fence" line
    x = 0.0
    while x < W:
        h = rng.uniform(0.30, 0.55) * H
        _pine(dm, x, gy - H * 0.08 + rng.uniform(-6, 6), h, _mix(mid_c, far_c, rng.uniform(0, 0.25)) + (255,))
        x += rng.uniform(40, 140)
    under = _mix(mid_c, gnd, 0.35) + (255,)
    dm.rectangle([0, gy - H * 0.09, W, H], fill=under)
    bx = 0.0
    while bx < W:  # bumpy undergrowth edge
        r = rng.uniform(H * 0.02, H * 0.05)
        dm.ellipse([bx - r, gy - H * 0.09 - r * 0.8, bx + r, gy - H * 0.09 + r * 0.8], fill=under)
        bx += r * rng.uniform(0.9, 1.6)
    near = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dn = ImageDraw.Draw(near)
    dn.rectangle([0, gy, W, H], fill=gnd + (255,))
    dn.line([(0, gy), (W, gy)], fill=_mix(gnd, (255, 255, 255), 0.12) + (255,), width=3)
    for _ in range(int(W / 6)):
        x = rng.uniform(0, W)
        y = rng.uniform(gy, H)
        L = rng.uniform(6, 22) * (0.6 + (y - gy) / (H - gy))
        dn.line([(x, y), (x + rng.uniform(-5, 5), y - L)], fill=_mix(gnd, mid_c, 0.5) + (255,), width=2)
    for _ in range(int(W / 220)):
        x, y = rng.uniform(0, W), rng.uniform(gy + 30, H - 20)
        r = rng.uniform(10, 28)
        dn.ellipse([x - r, y - r * 0.6, x + r, y + r * 0.4], fill=_mix(gnd, (90, 90, 100), 0.5) + (255,))
    # near foreground trees (big, dark) on the edges add depth
    for x in (rng.uniform(-60, W * 0.08), rng.uniform(W * 0.92, W + 60)):
        _pine(dn, x, H + 40, H * 0.95, _mix(mid_c, (0, 0, 0), 0.5) + (255,))
    return {"far": far, "mid": mid, "near": near, "ground": gy / H, "light": light}


def corridor(W, H, rng, mood="night"):
    """Abandoned facility corridor."""
    light = {"day": 1.0, "dusk": 0.85, "night": 0.7, "storm": 0.6}[mood]
    wall = _mix((70, 78, 82), (20, 22, 26), 1 - light)
    gy = int(H * 0.80)
    far = _gradient(W, H, _mix(wall, (0, 0, 0), 0.35), wall, 0.8)
    d = ImageDraw.Draw(far)
    # wall panels and stains
    pw = int(H * 0.28)
    for x in range(0, W, pw):
        d.line([(x, H * 0.12), (x, gy)], fill=_mix(wall, (0, 0, 0), 0.3) + (255,), width=3)
    for _ in range(int(W / 160)):
        x, y = rng.uniform(0, W), rng.uniform(H * 0.25, gy - 40)
        r = rng.uniform(20, 70)
        d.ellipse([x - r, y - r * 0.5, x + r, y + r * 1.4], fill=_mix(wall, (40, 50, 30), 0.35) + (255,))
    far = far.filter(ImageFilter.GaussianBlur(1.5))
    d = ImageDraw.Draw(far)
    d.rectangle([0, 0, W, H * 0.12], fill=_mix(wall, (0, 0, 0), 0.6) + (255,))
    # doors
    x = rng.uniform(80, 300)
    while x < W - 200:
        dw, dh = H * 0.20, H * 0.40
        top = gy - dh
        d.rectangle([x, top, x + dw, gy], fill=_mix(wall, (0, 0, 0), 0.55) + (255,))
        d.rectangle([x + 10, top + 10, x + dw - 10, gy], fill=_mix(wall, (30, 40, 60), 0.5) + (255,))
        d.rectangle([x + dw * 0.25, top + dh * 0.15, x + dw * 0.75, top + dh * 0.35], fill=(30, 36, 44, 255))
        d.ellipse([x + dw - 34, top + dh * 0.55, x + dw - 20, top + dh * 0.55 + 14], fill=(170, 160, 120, 255))
        sign = rng.choice(["B-2", "C-7", "LAB", "D-1", "E-4"])
        d.rectangle([x + dw * 0.3, top - 44, x + dw * 0.7, top - 12], fill=(200, 190, 140, 255))
        d.text((x + dw * 0.5, top - 28), sign, fill=(40, 40, 40, 255), anchor="mm")
        x += rng.uniform(dw * 2.2, dw * 4.5)
    mid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dm = ImageDraw.Draw(mid)
    # pipes along ceiling
    for k, yy in enumerate((0.15, 0.19)):
        c = _mix((110, 96, 80), wall, 0.4 + k * 0.2)
        dm.rectangle([0, H * yy, W, H * yy + 18], fill=c + (255,))
        dm.line([(0, H * yy + 4), (W, H * yy + 4)], fill=_mix(c, (255, 255, 255), 0.25) + (255,), width=3)
        for x in range(int(rng.uniform(0, 300)), W, 420):
            dm.rectangle([x, H * yy - 4, x + 26, H * yy + 22], fill=_mix(c, (0, 0, 0), 0.4) + (255,))
    # ceiling lamps
    for x in range(int(rng.uniform(100, 400)), W, 640):
        dm.polygon([(x - 50, H * 0.12), (x + 50, H * 0.12), (x + 30, H * 0.155), (x - 30, H * 0.155)], fill=(60, 60, 64, 255))
        dm.rectangle([x - 26, H * 0.155, x + 26, H * 0.165], fill=(255, 244, 200, 255))
    near = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dn = ImageDraw.Draw(near)
    floor = _mix((58, 60, 62), (14, 15, 18), 1 - light)
    dn.rectangle([0, gy, W, H], fill=floor + (255,))
    dn.rectangle([0, gy - 16, W, gy], fill=_mix(floor, (0, 0, 0), 0.4) + (255,))
    for x in range(0, W, 160):
        dn.line([(x, gy), (x - (x - W / 2) * 0.25, H)], fill=_mix(floor, (0, 0, 0), 0.25) + (255,), width=2)
    for y in (gy + 50, gy + 120):
        dn.line([(0, y), (W, y)], fill=_mix(floor, (0, 0, 0), 0.25) + (255,), width=2)
    for _ in range(int(W / 300)):  # debris
        x, y = rng.uniform(0, W), rng.uniform(gy + 20, H - 20)
        dn.polygon([(x, y), (x + rng.uniform(10, 40), y - rng.uniform(4, 14)), (x + rng.uniform(20, 50), y + 4)],
                   fill=_mix(floor, (120, 110, 90), 0.4) + (255,))
    return {"far": far, "mid": mid, "near": near, "ground": gy / H, "light": light}


def cabin(W, H, rng, mood="night"):
    """Wooden cabin interior with a window."""
    light = {"day": 1.0, "dusk": 0.85, "night": 0.65, "storm": 0.55}[mood]
    wood = _mix((128, 86, 52), (28, 20, 16), 1 - light)
    gy = int(H * 0.80)
    far = Image.new("RGBA", (W, H), wood + (255,))
    d = ImageDraw.Draw(far)
    for y in range(0, gy, 46):  # log planks
        c = _mix(wood, (0, 0, 0), rng.uniform(0.0, 0.25))
        d.rectangle([0, y, W, y + 44], fill=c + (255,))
        d.line([(0, y + 44), (W, y + 44)], fill=_mix(wood, (0, 0, 0), 0.5) + (255,), width=3)
    for _ in range(int(W / 50)):
        x, y = rng.uniform(0, W), rng.uniform(0, gy)
        d.ellipse([x, y, x + 14, y + 6], fill=_mix(wood, (0, 0, 0), 0.45) + (255,))
    sky_t, sky_h = MOODS[mood][0], MOODS[mood][1]
    for wx in (W * rng.uniform(0.15, 0.3), W * rng.uniform(0.6, 0.8)):
        ww, wh, wy = H * 0.30, H * 0.26, H * 0.22
        win = _gradient(int(ww), int(wh), sky_t, sky_h)
        far.paste(win, (int(wx), int(wy)))
        d.rectangle([wx, wy, wx + ww, wy + wh], outline=(52, 34, 22, 255), width=14)
        d.line([(wx + ww / 2, wy), (wx + ww / 2, wy + wh)], fill=(52, 34, 22, 255), width=10)
        d.line([(wx, wy + wh / 2), (wx + ww, wy + wh / 2)], fill=(52, 34, 22, 255), width=10)
    mid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dm = ImageDraw.Draw(mid)
    # table, shelf, lamp
    tx = W * rng.uniform(0.35, 0.55)
    dm.rectangle([tx, gy - H * 0.20, tx + H * 0.38, gy - H * 0.18], fill=(70, 46, 28, 255))
    for lx in (tx + 14, tx + H * 0.38 - 26):
        dm.rectangle([lx, gy - H * 0.18, lx + 12, gy], fill=(60, 40, 24, 255))
    dm.rectangle([tx + H * 0.05, gy - H * 0.26, tx + H * 0.09, gy - H * 0.20], fill=(255, 214, 120, 255))
    sx = W * rng.uniform(0.75, 0.9)
    dm.rectangle([sx, H * 0.30, sx + H * 0.3, H * 0.32], fill=(70, 46, 28, 255))
    for k in range(5):
        dm.rectangle([sx + 10 + k * 26, H * 0.30 - rng.uniform(40, 70), sx + 30 + k * 26, H * 0.30],
                     fill=rng.choice([(120, 40, 40), (40, 80, 120), (160, 140, 60), (60, 100, 60)]) + (255,))
    near = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dn = ImageDraw.Draw(near)
    fl = _mix(wood, (0, 0, 0), 0.25)
    dn.rectangle([0, gy, W, H], fill=fl + (255,))
    for y in range(gy, H, 34):
        dn.line([(0, y), (W, y)], fill=_mix(fl, (0, 0, 0), 0.4) + (255,), width=2)
    dn.rectangle([W * 0.3, gy + 40, W * 0.55, H - 30], fill=(110, 40, 40, 200))  # rug
    return {"far": far, "mid": mid, "near": near, "ground": gy / H, "light": light}


def void(W, H, rng, mood="night"):
    """Plain gradient (title cards, flashbacks)."""
    top, bot = {"day": ((235, 232, 224), (200, 196, 186)), "dusk": ((60, 30, 50), (16, 10, 20)),
                "night": ((24, 26, 40), (6, 6, 12)), "storm": ((40, 44, 50), (10, 10, 14))}[mood]
    far = _gradient(W, H, top, bot)
    empty = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    return {"far": far, "mid": empty, "near": empty.copy(), "ground": 0.80, "light": 1.0}


PRESETS = {"forest": forest, "corridor": corridor, "cabin": cabin, "void": void}
PARALLAX = {"far": 0.25, "mid": 0.6, "near": 1.0}


@lru_cache(16)
def build(preset: str, mood: str, seed: int, W: int, H: int):
    """Draw (and memory-cache) all layers for one location."""
    if preset not in PRESETS:
        raise ValueError(f"Unknown background preset '{preset}'. Available: {', '.join(PRESETS)}")
    LW, LH = int(W * OVERSCAN * 1.4), int(H * OVERSCAN)  # extra width for horizontal pans
    rng = random.Random(f"{preset}-{mood}-{seed}")
    layers = PRESETS[preset](LW, LH, rng, mood)
    layers["size"] = (LW, LH)
    return layers

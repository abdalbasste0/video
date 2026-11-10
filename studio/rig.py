"""
The stickman rig: turns a pose (angles) into joint positions and draws a
character with a face, emotion, mouth flap, accessory and optional prop.

Drawing trick for smooth lines: each character is drawn on its own small
canvas at 2x (settings: video.supersample) and shrunk with a high-quality
filter before being pasted on the frame. Pillow lines are not anti-aliased,
this gives clean rounded edges cheaply.
"""
from __future__ import annotations

import math
import random

from PIL import Image, ImageDraw

from . import poses as P
from .config import characters_cfg

HEAD_FILL = (247, 243, 235)
FACE_DARK = (34, 30, 38)
EMOTIONS = ["neutral", "happy", "sad", "angry", "scared", "surprised"]


# ── colors ────────────────────────────────────────────────────
def hex_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def shade(rgb, f):
    """f<1 darker, f>1 lighter."""
    if f <= 1:
        return tuple(int(c * f) for c in rgb)
    return tuple(int(c + (255 - c) * (f - 1)) for c in rgb)


def resolve_color(c: str):
    colors = characters_cfg().get("colors", {})
    return hex_rgb(colors.get(c, c))


# ── forward kinematics ───────────────────────────────────────
def solve(pose: dict, H: float, facing: int) -> dict:
    """Return joint positions (pixels) relative to the hip at (0,0), y down."""
    p = P.full(pose)
    B = P.BODY
    f = facing
    j = {"hip": (p["hip"][0] * H * f, p["hip"][1] * H)}
    hx, hy = j["hip"]
    t = math.radians(p["torso"])
    neck = (hx + f * math.sin(t) * B["torso"] * H, hy - math.cos(t) * B["torso"] * H)
    sh = B["shoulder_at"]
    j["neck"] = neck
    j["shoulder"] = (hx + (neck[0] - hx) * sh, hy + (neck[1] - hy) * sh)
    ha = math.radians(p["head"] + p["torso"] * 0.5)
    dist = (B["neck"] + B["head_r"]) * H
    j["head"] = (neck[0] + f * math.sin(ha) * dist, neck[1] - math.cos(ha) * dist)
    j["head_r"] = B["head_r"] * H

    for side in ("near", "far"):
        ua, la = p[f"{side}_arm"]
        dx, dy = P.limb_vec(ua, B["upper_arm"] * H, f)
        elbow = (j["shoulder"][0] + dx, j["shoulder"][1] + dy)
        dx, dy = P.limb_vec(la, B["forearm"] * H, f)
        j[f"{side}_elbow"], j[f"{side}_hand"] = elbow, (elbow[0] + dx, elbow[1] + dy)
        j[f"{side}_hand_angle"] = la
        th, sn = p[f"{side}_leg"]
        dx, dy = P.limb_vec(th, B["thigh"] * H, f)
        knee = (hx + dx, hy + dy)
        dx, dy = P.limb_vec(sn, B["shin"] * H, f)
        j[f"{side}_knee"], j[f"{side}_foot"] = knee, (knee[0] + dx, knee[1] + dy)
    return j


POINT_KEYS = ["hip", "neck", "near_elbow", "near_hand", "far_elbow", "far_hand",
              "near_knee", "near_foot", "far_knee", "far_foot"]


def ground_offset(j: dict, pose: dict) -> float:
    """How far to move the body down so its lowest point touches y=0."""
    if not P.full(pose).get("grounded", True):
        return 0.0
    lowest = max(j[k][1] for k in POINT_KEYS)
    lowest = max(lowest, j["head"][1] + j["head_r"])
    return -lowest


# ── drawing helpers ───────────────────────────────────────────
def _seg(d, a, b, w, color):
    d.line([a, b], fill=color, width=int(w))
    r = w / 2
    for (x, y) in (a, b):
        d.ellipse([x - r, y - r, x + r, y + r], fill=color)


def _limb(d, pts, w, col, outline, ow):
    for i in range(len(pts) - 1):
        _seg(d, pts[i], pts[i + 1], w + 2 * ow, outline)
    for i in range(len(pts) - 1):
        _seg(d, pts[i], pts[i + 1], w, col)


def _arc_pts(cx, cy, rx, ry, a0, a1, n=12):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def draw_face(d, cx, cy, r, facing, emotion="neutral", mouth=0.0, blink=False, look=(0, 0), s=1.0):
    """Eyes, brows and mouth. mouth = 0 (closed) .. 1 (wide open)."""
    f = facing
    fx = cx + f * r * 0.22 + look[0] * r * 0.08
    fy = cy + look[1] * r * 0.10
    lw = max(2, r * 0.07)
    big = emotion in ("scared", "surprised")
    ew, eh = (r * 0.16, r * 0.22) if big else (r * 0.10, r * 0.17)
    if emotion == "angry":
        eh *= 0.7
    eyes = [fx - r * 0.30, fx + r * 0.22] if f > 0 else [fx - r * 0.22, fx + r * 0.30]
    ey = fy - r * 0.12
    for i, ex in enumerate(eyes):
        if blink:
            d.line([(ex - ew, ey), (ex + ew, ey)], fill=FACE_DARK, width=int(lw))
        elif emotion == "happy":
            d.line(_arc_pts(ex, ey + eh * 0.3, ew * 1.1, eh * 0.8, 200, 340), fill=FACE_DARK, width=int(lw * 1.1))
        elif big:
            d.ellipse([ex - ew, ey - eh, ex + ew, ey + eh], fill=(255, 255, 255), outline=FACE_DARK, width=int(lw * 0.8))
            pr = ew * 0.42
            px, py = ex + f * ew * 0.15, ey
            d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=FACE_DARK)
        else:
            d.ellipse([ex - ew, ey - eh, ex + ew, ey + eh], fill=FACE_DARK)
            g = ew * 0.38
            d.ellipse([ex - ew * 0.2 - g, ey - eh * 0.45 - g, ex - ew * 0.2 + g, ey - eh * 0.45 + g], fill=(255, 255, 255))
        # brows: (inner y, outer y) offsets
        by = ey - eh - r * 0.10
        inner_dy, outer_dy = {"neutral": (0, 0), "happy": (-0.06, -0.06), "sad": (-0.12, 0.05),
                              "angry": (0.10, -0.08), "scared": (-0.14, -0.02), "surprised": (-0.16, -0.16)}[emotion]
        inner_is_right = (i == 0)
        x0, x1 = ex - ew * 1.3, ex + ew * 1.3
        y_in, y_out = by + inner_dy * r, by + outer_dy * r
        a, b = ((x0, y_out), (x1, y_in)) if inner_is_right else ((x0, y_in), (x1, y_out))
        d.line([a, b], fill=FACE_DARK, width=int(lw))
    # mouth
    mx, my = fx - f * r * 0.02, fy + r * 0.40
    mw = r * 0.26
    if mouth > 0.08:
        mh = r * (0.06 + 0.30 * min(1.0, mouth))
        w2 = mw * (0.8 + 0.3 * (emotion in ("happy", "surprised")))
        d.ellipse([mx - w2, my - mh, mx + w2, my + mh], fill=(70, 22, 30), outline=FACE_DARK, width=int(lw * 0.7))
        if mh > r * 0.14:
            d.ellipse([mx - w2 * 0.55, my + mh * 0.15, mx + w2 * 0.55, my + mh * 0.95], fill=(214, 92, 104))
    elif emotion == "happy":
        d.line(_arc_pts(mx, my - r * 0.08, mw, r * 0.16, 20, 160), fill=FACE_DARK, width=int(lw))
    elif emotion in ("sad", "angry"):
        d.line(_arc_pts(mx, my + r * 0.10, mw * 0.9, r * 0.12, 200, 340), fill=FACE_DARK, width=int(lw))
    elif emotion == "surprised":
        d.ellipse([mx - r * 0.08, my - r * 0.10, mx + r * 0.08, my + r * 0.10], fill=(70, 22, 30))
    elif emotion == "scared":
        pts = [(mx - mw + i * mw / 3, my + (r * 0.04 if i % 2 else -r * 0.04)) for i in range(7)]
        d.line(pts, fill=FACE_DARK, width=int(lw * 0.9))
    else:
        d.line([(mx - mw * 0.7, my), (mx + mw * 0.7, my)], fill=FACE_DARK, width=int(lw))


def draw_accessory(d, kind, j, col, facing, H, t, layer):
    """layer='back' is drawn behind the body, 'front' after the head."""
    f = facing
    hx, hy = j["head"]
    r = j["head_r"]
    acc = shade(col, 0.6)
    lite = shade(col, 1.45)
    w = max(3, H * 0.012)
    if layer == "back":
        if kind == "backpack":
            sx, sy = j["shoulder"]
            hx2, hy2 = j["hip"]
            cx, cy = (sx + hx2) / 2 - f * H * 0.06, (sy + hy2) / 2 - H * 0.02
            d.rounded_rectangle([cx - H * 0.055, cy - H * 0.09, cx + H * 0.055, cy + H * 0.08], radius=H * 0.025,
                                fill=acc, outline=shade(acc, 0.6), width=int(w))
        if kind == "scarf":
            nx, ny = j["neck"]
            sway = math.sin(t * 5.0) * H * 0.02
            tail = [(nx, ny), (nx - f * H * 0.07, ny + H * 0.03 + sway), (nx - f * H * 0.13, ny + H * 0.05 - sway)]
            d.line(tail, fill=acc, width=int(H * 0.035), joint="curve")
        if kind == "headband":
            sway = math.sin(t * 6.0) * H * 0.012
            bx, by = hx - f * r * 0.95, hy - r * 0.35
            d.line([(bx, by), (bx - f * H * 0.06, by + H * 0.03 + sway)], fill=col, width=int(H * 0.016))
        return
    if kind == "cap":
        d.chord([hx - r * 1.02, hy - r * 1.08, hx + r * 1.02, hy + r * 0.62], 180, 360, fill=col, outline=acc, width=int(w))
        d.rounded_rectangle([min(hx + f * r * 0.4, hx + f * r * 1.45), hy - r * 0.32,
                             max(hx + f * r * 0.4, hx + f * r * 1.45), hy - r * 0.12], radius=r * 0.1, fill=acc)
        d.ellipse([hx - r * 0.1, hy - r * 1.12, hx + r * 0.1, hy - r * 0.92], fill=acc)
    elif kind == "fedora":
        d.rounded_rectangle([hx - r * 1.45, hy - r * 0.62, hx + r * 1.45, hy - r * 0.42], radius=r * 0.1, fill=acc)
        d.polygon([(hx - r * 0.85, hy - r * 0.55), (hx - r * 0.7, hy - r * 1.35), (hx, hy - r * 1.2),
                   (hx + r * 0.7, hy - r * 1.35), (hx + r * 0.85, hy - r * 0.55)], fill=acc)
        d.rectangle([hx - r * 0.84, hy - r * 0.78, hx + r * 0.84, hy - r * 0.6], fill=col)
    elif kind == "beanie":
        d.chord([hx - r * 1.05, hy - r * 1.2, hx + r * 1.05, hy + r * 0.5], 180, 360, fill=col)
        d.rounded_rectangle([hx - r * 1.08, hy - r * 0.48, hx + r * 1.08, hy - r * 0.22], radius=r * 0.1, fill=acc)
        d.ellipse([hx - r * 0.22, hy - r * 1.45, hx + r * 0.22, hy - r * 1.02], fill=lite)
    elif kind == "helmet":
        d.chord([hx - r * 1.12, hy - r * 1.2, hx + r * 1.12, hy + r * 0.55], 180, 360, fill=col, outline=acc, width=int(w))
        lx = hx + f * r * 0.55
        d.ellipse([lx - r * 0.2, hy - r * 0.95, lx + r * 0.2, hy - r * 0.55], fill=(255, 240, 170), outline=acc)
    elif kind == "scarf":
        nx, ny = j["neck"]
        d.rounded_rectangle([nx - H * 0.045, ny - H * 0.012, nx + H * 0.045, ny + H * 0.03], radius=H * 0.015, fill=col,
                            outline=acc, width=int(w * 0.7))
    elif kind == "headband":
        d.line([(hx - r * 0.98, hy - r * 0.35), (hx + r * 0.98, hy - r * 0.35)], fill=col, width=int(r * 0.24))
    elif kind == "glasses":
        ex = hx + f * r * 0.22
        for dx in (-0.30, 0.22) if f > 0 else (-0.22, 0.30):
            cx = ex + dx * r
            d.ellipse([cx - r * 0.2, hy - r * 0.34, cx + r * 0.2, hy + r * 0.06], outline=acc, width=int(w))
        d.line([(ex - r * 0.1, hy - r * 0.16), (ex + r * 0.02, hy - r * 0.16)], fill=acc, width=int(w))
    elif kind == "badge":
        sx, sy = j["shoulder"]
        hx2, hy2 = j["hip"]
        bx, by = sx + (hx2 - sx) * 0.25 + f * H * 0.012, sy + (hy2 - sy) * 0.25
        rr = H * 0.028
        pts = [(bx + rr * (1 if i % 2 == 0 else 0.45) * math.cos(math.radians(-90 + i * 36)),
                by + rr * (1 if i % 2 == 0 else 0.45) * math.sin(math.radians(-90 + i * 36))) for i in range(10)]
        d.polygon(pts, fill=(255, 210, 60), outline=shade((255, 210, 60), 0.6))
    elif kind == "bowtie":
        nx, ny = j["neck"]
        ny += H * 0.015
        s = H * 0.03
        d.polygon([(nx, ny), (nx - s, ny - s * 0.7), (nx - s, ny + s * 0.7)], fill=col, outline=acc)
        d.polygon([(nx, ny), (nx + s, ny - s * 0.7), (nx + s, ny + s * 0.7)], fill=col, outline=acc)


def draw_prop(d, kind, j, side, facing, H):
    """Draw a prop in a hand. Returns (x, y, angle_deg_screen) for effects like the flashlight cone."""
    hx, hy = j[f"{side}_hand"]
    a = j[f"{side}_hand_angle"]
    ang = math.radians(a)
    dx, dy = facing * math.sin(ang), math.cos(ang)
    L = H * 0.10
    if kind == "flashlight":
        tip = (hx + dx * L, hy + dy * L)
        d.line([(hx - dx * L * 0.2, hy - dy * L * 0.2), tip], fill=(40, 40, 46), width=int(H * 0.035))
        d.line([(hx + dx * L * 0.7, hy + dy * L * 0.7), tip], fill=(255, 236, 160), width=int(H * 0.045))
        return tip[0], tip[1], math.degrees(math.atan2(dy, dx))
    if kind == "box":
        s = H * 0.13
        cx, cy = hx + facing * s * 0.3, hy - s * 0.2
        d.rectangle([cx - s, cy - s * 0.8, cx + s, cy + s * 0.6], fill=(181, 131, 84), outline=(110, 74, 40), width=int(H * 0.008))
        d.line([(cx - s, cy - s * 0.1), (cx + s, cy - s * 0.1)], fill=(110, 74, 40), width=int(H * 0.008))
    elif kind == "key":
        d.ellipse([hx - H * 0.02, hy - H * 0.02, hx + H * 0.02, hy + H * 0.02], outline=(255, 205, 60), width=int(H * 0.008))
        d.line([(hx, hy), (hx + dx * L * 0.6, hy + dy * L * 0.6)], fill=(255, 205, 60), width=int(H * 0.009))
    elif kind in ("note", "map"):
        s = H * 0.06
        d.rectangle([hx - s, hy - s * 1.3, hx + s, hy + s * 0.3], fill=(240, 228, 196), outline=(140, 120, 80), width=int(H * 0.005))
    elif kind == "lantern":
        s = H * 0.045
        d.rectangle([hx - s, hy + s * 0.3, hx + s, hy + s * 2.2], fill=(255, 214, 120), outline=(60, 50, 40), width=int(H * 0.007))
        return hx, hy + s * 1.2, 90.0
    return None


# ── main entry ────────────────────────────────────────────────
def render_character(char: dict, pose: dict, H: float, facing: int, emotion="neutral", mouth=0.0,
                     blink=False, t=0.0, prop=None, ss=2):
    """
    Draw one stickman. Returns (RGBA image, anchor_offset, info)
      anchor_offset = where the ground-point under the hip is inside the image
      info = {'head': (x,y), 'prop': (x,y,angle) or None} relative to that anchor
    """
    S = H * ss
    j = solve(pose, S, facing)
    gy = ground_offset(j, pose)
    j = {k: ((v[0], v[1] + gy) if isinstance(v, tuple) else v) for k, v in j.items()}
    pts = [j[k] for k in POINT_KEYS] + [j["head"]]
    margin = S * 0.35
    minx, maxx = min(p[0] for p in pts) - margin, max(p[0] for p in pts) + margin
    miny, maxy = min(p[1] for p in pts) - margin, max(p[1] for p in pts) + margin * 0.5
    W, Hh = int(maxx - minx), int(maxy - miny)
    j = {k: ((v[0] - minx, v[1] - miny) if isinstance(v, tuple) else v) for k, v in j.items()}
    img = Image.new("RGBA", (W, Hh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    col = resolve_color(char.get("color", "royal"))
    out = shade(col, 0.45)
    far = shade(col, 0.72)
    lw, ow = S * 0.042, S * 0.009
    kind = char.get("accessory")
    p = P.full(pose)
    side = p.get("prop_hand", "near")

    draw_accessory(d, kind, j, col, facing, S, t, "back")
    _limb(d, [j["shoulder"], j["far_elbow"], j["far_hand"]], lw, far, out, ow)
    _limb(d, [j["hip"], j["far_knee"], j["far_foot"]], lw, far, out, ow)
    if prop and side == "far":
        draw_prop(d, prop, j, "far", facing, S)
    _limb(d, [j["hip"], j["neck"]], lw * 1.05, col, out, ow)
    _limb(d, [j["hip"], j["near_knee"], j["near_foot"]], lw, col, out, ow)
    # head
    hx, hy, r = j["head"][0], j["head"][1], j["head_r"]
    d.ellipse([hx - r - ow * 1.6, hy - r - ow * 1.6, hx + r + ow * 1.6, hy + r + ow * 1.6], fill=out)
    d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=HEAD_FILL, outline=col, width=int(lw * 0.55))
    face_dir = -facing if p.get("face_flip") else facing
    draw_face(d, hx, hy, r * 0.94, face_dir, emotion, mouth, blink, look=(0, p["head"] / 40.0))
    draw_accessory(d, kind, j, col, face_dir, S, t, "front")
    _limb(d, [j["shoulder"], j["near_elbow"], j["near_hand"]], lw, col, out, ow)
    prop_info = None
    if prop and side == "near":
        prop_info = draw_prop(d, prop, j, "near", facing, S)

    if ss != 1:
        img = img.resize((max(1, W // ss), max(1, Hh // ss)), Image.LANCZOS)
    ax, ay = (-minx) / ss, (-miny) / ss  # where (hip-x, ground) sits in the image
    info = {"head": ((j["head"][0]) / ss - ax, j["head"][1] / ss - ay), "prop": None, "head_r": r / ss}
    if prop_info:
        info["prop"] = (prop_info[0] / ss - ax, prop_info[1] / ss - ay, prop_info[2])
    return img, (ax, ay), info


def blink_at(seed: str, t: float) -> bool:
    """Deterministic natural blinking every 2-6 s (0.12 s long)."""
    rng = random.Random(seed)
    tt = rng.uniform(0.5, 3)
    while tt < t + 1:
        if tt <= t < tt + 0.12:
            return True
        tt += rng.uniform(2, 6)
    return False

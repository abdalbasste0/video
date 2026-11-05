"""Simple stickman frame renderer with Pillow (no external service needed).

Draws a background in the scene's mood colours plus a stick figure in the requested pose.
The editing bot then adds slow motion and zoom (Ken Burns), and the subtitles are added later.
To swap in custom illustrations, put an image at assets/stickman/<pose>.png and it will be used instead.
"""
from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from .config import ROOT

MOOD_COLORS = {
    "suspense": ((18, 18, 32), (60, 40, 80)),
    "dramatic": ((40, 8, 8), (120, 30, 20)),
    "calm": ((200, 225, 240), (250, 250, 245)),
    "happy": ((255, 230, 150), (255, 250, 230)),
    "sad": ((60, 70, 90), (120, 130, 150)),
}

# Joint points relative to the hip, in units of the figure size (x to the right, y downward)
# shoulders=(0,-1), and each limb is defined by an elbow/knee point and a hand/foot point
POSES: dict[str, dict[str, tuple[tuple[float, float], tuple[float, float]]]] = {
    "standing": {"la": ((-0.25, -0.6), (-0.3, -0.2)), "ra": ((0.25, -0.6), (0.3, -0.2)),
                 "ll": ((-0.15, 0.45), (-0.2, 0.9)), "rl": ((0.15, 0.45), (0.2, 0.9))},
    "walking": {"la": ((-0.2, -0.6), (-0.05, -0.25)), "ra": ((0.25, -0.65), (0.4, -0.35)),
                "ll": ((-0.25, 0.4), (-0.35, 0.9)), "rl": ((0.2, 0.45), (0.15, 0.9))},
    "running": {"la": ((-0.35, -0.75), (-0.2, -1.0)), "ra": ((0.35, -0.6), (0.55, -0.85)),
                "ll": ((-0.4, 0.3), (-0.6, 0.75)), "rl": ((0.3, 0.35), (0.25, 0.9))},
    "thinking": {"la": ((-0.25, -0.6), (-0.3, -0.2)), "ra": ((0.35, -0.55), (0.12, -1.2)),
                 "ll": ((-0.15, 0.45), (-0.2, 0.9)), "rl": ((0.15, 0.45), (0.2, 0.9))},
    "shocked": {"la": ((-0.45, -1.1), (-0.55, -1.5)), "ra": ((0.45, -1.1), (0.55, -1.5)),
                "ll": ((-0.25, 0.45), (-0.35, 0.9)), "rl": ((0.25, 0.45), (0.35, 0.9))},
    "pointing": {"la": ((-0.25, -0.6), (-0.3, -0.2)), "ra": ((0.45, -0.95), (0.9, -1.0)),
                 "ll": ((-0.15, 0.45), (-0.2, 0.9)), "rl": ((0.15, 0.45), (0.2, 0.9))},
    "sitting": {"la": ((-0.25, -0.55), (0.0, -0.2)), "ra": ((0.25, -0.55), (0.35, -0.2)),
                "ll": ((0.45, 0.0), (0.45, 0.5)), "rl": ((0.5, 0.05), (0.55, 0.5))},
    "sad": {"la": ((-0.15, -0.55), (-0.18, -0.1)), "ra": ((0.15, -0.55), (0.18, -0.1)),
            "ll": ((-0.1, 0.45), (-0.12, 0.9)), "rl": ((0.1, 0.45), (0.12, 0.9))},
    "happy": {"la": ((-0.45, -1.05), (-0.5, -1.45)), "ra": ((0.45, -1.05), (0.5, -1.45)),
              "ll": ((-0.2, 0.45), (-0.3, 0.9)), "rl": ((0.2, 0.45), (0.3, 0.9))},
}


def _gradient(size: tuple[int, int], top: tuple, bottom: tuple) -> Image.Image:
    w, h = size
    img = Image.new("RGB", size)
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        d.line([(0, y), (w, y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return img


def render(pose: str, mood: str, out: Path, size: tuple[int, int], seed: int = 0) -> Path:
    custom = ROOT / "assets" / "stickman" / f"{pose}.png"
    bg_top, bg_bottom = MOOD_COLORS.get(mood, MOOD_COLORS["suspense"])
    img = _gradient(size, bg_top, bg_bottom)
    w, h = size
    d = ImageDraw.Draw(img)
    dark_bg = sum(bg_top) < 300
    ink = (245, 245, 245) if dark_bg else (20, 20, 20)

    # Floor
    floor_y = int(h * 0.82)
    d.line([(0, floor_y), (w, floor_y)], fill=ink, width=max(3, h // 200))

    if custom.exists():
        fig = Image.open(custom).convert("RGBA")
        fig.thumbnail((int(w * 0.6), int(h * 0.7)))
        img.paste(fig, ((w - fig.width) // 2, floor_y - fig.height), fig)
    else:
        rnd = random.Random(seed)
        unit = h * 0.22
        hip = (w * (0.5 + rnd.uniform(-0.12, 0.12)), floor_y - unit * 0.9)
        if pose == "sitting":
            hip = (hip[0], floor_y - unit * 0.5)
        p = POSES.get(pose, POSES["standing"])
        lw = max(6, int(unit * 0.07))

        def pt(rel):
            return (hip[0] + rel[0] * unit, hip[1] + rel[1] * unit)

        shoulder = pt((0, -1.0))
        neck = pt((0, -1.15))
        d.line([hip, neck], fill=ink, width=lw)
        r = unit * 0.28
        head_c = pt((0, -1.15 - 0.28))
        d.ellipse([head_c[0] - r, head_c[1] - r, head_c[0] + r, head_c[1] + r], outline=ink, width=lw)
        # Simple facial expression
        eye_y = head_c[1] - r * 0.15
        for dx in (-0.35, 0.35):
            d.ellipse([head_c[0] + dx * r - lw * 0.6, eye_y - lw * 0.6, head_c[0] + dx * r + lw * 0.6, eye_y + lw * 0.6], fill=ink)
        mouth_box = [head_c[0] - r * 0.4, head_c[1] + r * 0.1, head_c[0] + r * 0.4, head_c[1] + r * 0.6]
        if pose in ("happy",):
            d.arc(mouth_box, 20, 160, fill=ink, width=max(2, lw // 2))
        elif pose in ("sad",):
            d.arc([mouth_box[0], mouth_box[1] + r * 0.3, mouth_box[2], mouth_box[3] + r * 0.3], 200, 340, fill=ink, width=max(2, lw // 2))
        elif pose == "shocked":
            d.ellipse([head_c[0] - r * 0.15, head_c[1] + r * 0.2, head_c[0] + r * 0.15, head_c[1] + r * 0.55], outline=ink, width=max(2, lw // 2))
        else:
            d.line([(head_c[0] - r * 0.3, head_c[1] + r * 0.4), (head_c[0] + r * 0.3, head_c[1] + r * 0.4)], fill=ink, width=max(2, lw // 2))
        for limb in ("la", "ra"):
            mid, end = p[limb]
            d.line([shoulder, pt(mid), pt(end)], fill=ink, width=lw, joint="curve")
        for limb in ("ll", "rl"):
            mid, end = p[limb]
            d.line([hip, pt(mid), pt(end)], fill=ink, width=lw, joint="curve")

    # Soft vignette for a cinematic look
    vignette = Image.new("L", size, 0)
    ImageDraw.Draw(vignette).ellipse([-w * 0.2, -h * 0.2, w * 1.2, h * 1.2], fill=255)
    vignette = vignette.filter(ImageFilter.GaussianBlur(min(size) // 8))
    img = Image.composite(img, Image.new("RGB", size, (0, 0, 0)), vignette)

    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return out

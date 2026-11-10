"""
Light & weather effects applied to a finished frame (numpy array, HxWx3 float 0..255).

  darkness   0..1  how dark the scene is (1 = almost black)
  flashlight cone of light from a character's flashlight
  alarm      red pulsing emergency light
  rain       falling rain streaks
  flicker    broken-lamp brightness flicker
  fog        drifting low fog
  vignette   darker corners (cinematic)
"""
from __future__ import annotations

import math
import random
from functools import lru_cache

import numpy as np


@lru_cache(4)
def _grid(W, H, step):
    ys, xs = np.mgrid[0:H:step, 0:W:step].astype(np.float32)
    return xs, ys


@lru_cache(8)
def vignette_mask(W, H, strength):
    xs, ys = _grid(W, H, 1)
    nx, ny = (xs / W - 0.5) * 2, (ys / H - 0.5) * 2
    r = np.sqrt(nx ** 2 * 0.8 + ny ** 2)
    m = 1 - strength * np.clip(r - 0.45, 0, 1) ** 1.6
    return m[..., None].astype(np.float32)


def _upsample(mask, W, H, step):
    """Nearest-neighbour upsample of a coarse mask then light blur via repeat."""
    m = np.repeat(np.repeat(mask, step, axis=0), step, axis=1)[:H, :W]
    return m


def light_cone(W, H, ox, oy, angle_deg, length, spread_deg=24, step=4):
    """Soft cone mask 0..1 starting at (ox, oy) pointing at angle (screen degrees, 0 = right, 90 = down)."""
    xs, ys = _grid(W, H, step)
    dx, dy = xs - ox, ys - oy
    dist = np.sqrt(dx * dx + dy * dy) + 1e-3
    a = math.radians(angle_deg)
    cosang = (dx * math.cos(a) + dy * math.sin(a)) / dist
    edge = math.cos(math.radians(spread_deg))
    ang_term = np.clip((cosang - edge) / (1 - edge), 0, 1) ** 0.7
    dist_term = np.clip(1 - dist / length, 0, 1) ** 0.8
    core = np.clip(1 - dist / (length * 0.08), 0, 1)
    m = np.maximum(ang_term * dist_term, core * 0.8)
    return _upsample(m, W, H, step)[..., None]


def radial_glow(W, H, ox, oy, radius, step=4):
    xs, ys = _grid(W, H, step)
    d = np.sqrt((xs - ox) ** 2 + (ys - oy) ** 2)
    return _upsample(np.clip(1 - d / radius, 0, 1) ** 1.5, W, H, step)[..., None]


def lighting(W: int, H: int, fx: dict, t: float, lights: list):
    """
    Light mask (H, W, 1) with values ~0..1.15, or None when the scene is fully lit.
    lights: [(x, y, angle, kind)] screen-space light sources from props (flashlight/lantern).
    """
    darkness = float(fx.get("darkness", 0))
    if fx.get("flicker"):
        rng = random.Random(int(t * 12))
        if rng.random() < 0.18:
            darkness = min(1.0, darkness + rng.uniform(0.15, 0.4))
    if darkness <= 0:
        return None, 0.0
    lit = np.full((H, W, 1), 1 - 0.85 * darkness, np.float32)
    for (x, y, ang, kind) in lights:
        if kind == "flashlight":
            lit = np.maximum(lit, light_cone(W, H, x, y, ang, length=W * 0.55) * 1.15)
        elif kind == "lantern":
            lit = np.maximum(lit, radial_glow(W, H, x, y, W * 0.22) * 1.1)
    return lit, darkness


def post(frame: np.ndarray, fx: dict, t: float) -> np.ndarray:
    """Alarm light, fog and vignette on the composed frame (float32 HxWx3)."""
    H, W = frame.shape[:2]
    if fx.get("alarm"):
        pulse = 0.5 + 0.5 * math.sin(t * 2 * math.pi * fx.get("alarm_hz", 1.0))
        a = 0.12 + 0.28 * pulse
        frame = frame * (1 - a) + np.array([220, 20, 30], np.float32) * a * (frame.mean(axis=2, keepdims=True) / 255 * 0.6 + 0.4)
    if fx.get("fog"):
        xs, ys = _grid(W, H, 8)
        f = float(fx["fog"]) * np.clip((ys / H - 0.55) * 2.2, 0, 1) * (0.75 + 0.25 * np.sin(xs / 140 + t * 0.6))
        f = _upsample(f, W, H, 8)[..., None]
        frame = frame * (1 - f) + 190 * f
    v = fx.get("vignette", 0.35)
    if v:
        frame = frame * vignette_mask(W, H, float(v))
    return frame


# Characters are never darkened below this (cartoon "rim light" rule) so viewers always see them.
CHARACTER_MIN_LIGHT = 0.55


def draw_rain(draw, W, H, t, intensity=1.0, seed=0):
    """Rain streaks drawn with PIL (on the final image)."""
    rng = random.Random(seed * 100003 + int(t * 24))
    n = int(260 * intensity)
    for _ in range(n):
        x, y = rng.uniform(-100, W), rng.uniform(-50, H)
        L = rng.uniform(25, 60)
        draw.line([(x, y), (x + L * 0.25, y + L)], fill=(190, 205, 230), width=rng.choice([1, 1, 2]))

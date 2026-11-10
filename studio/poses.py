"""
Pose library + smooth interpolation.

A POSE is a set of limb angles in degrees (easy to edit by hand in assets/poses/*.json):

    0   = limb points straight DOWN
    90  = limb points FORWARD (the way the stickman faces)
    180 = limb points UP
    -90 = limb points BACKWARD

  torso / head : 0 = upright, positive = lean forward, negative = lean back
  near_arm / far_arm : [upper arm, forearm]
  near_leg / far_leg : [thigh, shin]
  hip : [dx, dy] extra hip offset in body-heights (rarely needed)
  grounded : true -> lowest body point is placed on the floor automatically

A pose FILE is either
  {"name": "point", "type": "pose", "pose": {...}}
or a looping CYCLE (walk, run, talk...):
  {"name": "walk", "type": "cycle", "duration": 1.0, "keys": [{...}, {...}, ...]}
"""
from __future__ import annotations

import json
import math
from functools import lru_cache

from .config import ASSETS, StudioError

ANGLE_KEYS = ["torso", "head"]
PAIR_KEYS = ["near_arm", "far_arm", "near_leg", "far_leg"]

NEUTRAL = {
    "torso": 0, "head": 0,
    "near_arm": [-8, -4], "far_arm": [8, 4],
    "near_leg": [4, 0], "far_leg": [-4, 0],
    "hip": [0, 0], "grounded": True,
}

# Body proportions in "body heights" (total height ~ 1.0)
BODY = {
    "head_r": 0.105, "neck": 0.035, "torso": 0.30, "shoulder_at": 0.86,
    "upper_arm": 0.165, "forearm": 0.155, "thigh": 0.215, "shin": 0.215,
}


# ── easing ────────────────────────────────────────────────────
def ease_in_out(t: float) -> float:
    """Smooth start and end (cubic). t in 0..1."""
    t = max(0.0, min(1.0, t))
    return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def ease_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def ease_in(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t ** 3


EASINGS = {"linear": lambda t: max(0.0, min(1.0, t)), "in_out": ease_in_out, "out": ease_out, "in": ease_in}


# ── pose math ─────────────────────────────────────────────────
def full(p: dict) -> dict:
    """Fill missing keys from the neutral pose."""
    out = json.loads(json.dumps(NEUTRAL))
    out.update(p or {})
    return out


def lerp_pose(a: dict, b: dict, t: float) -> dict:
    a, b = full(a), full(b)
    out = dict(b)  # non-numeric flags (grounded, face_flip...) come from target
    for k in ANGLE_KEYS:
        out[k] = a[k] + (b[k] - a[k]) * t
    for k in PAIR_KEYS + ["hip"]:
        out[k] = [a[k][i] + (b[k][i] - a[k][i]) * t for i in range(2)]
    if t < 0.5:
        out["grounded"] = a.get("grounded", True)
    return out


def _catmull(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)


def spline_pose(p0, p1, p2, p3, t) -> dict:
    """Catmull-Rom between p1 and p2 - very smooth for looping cycles."""
    p0, p1, p2, p3 = (full(x) for x in (p0, p1, p2, p3))
    out = dict(p1)
    for k in ANGLE_KEYS:
        out[k] = _catmull(p0[k], p1[k], p2[k], p3[k], t)
    for k in PAIR_KEYS + ["hip"]:
        out[k] = [_catmull(p0[k][i], p1[k][i], p2[k][i], p3[k][i], t) for i in range(2)]
    return out


# ── library ───────────────────────────────────────────────────
@lru_cache(None)
def library() -> dict:
    folder = ASSETS / "poses"
    lib = {}
    for f in sorted(folder.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise StudioError(f"Pose file {f.name} is not valid JSON: {e}") from e
        lib[data["name"]] = data
    if not lib:
        raise StudioError("No poses found in assets/poses/. Run `python make.py doctor`.")
    for name, d in lib.items():  # pre-compute walking speed for cycles
        if d.get("type") == "cycle" and d.get("stride", "auto") == "auto":
            d["stride"] = auto_stride(d)
    return lib


def get(name: str) -> dict:
    lib = library()
    if name not in lib:
        raise StudioError(f"Pose '{name}' does not exist. Available: {', '.join(sorted(lib))}")
    return lib[name]


def sample(name: str, t: float) -> dict:
    """Pose `name` at time t seconds (cycles loop)."""
    d = get(name)
    if d.get("type") != "cycle":
        return full(d["pose"])
    keys = d["keys"]
    n = len(keys)
    u = (t / d["duration"]) % 1.0 * n
    i = int(u) % n
    return spline_pose(keys[(i - 1) % n], keys[i], keys[(i + 1) % n], keys[(i + 2) % n], u - int(u))


def first_key(name: str) -> dict:
    d = get(name)
    return full(d["keys"][0] if d.get("type") == "cycle" else d["pose"])


def limb_vec(angle_deg: float, length: float, facing: int):
    a = math.radians(angle_deg)
    return facing * math.sin(a) * length, math.cos(a) * length


def auto_stride(cycle: dict) -> float:
    """Distance (body heights) travelled per cycle so feet don't slide.
    Measured as 2x the horizontal gap between feet at the first key (contact pose)."""
    k = full(cycle["keys"][0])
    def foot_x(leg):
        x1, _ = limb_vec(leg[0], BODY["thigh"], 1)
        x2, _ = limb_vec(leg[1], BODY["shin"], 1)
        return x1 + x2
    return round(2 * abs(foot_x(k["near_leg"]) - foot_x(k["far_leg"])), 4)

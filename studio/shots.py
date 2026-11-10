"""
Shot description format + timeline evaluation.

A SHOT is plain JSON (written by the Storyboard department or by demo.py):

{
  "id": "S001",
  "duration": 4.5,                                  seconds
  "bg": {"preset": "forest", "mood": "dusk", "seed": 3},
  "camera": {"from": {"x": 0.5, "y": 0.5, "zoom": 1.0},
             "to":   {"x": 0.55, "y": 0.52, "zoom": 1.2},
             "ease": "in_out",
             "shake": [{"t": 2.0, "dur": 0.6, "amp": 14}]},
  "actors": [
    {"char": "hero", "height": 0.30, "x": 0.35, "facing": 1, "prop": "flashlight",
     "actions": [ {"t0": 0, "t1": 2.5, "do": "walk", "to": 0.55},
                  {"t0": 2.5, "t1": 4.5, "do": "pose", "pose": "talk"} ],
     "emotions": [ {"t": 0, "e": "neutral"}, {"t": 3.0, "e": "scared"} ] }
  ],
  "fx":   {"darkness": 0.0, "alarm": false, "rain": false, "fog": 0, "flicker": false, "vignette": 0.35},
  "text": [ {"t0": 0.2, "t1": 3.0, "text": "...", "x": 0.5, "y": 0.2, "size": 90} ],
  "speech": [ {"speaker": "hero", "t0": 0.4, "env": [0.0, 0.3, ...]} ]     mouth envelope @ fps
}

x / y positions are fractions of the WORLD (world is 1.4 screens wide, 1 screen high).
"""
from __future__ import annotations

import math
import random

from . import poses as P

WORLD_W = 1.4      # world width in screen-widths (room to pan)
BLEND = 0.28       # seconds to blend between two actions' poses

CAST_SCHEMA = {
    "characters": [{"key": "hero", "name": "...", "role": "hero|ally|antagonist|extra",
                    "color": "royal", "accessory": "cap", "voice": "hero"}]
}


def lerp(a, b, t):
    return a + (b - a) * t


def camera_at(cam: dict, t: float, duration: float):
    """Return camera (x, y, zoom) in world fractions at time t."""
    cam = cam or {}
    a = {"x": 0.5, "y": 0.5, "zoom": 1.0, **(cam.get("from") or {})}
    b = {**a, **(cam.get("to") or {})}
    e = P.EASINGS[cam.get("ease", "in_out")](t / max(duration, 1e-6))
    x, y, z = lerp(a["x"], b["x"], e), lerp(a["y"], b["y"], e), lerp(a["zoom"], b["zoom"], e)
    sx = sy = 0.0
    for s in cam.get("shake", []):
        dt = t - s["t"]
        if 0 <= dt <= s.get("dur", 0.5):
            decay = 1 - dt / s.get("dur", 0.5)
            amp = s.get("amp", 12) * decay
            rng = random.Random(int(t * 48))
            sx += rng.uniform(-amp, amp)
            sy += rng.uniform(-amp, amp)
    return x, y, max(1.0, z), sx, sy


def _action_state(actor: dict, t: float, H_world: float):
    """Return (pose_name, local_time, x, facing) for one action at time t, plus the action index."""
    x = actor.get("x", 0.5)
    facing = actor.get("facing", 1)
    acts = actor.get("actions") or [{"t0": 0, "t1": 1e9, "do": "pose", "pose": "idle"}]
    idx = 0
    for i, a in enumerate(acts):
        if t >= a["t0"]:
            idx = i
    # walk through actions up to idx to accumulate position
    states = []
    for i, a in enumerate(acts[: idx + 1]):
        lt = (min(t, a["t1"]) - a["t0"])
        if a["do"] in ("walk", "run", "sneak"):
            frm = x
            to = a.get("to", x)
            if to != frm:
                facing = 1 if to > frm else -1
            facing = a.get("facing", facing)
            span = max(a["t1"] - a["t0"], 1e-3)
            u = max(0.0, min(1.0, lt / span))
            x = frm + (to - frm) * u
            dist = abs(to - frm) * u * WORLD_W  # in screen widths
            cyc = P.get(a.get("pose", a["do"]))
            stride = cyc.get("stride", 0.5) or 0.5
            # phase from distance travelled -> feet never slide
            phase_time = (dist / max(stride * H_world, 1e-6)) * cyc["duration"]
            states.append((a.get("pose", a["do"]), phase_time, x, facing))
        else:
            facing = a.get("facing", facing)
            states.append((a.get("pose", "idle"), lt, x, facing))
    return states, acts, idx


def actor_at(actor: dict, t: float, screen_aspect=16 / 9):
    """
    Pose dict, x (world fraction), facing, emotion for an actor at time t.
    Blends smoothly from the previous action's pose for BLEND seconds.
    """
    H_world = actor.get("height", 0.30) / screen_aspect  # body height in screen-widths
    states, acts, idx = _action_state(actor, t, H_world)
    name, lt, x, facing = states[-1]
    pose = P.sample(name, lt)
    t0 = acts[idx]["t0"]
    if idx > 0 and t - t0 < BLEND:
        pname, plt, _, _ = states[-2]
        prev = P.sample(pname, plt + (t - t0))
        pose = P.lerp_pose(prev, pose, P.ease_in_out((t - t0) / BLEND))
    emotion = "neutral"
    for e in actor.get("emotions", []):
        if t >= e["t"]:
            emotion = e["e"]
    return pose, x, facing, emotion


def mouth_at(speech: list, speaker: str, t: float, fps: int) -> float:
    """Mouth openness 0..1 from voice amplitude envelopes."""
    v = 0.0
    for s in speech or []:
        if s["speaker"] != speaker:
            continue
        i = int((t - s["t0"]) * fps)
        env = s.get("env", [])
        if 0 <= i < len(env):
            v = max(v, env[i])
    return v


def static_seconds(shot: dict) -> float:
    """Rough QC helper: seconds the shot shows no movement (no camera move, all actors still, no speech)."""
    cam = shot.get("camera", {})
    moving_cam = cam.get("to") and cam.get("to") != cam.get("from")
    has_motion = any(a["do"] in ("walk", "run", "sneak") or P.get(a.get("pose", "idle")).get("type") == "cycle"
                     for ac in shot.get("actors", []) for a in ac.get("actions", []))
    if moving_cam or has_motion or shot.get("speech"):
        return 0.0
    return float(shot.get("duration", 0))

"""Editor Agent — canvas, main track aligned to voice timestamps, rhythm cuts,
transitions, and slow Ken-Burns zoom keyframes on still images.

Writes draft/timeline.json: an engine-neutral timeline (seconds) that the
Motion/Color/VFX/Sound agents enrich, and that is compiled into
  • a CapCut draft  (capcut/draft_builder.py)
  • an FFmpeg render (render_agent.py, phone mode)
"""
from __future__ import annotations

from .base import BaseAgent

TAIL = 0.6            # seconds of picture after the last word
MAX_SHOT = 4.2        # longer scenes get a rhythm cut (punch-in)
TRANSITION_CYCLE = ["fade", "zoom", "slide", "fade", "whip"]


class EditorAgent(BaseAgent):
    name = "editor"

    def run(self) -> dict:
        ts = self.p.read_json("voice", "timestamps.json")
        assets = self.p.read_json("assets", "assets.json")
        w, h = self.s.resolution(self.ctx.fmt)
        fps = int(self.s.get("render.fps", 30))
        ov = self.ctx.overrides("editor")
        zoom = float(ov.get("ken_burns_zoom", 0.12))
        use_transitions = ov.get("transitions", True)

        scenes = ts["scenes"]
        total = round(ts["duration"] + TAIL, 3)
        clips = []
        for i, sc in enumerate(scenes):
            start = 0.0 if i == 0 else sc["start"]
            end = scenes[i + 1]["start"] if i + 1 < len(scenes) else total
            asset = assets["scenes"][sc["id"]]
            for k, (a, b) in enumerate(self._rhythm_split(start, end, sc)):
                kb = None
                if asset["kind"] == "image" or k > 0:
                    # alternate push-in / pull-out and drift direction for variety
                    s0, s1 = (1.0, 1.0 + zoom) if (i + k) % 2 == 0 else (1.0 + zoom, 1.0)
                    dx = 0.03 if (i % 3) == 1 else (-0.03 if (i % 3) == 2 else 0.0)
                    kb = {"scale": [s0, s1], "x": [0.0, dx], "y": [0.0, 0.0]}
                source_start = 0.0
                if asset["kind"] == "video" and asset.get("duration"):
                    source_start = min(max(0.0, asset["duration"] - (b - a)), (a - start))
                clips.append({
                    "id": f"{sc['id']}_c{k + 1}",
                    "scene": sc["id"],
                    "path": asset["path"],
                    "kind": asset["kind"],
                    "start": round(a, 3),
                    "duration": round(b - a, 3),
                    "source_start": round(source_start, 3),
                    "source_duration": asset.get("duration"),
                    "ken_burns": kb,
                    "transition_out": None,
                    "adjust": {},
                })
            if use_transitions and i + 1 < len(scenes):
                clips[-1]["transition_out"] = TRANSITION_CYCLE[i % len(TRANSITION_CYCLE)]

        timeline = {
            "video_id": self.ctx.video_id,
            "fmt": self.ctx.fmt, "width": w, "height": h, "fps": fps,
            "duration": total,
            "video": clips,
            "texts": [], "overlays": [], "effects": [], "filter": None, "audio": [],
        }
        self.p.write_json("draft", "timeline.json", timeline)
        self.info(f"main track: {len(clips)} clips over {total:.2f}s ({w}x{h}@{fps})")
        return timeline

    @staticmethod
    def _rhythm_split(start: float, end: float, scene: dict) -> list[tuple[float, float]]:
        """Split long scenes on a word boundary near the middle → rhythm-based cut."""
        if end - start <= MAX_SHOT or len(scene["words"]) < 4:
            return [(start, end)]
        mid = (start + end) / 2
        cut = min((w["start"] for w in scene["words"][1:]), key=lambda t: abs(t - mid))
        if cut - start < 1.2 or end - cut < 1.2:
            return [(start, end)]
        return [(start, cut), (cut, end)]

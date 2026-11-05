"""VFX Agent — tasteful effect tracks (grain, vignette, light leak on the hook…)."""
from __future__ import annotations

from .base import BaseAgent

INTENSITY = {"subtle": 0.35, "medium": 0.6, "off": 0.0}


class VFXAgent(BaseAgent):
    name = "vfx"

    def run(self) -> dict:
        tl = self.p.read_json("draft", "timeline.json")
        ov = self.ctx.overrides("vfx")
        enabled = ov.get("enabled", self.s.get("vfx.enabled", True))
        level = ov.get("intensity", self.s.get("vfx.intensity", "subtle"))
        names = ov.get("effects", self.s.get("vfx.effects", []))
        lib = self.s.effects.get("video_effects", {})
        effects = []
        if enabled and INTENSITY.get(level, 0) > 0:
            for key in names:
                if key not in lib:
                    self.warn(f"effect '{key}' not in effects_library.json → skipped")
                    continue
                effects.append({"key": key, "start": 0.0, "duration": tl["duration"],
                                "intensity": INTENSITY[level]})
            # a short accent on the hook if the library has one (never on the whole video)
            if "light_leak" in lib and lib["light_leak"].get("resource_id"):
                effects.append({"key": "light_leak", "start": 0.0, "duration": min(1.2, tl["duration"]),
                                "intensity": INTENSITY[level]})
        tl["effects"] = effects
        self.p.write_json("draft", "timeline.json", tl)
        self.info(f"vfx: {[e['key'] for e in effects]} at '{level}'")
        return tl

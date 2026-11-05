"""Colorist Agent — per-clip Adjust (shot matching) + one channel look
(filter or .cube LUT) on an adjustment layer covering the whole timeline."""
from __future__ import annotations

from statistics import median

from .. import media
from .base import BaseAgent

TARGET_LUMA = 118.0   # mid-grey-ish target for consistent exposure across shots


class ColoristAgent(BaseAgent):
    name = "colorist"

    def run(self) -> dict:
        tl = self.p.read_json("draft", "timeline.json")
        base = dict(self.s.get("color.adjust", {}))
        for k, v in self.ctx.overrides("colorist").items():
            if k in base:
                base[k] = max(-50, min(50, base[k] + v))

        # measure each source once, then match exposure toward the median shot
        lumas = {}
        for c in tl["video"]:
            if c["path"] not in lumas:
                lumas[c["path"]] = media.mean_luma(c["path"], at=0.0 if c["kind"] == "image" else 0.5)
        valid = [v for v in lumas.values() if v is not None]
        ref = median(valid) if valid else TARGET_LUMA
        ref = (ref + TARGET_LUMA) / 2

        for c in tl["video"]:
            adj = dict(base)
            y = lumas.get(c["path"])
            if y is not None:
                # ±1 luma ≈ ±0.35 CapCut brightness units, clamped to keep it natural
                adj["brightness"] = round(max(-25, min(25, adj.get("brightness", 0) + (ref - y) * 0.35)), 1)
            c["adjust"] = adj

        lut = self.s.get("color.lut_file") or ""
        tl["filter"] = {
            "key": self.ctx.overrides("colorist").get("filter_key") or self.s.get("color.filter_key", "channel_look"),
            "intensity": float(self.s.get("color.filter_intensity", 0.6)),
            "lut": str(self.s.root / "library" / "luts" / lut) if lut else "",
            "start": 0.0, "duration": tl["duration"],
        }
        self.p.write_json("draft", "timeline.json", tl)
        self.info(f"color: {len(tl['video'])} clips matched to luma {ref:.0f}, look={tl['filter']['key']}")
        return tl

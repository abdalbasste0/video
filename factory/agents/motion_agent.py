"""Motion Graphics Agent — hook title, synced captions with keyword highlight,
lower thirds, with In/Out/Loop animations and keyframes. Arabic RTL aware."""
from __future__ import annotations

import re

from .base import BaseAgent

AR_RE = re.compile(r"[؀-ۿ]")


def norm(word: str) -> str:
    return re.sub(r"[^\w؀-ۿ]", "", word).lower()


class MotionAgent(BaseAgent):
    name = "motion"

    def run(self) -> dict:
        tl = self.p.read_json("draft", "timeline.json")
        ts = self.p.read_json("voice", "timestamps.json")
        script = self.p.read_json("script", "script.json")
        cap = dict(self.s.get("captions", {}))
        cap["size"] = int(cap.get("size", 64)) + int(self.ctx.overrides("motion").get("size", 0))
        safe = self.s.get(f"safe_zone.{self.ctx.fmt}")
        rtl = self.ctx.language == "ar"
        if "safe zone" in (self.ctx.notes or ""):
            cap["size"] = int(cap["size"] * 0.88)   # QA feedback: shrink and re-fit
        safe_w = tl["width"] * (1 - safe["left"] - safe["right"]) * 0.94

        def max_chars(size: float) -> int:
            return max(6, int(safe_w / (size * 0.55)))

        keywords = {norm(k) for sc in script["scenes"] for k in sc.get("keywords", []) if k}
        texts = []

        # 1) Hook title — top third, pop in, gentle pulse, fade out at 3 s
        hook = script.get("hook") or script["scenes"][0]["narration"]
        hook_end = min(3.0, tl["duration"])
        hook_size = int(cap["size"] * 1.25)
        texts.append({
            "id": "title_hook", "kind": "title", "text": self._wrap(hook, max_chars(hook_size)), "start": 0.0,
            "duration": round(hook_end, 3), "rtl": rtl,
            "style": {**cap, "size": hook_size, "color": cap.get("highlight_color", "#FFD400"),
                      "background": "#00000000"},
            "y": safe["top"] + 0.12,
            "anim_in": "in_pop", "anim_out": "out_fade", "anim_loop": None,
            "keyframes": [{"prop": "scale", "t": 0.0, "v": 0.92}, {"prop": "scale", "t": hook_end, "v": 1.0}],
        })

        # 2) Captions — groups of N words synced to word timestamps
        n = int(cap.get("max_words_per_line", 4))
        limit = max_chars(cap["size"])
        idx = 0
        for sc in ts["scenes"]:
            for grp in self._groups(sc["words"], n, limit):
                start = grp[0]["start"]
                end = grp[-1]["end"]
                if start < hook_end and sc is ts["scenes"][0]:
                    continue  # the hook title already shows these words
                idx += 1
                texts.append({
                    "id": f"cap_{idx:03d}", "kind": "caption", "text": " ".join(w["text"] for w in grp),
                    "start": round(start, 3), "duration": round(max(0.3, end - start), 3), "rtl": rtl,
                    "words": [{**w, "highlight": norm(w["text"]) in keywords} for w in grp],
                    "style": cap, "y": float(cap.get("position_y", 0.72)),
                    "anim_in": "in_fade", "anim_out": None, "anim_loop": None, "keyframes": [],
                })

        # 3) Lower thirds / on-screen text from the script
        for sc_script, sc_ts in zip(script["scenes"], ts["scenes"]):
            label = self._wrap((sc_script.get("on_screen_text") or "").strip(), max_chars(cap["size"] * 0.7))
            if not label or sc_ts is ts["scenes"][0]:
                continue
            texts.append({
                "id": f"lt_{sc_script['id']}", "kind": "lower_third", "text": label,
                "start": sc_ts["start"], "duration": round(min(2.5, sc_ts["end"] - sc_ts["start"]), 3), "rtl": rtl,
                "style": {**cap, "size": int(cap.get("size", 64) * 0.7), "background": "#000000B0"},
                "y": 1 - safe["bottom"] - 0.14,
                "anim_in": "in_pop", "anim_out": "out_fade", "anim_loop": None,
                "keyframes": [{"prop": "x", "t": 0.0, "v": 0.08 if rtl else -0.08}, {"prop": "x", "t": 0.35, "v": 0.0}],
            })

        tl["texts"] = texts
        tl["rtl"] = rtl
        self.p.write_json("draft", "timeline.json", tl)
        self.info(f"motion: {len(texts)} text layers ({sum(t['kind'] == 'caption' for t in texts)} captions), rtl={rtl}")
        return tl

    @staticmethod
    def _groups(words: list[dict], n: int, limit: int) -> list[list[dict]]:
        """≤ n words and ≤ limit characters per caption line."""
        out, cur = [], []
        for w in words:
            if cur and (len(cur) >= n or len(" ".join(x["text"] for x in cur + [w])) > limit):
                out.append(cur)
                cur = []
            cur.append(w)
        if cur:
            out.append(cur)
        return out

    @staticmethod
    def _wrap(text: str, limit: int) -> str:
        """Wrap on word boundaries so every line fits the safe-zone width."""
        lines, cur = [], ""
        for w in text.split():
            if cur and len(cur) + 1 + len(w) > limit:
                lines.append(cur)
                cur = w
            else:
                cur = f"{cur} {w}".strip()
        if cur:
            lines.append(cur)
        return "\n".join(lines)

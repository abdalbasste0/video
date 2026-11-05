"""Script Agent — hook in the first 3 s, scenes with duration + visual description."""
from __future__ import annotations

import re

from .. import llm
from .base import BaseAgent

SCRIPT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "hook": {"type": "string"},
        "description": {"type": "string"},
        "hashtags": {"type": "array", "items": {"type": "string"}},
        "suggested_platform": {"type": "string"},
        "scenes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "narration": {"type": "string"},
                    "duration_sec": {"type": "number"},
                    "visual": {"type": "string"},
                    "search_query": {"type": "string"},
                    "on_screen_text": {"type": "string"},
                    "keywords": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["narration", "duration_sec", "visual", "search_query", "on_screen_text", "keywords"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["title", "hook", "description", "hashtags", "suggested_platform", "scenes"],
    "additionalProperties": False,
}

SYSTEM = """You write scripts for short-form social video (TikTok, Reels, Shorts, YouTube).
Rules:
- Scene 1 IS the hook: it must create curiosity or tension within the first 3 seconds (max ~9 words).
- Short spoken sentences, one idea per scene, 2-6 seconds each. No filler.
- `visual` describes what is on screen; `search_query` is 2-4 ENGLISH words for a stock-footage search.
- `on_screen_text` is an optional 1-4 word overlay ('' if none). `keywords` are words from the
  narration that the captions should highlight (exact spelling as in narration).
- Write the narration, title, description and hashtags in the requested language.
- End with a short call to action."""


class ScriptAgent(BaseAgent):
    name = "script"

    def run(self) -> dict:
        v = self.ctx.video
        target = int(self.s.get("channel.target_duration_sec", 45))
        lang = "Arabic" if self.ctx.language == "ar" else "English"
        previous = self.p.read_json("script", "script.json", default={})

        if llm.available():
            prompt = (f"Idea: {v['idea']}\nLanguage: {lang}\nFormat: {self.ctx.fmt}\n"
                      f"Target total duration: ~{target} seconds.\n")
            if self.ctx.notes and previous:
                prompt += (f"\nThis is a REVISION. Keep what works, change what the notes ask.\n"
                           f"Owner notes: {self.ctx.notes}\nPrevious script JSON: {previous}\n")
            data = llm.json_call(SYSTEM, prompt, SCRIPT_SCHEMA,
                                 model=self.s.get("script.model", "claude-opus-5-5"),
                                 effort=self.s.get("script.effort", "medium"))
            self.info(f"script written by Claude: {len(data['scenes'])} scenes")
        else:
            self.warn("ANTHROPIC_API_KEY not set → template script (set the key for real scripts)")
            data = self._template(v["idea"], target)

        data["scenes"] = [self._clean(i, s) for i, s in enumerate(data["scenes"], start=1)]
        data["hashtags"] = [h if h.startswith("#") else f"#{h}" for h in data.get("hashtags", [])][:12]
        self.p.write_json("script", "script.json", data)
        self.ctx.store.update_video(self.ctx.video_id, title=data["title"])
        return data

    @staticmethod
    def _clean(i: int, s: dict) -> dict:
        s = dict(s)
        s["id"] = f"s{i:02d}"
        s["narration"] = re.sub(r"\s+", " ", s["narration"]).strip()
        s["duration_sec"] = max(1.5, min(float(s.get("duration_sec", 4)), 12.0))
        s.setdefault("keywords", [])
        s.setdefault("on_screen_text", "")
        return s

    def _template(self, idea: str, target: int) -> dict:
        ar = self.ctx.language == "ar"
        lines = [
            (f"هل تعرف حقيقة {idea}؟" if ar else f"You won't believe this about {idea}."),
            (f"الكثير من الناس يجهلون هذا عن {idea}." if ar else f"Most people get {idea} completely wrong."),
            ("إليك السر الأول." if ar else "Here is the first secret."),
            ("والسر الثاني أهم بكثير." if ar else "The second one matters even more."),
            ("طبّق هذا اليوم وستلاحظ الفرق." if ar else "Try it today and you will see the difference."),
            ("تابعنا لمزيد من الأفكار." if ar else "Follow for more ideas like this."),
        ]
        per = max(2.5, target / len(lines))
        scenes = [{"narration": t, "duration_sec": per, "visual": f"{idea} b-roll",
                   "search_query": idea if not ar else "abstract background",
                   "on_screen_text": "", "keywords": [t.split()[-1].strip("؟?.!")]} for t in lines]
        return {"title": idea, "hook": lines[0], "description": idea,
                "hashtags": ["#shorts", "#viral"], "suggested_platform": "tiktok", "scenes": scenes}

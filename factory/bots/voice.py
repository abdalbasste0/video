"""Bot 3 — voice-over: turns each scene's narration into audio with ElevenLabs.

Each scene is a separate unit, so a helper bot can generate part of the scenes in parallel.
We pass the previous and next text (previous_text / next_text) so the voice stays continuous and natural across scenes.
"""
from __future__ import annotations

import requests

from ..config import settings
from ..media_tools import duration, ffmpeg
from ..state import Job
from .base import ProductionBot

API = "https://api.elevenlabs.io/v1/text-to-speech/{voice}"
MOOD_STYLE = {"suspense": 0.35, "dramatic": 0.55, "calm": 0.15, "happy": 0.4, "sad": 0.3}


class VoiceBot(ProductionBot):
    name = "bot3_voice"
    title_ar = "البوت الثالث — التعليق الصوتي (ElevenLabs)"
    stage = "voice"

    def plan(self, job: Job) -> list[dict]:
        scenes = job.get("script")["scenes"]
        (job.dir / "audio").mkdir(exist_ok=True)
        units = []
        for i, s in enumerate(scenes):
            units.append({
                "index": i,
                "text": s["narration"],
                "mood": s.get("mood", "suspense"),
                "prev": scenes[i - 1]["narration"] if i > 0 else "",
                "next": scenes[i + 1]["narration"] if i + 1 < len(scenes) else "",
            })
        return units

    def work(self, job: Job, unit: dict) -> dict:
        out = job.dir / "audio" / f"scene_{unit['index']:03d}.mp3"
        if settings.dry_run or not settings.elevenlabs_key:
            if not settings.dry_run:
                raise RuntimeError("ELEVENLABS_API_KEY غير مضبوط")
            # Test mode: a quiet audio clip the same length as the text would take to read
            secs = max(2.0, len(unit["text"].split()) / 2.3)
            ffmpeg("-f", "lavfi", "-i", f"sine=frequency=220:duration={secs:.2f}", "-af", "volume=0.05",
                   "-ar", "44100", "-ac", "1", "-c:a", "libmp3lame", "-q:a", "4", out)
        else:
            r = requests.post(
                API.format(voice=settings.elevenlabs_voice),
                params={"output_format": "mp3_44100_128"},
                headers={"xi-api-key": settings.elevenlabs_key, "Content-Type": "application/json"},
                json={
                    "text": unit["text"],
                    "model_id": settings.elevenlabs_model,
                    "previous_text": unit["prev"],
                    "next_text": unit["next"],
                    "voice_settings": {
                        "stability": 0.45,
                        "similarity_boost": 0.8,
                        "style": MOOD_STYLE.get(unit["mood"], 0.3),
                        "use_speaker_boost": True,
                    },
                },
                timeout=180,
            )
            if r.status_code != 200:
                raise RuntimeError(f"ElevenLabs {r.status_code}: {r.text[:300]}")
            out.write_bytes(r.content)
        return {"index": unit["index"], "path": str(out), "duration": duration(out)}

    def finish(self, job: Job, results: list[dict]) -> None:
        job.put("audio", results)
        job.put("audio_total_seconds", round(sum(r["duration"] for r in results), 2))

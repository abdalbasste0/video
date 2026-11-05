"""Voice Agent — voiceover + per-sentence/per-word timestamps (also used for subtitles)."""
from __future__ import annotations

import re
from pathlib import Path

from .. import media
from .base import BaseAgent

GAP = 0.18  # breath between scenes (s)


class VoiceAgent(BaseAgent):
    name = "voice"

    def run(self) -> dict:
        script = self.p.read_json("script", "script.json")
        engine = self.s.get("voice.engine", "edge")
        voice = self.ctx.overrides("voice").get("voice") or self.s.get(f"voice.voices.{self.ctx.language}")
        rate = self.ctx.overrides("voice").get("rate") or self.s.get("voice.rate", "+0%")
        vdir = self.p.dir("voice")

        parts: list[tuple[Path, list[dict], float]] = []
        for sc in script["scenes"]:
            out = vdir / f"{sc['id']}.wav"
            words: list[dict] = []
            if engine == "edge":
                try:
                    words = self._edge(sc["narration"], voice, rate, out)
                except Exception as e:  # network down, package missing …
                    self.warn(f"edge-tts failed ({e}); using silent timing track for {sc['id']}")
                    engine = "silent"
            if engine != "edge":
                words = self._silent(sc["narration"], out)
            dur = media.duration(out)
            if not words or not any(w["end"] > 0 for w in words):
                words = self._spread(sc["narration"], 0.0, dur)
            parts.append((out, words, dur))

        # concatenate with small gaps, collect absolute timestamps
        t = 0.0
        scenes_ts = []
        concat_list = vdir / "concat.txt"
        gap_file = vdir / "_gap.wav"
        media.ffmpeg("-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", f"{GAP}", str(gap_file))
        lines = []
        for (path, words, dur), sc in zip(parts, script["scenes"]):
            scenes_ts.append({
                "id": sc["id"], "text": sc["narration"], "start": round(t, 3), "end": round(t + dur, 3),
                "words": [{"text": w["text"], "start": round(t + w["start"], 3), "end": round(t + w["end"], 3)}
                          for w in words],
            })
            lines += [f"file '{path.name}'", f"file '{gap_file.name}'"]
            t += dur + GAP
        concat_list.write_text("\n".join(lines), encoding="utf-8")
        media.ffmpeg("-f", "concat", "-safe", "0", "-i", str(concat_list),
                     "-ar", "48000", "-ac", "1", str(self.p.voice_file))
        total = media.duration(self.p.voice_file)
        data = {"engine": engine, "voice": voice, "duration": round(total, 3), "scenes": scenes_ts}
        self.p.write_json("voice", "timestamps.json", data)
        self.p.write_json("voice", "subtitles.srt.json", self._srt_lines(scenes_ts))
        self.info(f"voice ready: {total:.1f}s, engine={engine}, {sum(len(s['words']) for s in scenes_ts)} words")
        return data

    # ---------- engines ----------
    def _edge(self, text: str, voice: str, rate: str, out: Path) -> list[dict]:
        import edge_tts

        mp3 = out.with_suffix(".mp3")
        try:
            com = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
        except TypeError:  # edge-tts < 7 emits WordBoundary by default
            com = edge_tts.Communicate(text, voice, rate=rate)
        words: list[dict] = []
        sentences: list[dict] = []
        with open(mp3, "wb") as f:
            for chunk in com.stream_sync():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                    item = {"text": chunk["text"], "start": chunk["offset"] / 1e7,
                            "end": (chunk["offset"] + chunk["duration"]) / 1e7}
                    (words if chunk["type"] == "WordBoundary" else sentences).append(item)
        media.ffmpeg("-i", str(mp3), "-ar", "48000", "-ac", "1", str(out))
        if not words and sentences:
            for s in sentences:
                words += self._spread(s["text"], s["start"], s["end"])
        return words

    def _silent(self, text: str, out: Path) -> list[dict]:
        n = len(text.split())
        dur = max(1.2, n / 2.6 + 0.3)
        media.ffmpeg("-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", f"{dur:.2f}", str(out))
        return self._spread(text, 0.1, dur - 0.1)

    @staticmethod
    def _spread(text: str, start: float, end: float) -> list[dict]:
        """Distribute words over [start, end] proportionally to their length."""
        ws = [w for w in re.split(r"\s+", text.strip()) if w]
        if not ws:
            return []
        total = sum(len(w) + 1 for w in ws)
        t, out = start, []
        for w in ws:
            d = (end - start) * (len(w) + 1) / total
            out.append({"text": w, "start": t, "end": t + d})
            t += d
        return out

    @staticmethod
    def _srt_lines(scenes: list[dict]) -> list[dict]:
        return [{"start": s["start"], "end": s["end"], "text": s["text"]} for s in scenes]

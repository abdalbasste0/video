"""Sound Agent — voice normalisation, music ducking via volume keyframes,
fades, SFX on transitions. Final −14 LUFS is enforced at render/export."""
from __future__ import annotations

from .. import media
from .base import BaseAgent

VOICE_TARGET_LUFS = -16.0


def db(x: float) -> float:
    return round(10 ** (x / 20), 4)


class SoundAgent(BaseAgent):
    name = "sound"

    def run(self) -> dict:
        tl = self.p.read_json("draft", "timeline.json")
        ts = self.p.read_json("voice", "timestamps.json")
        assets = self.p.read_json("assets", "assets.json")
        cfg = dict(self.s.get("sound", {}))
        ov = self.ctx.overrides("sound")
        music_db = float(self.s.get("assets.music_volume_db", -20)) + float(ov.get("music_db", 0))
        duck_db = float(cfg.get("ducking_db", -12)) + float(ov.get("duck_db", 0))
        fade_in, fade_out = float(cfg.get("fade_in_sec", 0.8)), float(cfg.get("fade_out_sec", 1.5))
        total = tl["duration"]

        # voice gain so speech sits at ~-16 LUFS before the final -14 LUFS master
        measured = media.loudness(self.p.voice_file)
        voice_gain_db = 0.0 if measured is None or measured < -60 else max(-10, min(15, VOICE_TARGET_LUFS - measured))

        # ducking keyframes: low under each spoken scene, recover in pauses
        base, ducked = db(music_db), db(music_db + duck_db)
        kfs = [(0.0, base)]
        for sc in ts["scenes"]:
            a, b = sc["start"], sc["end"]
            kfs += [(max(0.0, a - 0.25), base if a > 0.3 else ducked), (a, ducked), (b, ducked), (b + 0.3, base)]
        kfs.append((total, base))
        kfs = self._clean(kfs, total)

        audio = [
            {"id": "voice", "kind": "voice", "path": str(self.p.voice_file), "start": 0.0,
             "duration": round(media.duration(self.p.voice_file), 3), "source_start": 0.0,
             "volume": db(voice_gain_db), "fade_in": 0.0, "fade_out": 0.0, "volume_keyframes": []},
            {"id": "music", "kind": "music", "path": assets["music"], "start": 0.0,
             "duration": total, "source_start": 0.0, "volume": 1.0, "loop": True,
             "fade_in": fade_in, "fade_out": fade_out,
             "volume_keyframes": [{"t": round(t, 3), "v": v} for t, v in kfs]},
        ]
        if cfg.get("transition_sfx", True) and not ov.get("no_sfx"):
            sfx = assets["sfx"]["whoosh"]
            sfx_d = media.duration(sfx)
            for c in tl["video"]:
                if c.get("transition_out"):
                    t = c["start"] + c["duration"] - 0.2
                    audio.append({"id": f"sfx_{c['id']}", "kind": "sfx", "path": sfx, "start": round(max(0, t), 3),
                                  "duration": round(min(sfx_d, total - t), 3), "source_start": 0.0,
                                  "volume": db(-10), "fade_in": 0.0, "fade_out": 0.0, "volume_keyframes": []})
        tl["audio"] = audio
        tl["target_lufs"] = float(cfg.get("target_lufs", -14))
        self.p.write_json("draft", "timeline.json", tl)
        self.info(f"sound: voice {voice_gain_db:+.1f} dB, music {music_db} dB ducked {duck_db} dB, "
                  f"{sum(a['kind'] == 'sfx' for a in audio)} sfx")
        return tl

    @staticmethod
    def _clean(kfs: list[tuple[float, float]], total: float) -> list[tuple[float, float]]:
        out: list[tuple[float, float]] = []
        for t, v in sorted(kfs):
            t = min(max(0.0, t), total)
            if out and t - out[-1][0] < 0.02:
                out[-1] = (out[-1][0], v)
            else:
                out.append((t, v))
        return out

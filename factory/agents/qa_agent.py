"""QA Agent — validates the draft (stage="draft") and the exported file (stage="export").
Every issue names the responsible agent so the Orchestrator can route it back."""
from __future__ import annotations

import json
import re
from pathlib import Path

from .. import media
from .base import BaseAgent, QAIssue

PLATFORM_LIMITS = {"9:16": (5.0, 180.0), "16:9": (5.0, 3600.0)}


def words_of(text: str) -> list[str]:
    return [re.sub(r"[^\w؀-ۿ]", "", w).lower() for w in text.split() if w.strip()]


class QAAgent(BaseAgent):
    name = "qa"

    def run(self, stage: str = "draft") -> dict:
        issues = self.check_draft() if stage == "draft" else self.check_export()
        errors = [i for i in issues if i.severity == "error"]
        report = {"stage": stage, "passed": not errors, "issues": [i.__dict__ for i in issues]}
        reports = self.p.read_json("logs", "qa_report.json", default={})
        reports[stage] = report
        self.p.write_json("logs", "qa_report.json", reports)
        self.info(f"QA {stage}: {'PASS' if not errors else 'FAIL'} ({len(errors)} errors, "
                  f"{len(issues) - len(errors)} warnings)")
        return report

    # ------------------------------------------------------------------ draft
    def check_draft(self) -> list[QAIssue]:
        tl = self.p.read_json("draft", "timeline.json")
        ts = self.p.read_json("voice", "timestamps.json")
        issues: list[QAIssue] = []
        W, H, total = tl["width"], tl["height"], tl["duration"]

        # canvas
        if (W, H) != tuple(self.s.resolution(tl["fmt"])) or tl["fps"] != 30:
            issues.append(QAIssue("editor", f"canvas {W}x{H}@{tl['fps']} ≠ expected"))

        # main track continuity
        clips = sorted(tl["video"], key=lambda c: c["start"])
        if not clips or abs(clips[0]["start"]) > 0.001:
            issues.append(QAIssue("editor", "main track does not start at 0"))
        for a, b in zip(clips, clips[1:]):
            gap = b["start"] - (a["start"] + a["duration"])
            if abs(gap) > 0.034:
                issues.append(QAIssue("editor", f"{'gap' if gap > 0 else 'overlap'} of {abs(gap):.3f}s "
                                                f"between {a['id']} and {b['id']}"))
        if clips and abs(clips[-1]["start"] + clips[-1]["duration"] - total) > 0.034:
            issues.append(QAIssue("editor", "main track does not reach the end of the timeline"))
        for c in clips:
            if not Path(c["path"]).exists():
                issues.append(QAIssue("assets", f"missing media {c['path']}"))

        # audio not cut off
        voice = next((a for a in tl.get("audio", []) if a["kind"] == "voice"), None)
        if not voice:
            issues.append(QAIssue("sound", "no voice track in timeline"))
        elif voice["start"] + voice["duration"] > total + 0.01:
            issues.append(QAIssue("editor", f"voice ({voice['duration']:.2f}s) is cut off by timeline ({total:.2f}s)"))
        if ts["scenes"] and ts["scenes"][-1]["end"] > total:
            issues.append(QAIssue("editor", "last spoken word ends after the video"))
        music = next((a for a in tl.get("audio", []) if a["kind"] == "music"), None)
        if music and abs(music["duration"] - total) > 0.05:
            issues.append(QAIssue("sound", "music bed does not cover the full video", "warning"))

        # subtitles match speech
        spoken = [w for sc in ts["scenes"] for w in words_of(" ".join(x["text"] for x in sc["words"]))]
        shown = [w for t in tl.get("texts", []) if t["kind"] in ("caption", "title") for w in words_of(t["text"])]
        missing = [w for w in spoken if w not in set(shown)]
        if spoken and len(missing) / len(spoken) > 0.05:
            issues.append(QAIssue("motion", f"{len(missing)} spoken words have no caption (e.g. {missing[:5]})"))
        for t in tl.get("texts", []):
            if t.get("words"):
                if abs(t["start"] - t["words"][0]["start"]) > 0.15:
                    issues.append(QAIssue("motion", f"caption {t['id']} out of sync by "
                                                    f"{t['start'] - t['words'][0]['start']:.2f}s"))
            if t["start"] + t["duration"] > total + 0.01:
                issues.append(QAIssue("motion", f"text {t['id']} runs past the end"))

        # safe zone
        sz = self.s.get(f"safe_zone.{tl['fmt']}")
        for t in tl.get("texts", []):
            size = float(t["style"].get("size", 64))
            lines = t["text"].split("\n")
            width_px = max(len(line) for line in lines) * size * 0.55
            height_px = len(lines) * size * 1.3
            y = float(t.get("y", 0.7)) * H
            if width_px > W * (1 - sz["left"] - sz["right"]):
                issues.append(QAIssue("motion", f"text {t['id']} is too wide for the safe zone "
                                                f"({width_px:.0f}px)"))
            if y - height_px / 2 < H * sz["top"] or y + height_px / 2 > H * (1 - sz["bottom"]):
                issues.append(QAIssue("motion", f"text {t['id']} leaves the vertical safe zone"))

        # duration
        lo, hi = PLATFORM_LIMITS.get(tl["fmt"], (5, 3600))
        if not lo <= total <= hi:
            issues.append(QAIssue("script", f"duration {total:.1f}s outside {lo}-{hi}s for {tl['fmt']}"))

        # draft JSON integrity (what CapCut will read)
        issues += self._check_capcut_json()

        lib_skipped = self.ctx.video.get("meta", {}).get("draft_skipped", [])
        if lib_skipped:
            issues.append(QAIssue("draft", f"CapCut IDs missing (skipped, draft still opens): "
                                           f"{sorted(set(lib_skipped))} → run `main.py learn-draft`", "warning"))
        return issues

    def _check_capcut_json(self) -> list[QAIssue]:
        name = self.ctx.video.get("meta", {}).get("draft_name")
        ddir = self.ctx.video.get("meta", {}).get("draft_dir")
        if not name or not ddir:
            return [QAIssue("draft", "draft was not built")]
        f = Path(ddir) / "draft_content.json"
        try:
            doc = json.loads(f.read_text(encoding="utf-8"))
            json.loads((Path(ddir) / "draft_meta_info.json").read_text(encoding="utf-8"))
        except Exception as e:
            return [QAIssue("draft", f"draft JSON unreadable: {e}")]
        issues = []
        ids = {m["id"] for lst in doc["materials"].values() if isinstance(lst, list) for m in lst
               if isinstance(m, dict) and "id" in m}
        for tr in doc["tracks"]:
            last_end = -1
            for s in sorted(tr["segments"], key=lambda x: x["target_timerange"]["start"]):
                if s["material_id"] not in ids:
                    issues.append(QAIssue("draft", f"segment references missing material {s['material_id']}"))
                for r in s.get("extra_material_refs", []):
                    if r not in ids:
                        issues.append(QAIssue("draft", f"segment ref {r} missing"))
                st = s["target_timerange"]["start"]
                if st < last_end - 1:  # 1 µs tolerance
                    issues.append(QAIssue("draft", f"overlapping segments on {tr['type']} track"))
                last_end = st + s["target_timerange"]["duration"]
            if tr["type"] == "video" and tr is doc["tracks"][0] and abs(last_end - doc["duration"]) > 40_000:
                issues.append(QAIssue("draft", "draft main track length ≠ draft duration"))
        for v in doc["materials"].get("videos", []) + doc["materials"].get("audios", []):
            p = v["path"].replace("##DRAFT_DIR##", str(Path(ddir)))
            if not Path(p).exists():
                issues.append(QAIssue("draft", f"draft media path not found: {p}"))
        return issues

    # ------------------------------------------------------------------ export
    def check_export(self) -> list[QAIssue]:
        tl = self.p.read_json("draft", "timeline.json")
        f = self.p.final_file
        if not f.exists():
            return [QAIssue("render", "final.mp4 missing")]
        info = media.video_info(f)
        issues = []
        if (info["width"], info["height"]) != (tl["width"], tl["height"]):
            issues.append(QAIssue("render", f"resolution {info['width']}x{info['height']} ≠ "
                                            f"{tl['width']}x{tl['height']}"))
        if abs(info["fps"] - tl["fps"]) > 0.5:
            issues.append(QAIssue("render", f"fps {info['fps']} ≠ {tl['fps']}"))
        if abs(info["duration"] - tl["duration"]) > 0.35:
            issues.append(QAIssue("render", f"duration {info['duration']:.2f}s ≠ timeline {tl['duration']:.2f}s"))
        if not info["has_audio"]:
            issues.append(QAIssue("render", "export has no audio"))
        lufs = media.loudness(f)
        target = tl.get("target_lufs", -14)
        if lufs is None or abs(lufs - target) > 2.0:
            issues.append(QAIssue("sound", f"loudness {lufs} LUFS (target {target})",
                                  "warning" if lufs is not None and abs(lufs - target) <= 3 else "error"))
        self.ctx.store.merge_meta(self.ctx.video_id, export_info={**info, "lufs": lufs})
        return issues

"""Bot 6 — QA: checks the video and its editing before it is shown to the owner.

Each check is a separate unit (a helper can run part of the checks in parallel):
  technical  — resolution, frame rate, presence of audio and video, total length vs. narration (sync)
  black      — black (empty) frames
  silence    — long silent gaps
  loudness   — loudness level (target -14 LUFS)
  content    — editorial review by Claude: title, description, tags, fact-check results, platform policies
  preview    — a contact sheet of frames for the owner to glance at
"""
from __future__ import annotations

import json
import re

from pydantic import BaseModel

from .. import llm
from ..config import settings
from ..media_tools import ffmpeg, probe, run
from ..state import Job
from .base import ProductionBot

CHECKS = ["technical", "black", "silence", "loudness", "content", "preview"]


class ContentReview(BaseModel):
    passed: bool
    issues: list[str]
    suggestions: list[str]


class QABot(ProductionBot):
    name = "bot6_qa"
    title_ar = "البوت السادس — الفحص قبل العرض"
    stage = "qa"

    def plan(self, job: Job) -> list[dict]:
        return [{"check": c} for c in CHECKS]

    def work(self, job: Job, unit: dict) -> dict:
        video = job.get("video")["path"]
        return getattr(self, f"_check_{unit['check']}")(job, video)

    def finish(self, job: Job, results: list[dict]) -> None:
        critical = [r for r in results if not r["ok"] and r.get("critical")]
        report = {"passed": not critical, "checks": results}
        job.put("qa_report", report)
        if critical:
            raise RuntimeError("فشل الفحص: " + " | ".join(f"{r['check']}: {r['detail']}" for r in critical))

    # ------------------------------------------------------------------
    def _check_technical(self, job: Job, video: str) -> dict:
        info = probe(video)
        v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
        a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
        problems = []
        if not v:
            problems.append("لا يوجد مسار فيديو")
        elif (v["width"], v["height"]) != settings.resolution:
            problems.append(f"الدقة {v['width']}x{v['height']} بدل {settings.resolution}")
        if not a:
            problems.append("لا يوجد صوت")
        dur = float(info["format"]["duration"])
        expected = job.get("audio_total_seconds", 0)
        if expected and abs(dur - expected) > max(2.0, 0.6 * len(job.get("audio", []))):
            problems.append(f"مدة الفيديو {dur:.1f}ث لا تطابق مدة التعليق {expected:.1f}ث (مشكلة مزامنة)")
        return {"check": "technical", "ok": not problems, "critical": True,
                "detail": "; ".join(problems) or f"سليم — {dur:.1f} ثانية"}

    def _check_black(self, job: Job, video: str) -> dict:
        p = run(["ffmpeg", "-hide_banner", "-i", video, "-vf", "blackdetect=d=1.0:pic_th=0.98", "-an", "-f", "null", "-"])
        hits = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", p.stderr)
        return {"check": "black", "ok": not hits, "critical": True,
                "detail": f"لقطات سوداء عند: {hits}" if hits else "لا توجد لقطات سوداء"}

    def _check_silence(self, job: Job, video: str) -> dict:
        p = run(["ffmpeg", "-hide_banner", "-i", video, "-af", "silencedetect=noise=-45dB:d=2.5", "-vn", "-f", "null", "-"])
        hits = re.findall(r"silence_start: ([\d.]+)", p.stderr)
        return {"check": "silence", "ok": not hits, "critical": False,
                "detail": f"صمت طويل عند الثواني: {hits}" if hits else "لا يوجد صمت طويل"}

    def _check_loudness(self, job: Job, video: str) -> dict:
        p = run(["ffmpeg", "-hide_banner", "-i", video, "-af", "ebur128", "-vn", "-f", "null", "-"])
        m = re.findall(r"I:\s+(-?[\d.]+) LUFS", p.stderr)
        lufs = float(m[-1]) if m else None
        ok = lufs is not None and -17 <= lufs <= -11
        return {"check": "loudness", "ok": ok, "critical": False, "detail": f"الجهارة {lufs} LUFS (المستهدف -14)"}

    def _check_content(self, job: Job, video: str) -> dict:
        script = job.get("script")
        checks = job.get("fact_checks", [])
        prompt = (
            f"السكريبت النهائي:\n{json.dumps(script, ensure_ascii=False, indent=2)}\n\n"
            f"نتائج تدقيق الحقائق:\n{json.dumps(checks, ensure_ascii=False, indent=2)}\n\n"
            "راجع كمدقق جودة قبل النشر على يوتيوب: هل العنوان ≤ 100 حرف وجذاب وغير مضلل؟ "
            "هل بقيت أي معلومة حُكم عليها بأنها خاطئة دون تصحيح؟ هل التواريخ والأوقات متسقة داخل القصة؟ "
            "هل يوجد ما يخالف سياسات يوتيوب (عنف صريح، معلومات مضللة، حقوق)؟ "
            "passed=false فقط عند وجود مشكلة تمنع النشر."
        )
        review = llm.ask_json("أنت مدقق جودة محتوى صارم.", prompt, ContentReview, effort="medium",
                              mock={"passed": True, "issues": [], "suggestions": ["(تجريبي) لا ملاحظات"]})
        detail = "; ".join(review.issues) or "لا مشاكل في المحتوى"
        if review.suggestions:
            detail += " | اقتراحات: " + "; ".join(review.suggestions)
        return {"check": "content", "ok": review.passed, "critical": True, "detail": detail}

    def _check_preview(self, job: Job, video: str) -> dict:
        sheet = job.dir / "preview_sheet.jpg"
        dur = job.get("video")["duration"]
        step = max(dur / 9, 0.5)
        ffmpeg("-i", video, "-vf", f"fps=1/{step:.2f},scale=480:-1,tile=3x3", "-frames:v", "1", "-q:v", "3", sheet)
        job.put("preview_sheet", str(sheet))
        return {"check": "preview", "ok": True, "critical": False, "detail": f"لوحة معاينة: {sheet.name}"}

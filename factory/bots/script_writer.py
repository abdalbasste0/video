"""Bot 2 — script writer: writes the script, edits it professionally, and checks dates and times.

Steps:
 1. plan():   writes a full draft and pulls out every claim tied to a date, time, number, or name.
 2. work():   checks each claim with a web search (each claim is a unit a helper can take over).
 3. finish(): professional edit that applies every fix, then saves the final script.
"""
from __future__ import annotations

import json

from pydantic import BaseModel, Field

from .. import llm
from ..state import Job
from .base import ProductionBot

POSES = ["standing", "walking", "running", "thinking", "shocked", "pointing", "sitting", "sad", "happy"]

SYSTEM = (
    "أنت كاتب سكريبتات يوتيوب عربي محترف متخصص في قصص ستيك مان والغموض والألغاز. "
    "تكتب بالعربية الفصحى المبسطة بأسلوب سردي مشوق، جمل قصيرة تناسب التعليق الصوتي، "
    "خطاف قوي في أول 5 ثوان، تصاعد للتشويق، ونهاية تدفع للتعليق والاشتراك. "
    "لا تخترع حقائق تاريخية: أي تاريخ أو وقت أو رقم يجب أن يكون قابلاً للتحقق."
)


class Scene(BaseModel):
    narration: str = Field(description="نص التعليق الصوتي لهذا المشهد (1-3 جمل)")
    visual_type: str = Field(description="stickman | stock")
    visual_query_en: str = Field(description="كلمات بحث إنجليزية لمكتبات الفيديو/الصور")
    stickman_pose: str = Field(default="standing", description="|".join(POSES))
    on_screen_text: str = Field(default="", description="نص قصير يظهر على الشاشة (اختياري)")
    mood: str = Field(default="suspense", description="suspense | calm | dramatic | happy | sad")


class Claim(BaseModel):
    claim: str
    kind: str = Field(description="date | time | number | name | event")


class Script(BaseModel):
    title: str
    description: str
    tags: list[str]
    thumbnail_text: str
    scenes: list[Scene]
    claims: list[Claim] = Field(default_factory=list)


class ClaimCheck(BaseModel):
    claim: str
    verdict: str = Field(description="correct | wrong | unverifiable")
    correction: str = ""
    source: str = ""


def _mock_script(title: str) -> dict:
    return {
        "title": title,
        "description": "قصة غامضة حقيقية… شاهد حتى النهاية.",
        "tags": ["غموض", "قصص", "ألغاز"],
        "thumbnail_text": "اختفى من غرفة مغلقة!",
        "scenes": [
            {"narration": "باب مغلق من الداخل… والغرفة فارغة تماماً.", "visual_type": "stickman",
             "visual_query_en": "locked door dark room", "stickman_pose": "shocked", "on_screen_text": "غرفة مغلقة", "mood": "suspense"},
            {"narration": "في صباح ذلك اليوم، استيقظ أهل القرية على خبر غريب.", "visual_type": "stock",
             "visual_query_en": "foggy village morning", "stickman_pose": "standing", "mood": "calm"},
            {"narration": "فكّر جيداً… كيف خرج الرجل؟ اكتب إجابتك في التعليقات.", "visual_type": "stickman",
             "visual_query_en": "thinking", "stickman_pose": "thinking", "on_screen_text": "ما الحل؟", "mood": "dramatic"},
        ],
        "claims": [{"claim": "وقعت القصة عام 1931", "kind": "date"}],
    }


class ScriptWriter(ProductionBot):
    name = "bot2_script_writer"
    title_ar = "البوت الثاني — كاتب السكريبت ومدقق التواريخ"
    stage = "script"

    def plan(self, job: Job) -> list[dict]:
        idea = job.get("chosen_idea")
        if not idea:
            raise RuntimeError("لم يتم اختيار فكرة بعد")
        minutes = job.brief.get("minutes", 6 if job.brief.get("format") != "vertical" else 1)
        feedback = job.brief.get("script_feedback", "")
        prompt = (
            f"الفكرة المعتمدة من المالك:\n{json.dumps(idea, ensure_ascii=False, indent=2)}\n\n"
            f"المدة المستهدفة: حوالي {minutes} دقيقة (≈ {int(minutes * 140)} كلمة).\n"
            f"ملاحظات المالك: {job.brief.get('notes', 'لا يوجد')}\n"
            f"تعليمات خاصة لك من المالك: {self.owner_note(job) or 'لا يوجد'}\n"
            + (f"ملاحظات المالك على النسخة السابقة (يجب تطبيقها): {feedback}\n" if feedback else "")
            + "اكتب السكريبت مقسماً إلى مشاهد (كل مشهد 4-10 ثوان). "
              "لقصص ستيك مان استخدم visual_type=stickman لمعظم المشاهد. "
              "استخرج في claims كل تاريخ أو وقت أو رقم أو اسم حقيقي ورد في النص لتدقيقه."
        )
        draft = llm.ask_json(SYSTEM, prompt, Script, web_search=True, mock=_mock_script(idea["title"]))
        job.put("script_draft", draft.model_dump())
        return [c.model_dump() for c in draft.claims] or [{"claim": "", "kind": "none"}]

    def work(self, job: Job, unit: dict) -> dict:
        if not unit["claim"]:
            return {"claim": "", "verdict": "correct", "correction": "", "source": ""}
        prompt = (
            f"تحقق من صحة هذه المعلومة بالبحث في مصادر موثوقة: «{unit['claim']}» (النوع: {unit['kind']}).\n"
            "انتبه بشكل خاص للتواريخ (اليوم/الشهر/السنة) والأوقات والمناطق الزمنية."
        )
        mock = {"claim": unit["claim"], "verdict": "correct", "correction": "", "source": "https://example.com"}
        return llm.ask_json(
            "أنت مدقق حقائق صارم.", prompt, ClaimCheck, web_search=True, effort="medium", mock=mock
        ).model_dump()

    def finish(self, job: Job, results: list[dict]) -> None:
        draft = job.get("script_draft")
        checks = [r for r in results if r["claim"]]
        job.put("fact_checks", checks)
        prompt = (
            f"المسودة:\n{json.dumps(draft, ensure_ascii=False, indent=2)}\n\n"
            f"نتائج التدقيق:\n{json.dumps(checks, ensure_ascii=False, indent=2)}\n\n"
            "قم بتحرير احترافي نهائي: صحح كل معلومة خاطئة، احذف أو صِغ بحذر ما لا يمكن التحقق منه، "
            "حسّن الإيقاع والخطاف والانتقالات، ووحّد الأسلوب. أبقِ نفس بنية المشاهد."
        )
        final = llm.ask_json(SYSTEM, prompt, Script, mock=draft)
        job.put("script", final.model_dump())

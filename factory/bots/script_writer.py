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
from ..config import settings
from ..state import Job
from .base import ProductionBot

POSES = ["standing", "walking", "running", "thinking", "shocked", "pointing", "sitting", "sad", "happy"]



def system_prompt() -> str:
    lang = settings.language_name
    return (
        "You are a professional YouTube scriptwriter specialised in stickman stories, mystery stories and riddles. "
        f"Write EVERY viewer-facing field (narration, title, description, tags, thumbnail_text, on_screen_text) in {lang}. "
        "Narration is read aloud by a voice-over artist: short, punchy spoken sentences, vivid storytelling, "
        "a strong hook in the first 5 seconds, rising suspense, and an ending that invites comments and subscriptions. "
        "Use punctuation (commas, ellipses, question marks) to guide natural pacing for the voice. "
        "Never invent historical facts: every date, time, number and real name must be verifiable."
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
    if settings.language == "en":
        return {
            "title": "The Man Who Vanished From a Locked Room",
            "description": "A true mystery that still has no answer... watch until the end.",
            "tags": ["mystery", "stories", "riddles"],
            "thumbnail_text": "VANISHED from a LOCKED room!",
            "scenes": [
                {"narration": "The door was locked from the inside... and the room was completely empty.", "visual_type": "stickman",
                 "visual_query_en": "locked door dark room", "stickman_pose": "shocked", "on_screen_text": "LOCKED ROOM", "mood": "suspense"},
                {"narration": "That morning, the whole village woke up to very strange news.", "visual_type": "stock",
                 "visual_query_en": "foggy village morning", "stickman_pose": "standing", "mood": "calm"},
                {"narration": "So think carefully... how did he get out? Drop your answer in the comments.", "visual_type": "stickman",
                 "visual_query_en": "thinking", "stickman_pose": "thinking", "on_screen_text": "Your answer?", "mood": "dramatic"},
            ],
            "claims": [{"claim": "The story happened in 1931", "kind": "date"}],
        }
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
            f"المدة المستهدفة: حوالي {minutes} دقيقة (≈ {int(minutes * (150 if settings.language == 'en' else 140))} كلمة).\n"
            f"لغة الفيديو والتعليق الصوتي: {settings.language_name}\n"
            f"ملاحظات المالك: {job.brief.get('notes', 'لا يوجد')}\n"
            f"تعليمات خاصة لك من المالك: {self.owner_note(job) or 'لا يوجد'}\n"
            + (f"ملاحظات المالك على النسخة السابقة (يجب تطبيقها): {feedback}\n" if feedback else "")
            + "اكتب السكريبت مقسماً إلى مشاهد (كل مشهد 4-10 ثوان). "
              "لقصص ستيك مان استخدم visual_type=stickman لمعظم المشاهد. "
              "استخرج في claims كل تاريخ أو وقت أو رقم أو اسم حقيقي ورد في النص لتدقيقه."
        )
        draft = llm.ask_json(system_prompt(), prompt, Script, web_search=True, mock=_mock_script(idea["title"]))
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
        final = llm.ask_json(system_prompt(), prompt, Script, mock=draft)
        job.put("script", final.model_dump())

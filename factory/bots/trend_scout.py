"""Bot 1 — trend research: looks for the viral topics and ideas that are spreading right now.

It searches several angles in parallel (each angle is a work unit a helper can take over),
then merges the results and ranks the best ideas, which are presented to the owner to choose from.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from .. import llm
from ..config import settings
from ..state import Job, history
from .base import ProductionBot

CATEGORIES = {
    "stickman": "قصص ستيك مان (رسوم بسيطة، قصص حياتية/تحفيزية/كوميدية/تاريخية مبسطة)",
    "mystery": "قصص الغموض والجرائم الغامضة والأحداث غير المفسرة",
    "riddles": "الألغاز والتحديات الذهنية وقصص الألغاز البوليسية",
}

ANGLES = [
    "ما الذي ينتشر الآن على يوتيوب وتيك توك في هذه الفئة (آخر 7 أيام)؟ ابحث عن فيديوهات تفوقت على متوسط قنواتها.",
    "ما المواضيع التي يبحث عنها الناس الآن (Google Trends، أسئلة شائعة، ريديت، X)؟",
    "ما الذكريات السنوية أو الأحداث التاريخية الموافقة لتاريخ اليوم أو هذا الأسبوع والتي تصلح لقصة في هذه الفئة؟",
]

SYSTEM = (
    "أنت باحث محتوى فيروسي محترف لقناة يوتيوب عربية. مهمتك إيجاد أفكار حقيقية ومثبتة بالمصادر، "
    "لا تخترع أرقام مشاهدات أو أحداثاً. اذكر رابط المصدر لكل فكرة."
)


class Idea(BaseModel):
    title: str = Field(description="عنوان جذاب مقترح للفيديو")
    category: str = Field(description="stickman | mystery | riddles")
    hook: str = Field(description="أول جملة تشد المشاهد في أول 5 ثوان")
    why_viral: str = Field(description="لماذا نتوقع انتشارها، مع دليل")
    sources: list[str] = Field(default_factory=list)
    virality_score: int = Field(ge=1, le=10)


class IdeaList(BaseModel):
    ideas: list[Idea]


def _mock_ideas(category: str) -> dict:
    return {"ideas": [
        {"title": "الرجل الذي اختفى من غرفة مغلقة", "category": category,
         "hook": "باب مغلق من الداخل… والغرفة فارغة تماماً.",
         "why_viral": "قصص الغرفة المغلقة تحقق نسب مشاهدة عالية هذا الأسبوع",
         "sources": ["https://example.com/source"], "virality_score": 8},
        {"title": "لغز الساعة التي توقفت", "category": category,
         "hook": "كل الساعات في القرية توقفت عند 3:17.",
         "why_viral": "ألغاز الوقت رائجة", "sources": ["https://example.com/2"], "virality_score": 7},
    ]}


class TrendScout(ProductionBot):
    name = "bot1_trend_scout"
    title_ar = "البوت الأول — باحث الأفكار الفيروسية"
    stage = "research"

    def plan(self, job: Job) -> list[dict]:
        cats = [job.brief["category"]] if job.brief.get("category") in CATEGORIES else list(CATEGORIES)
        return [{"category": c, "angle": a} for c in cats for a in ANGLES]

    def work(self, job: Job, unit: dict) -> list[dict]:
        cat = unit["category"]
        prompt = (
            f"تاريخ اليوم: {job.day.isoformat()}\nالفئة: {CATEGORIES[cat]}\n"
            f"لغة الفيديو والجمهور المستهدف: {settings.language_name} — ابحث فيما ينتشر لدى هذا الجمهور، "
            f"واكتب title و hook بهذه اللغة، أما why_viral فاكتبه بالعربية للمالك.\n"
            f"زاوية البحث: {unit['angle']}\n"
            f"ملاحظات المالك: {job.brief.get('notes', 'لا يوجد')}\n"
            f"موضوع مقترح من المالك (إن وجد): {job.brief.get('topic', 'لا يوجد')}\n"
            f"عناوين نُشرت سابقاً (لا تكررها): {[h['title'] for h in history()[-30:]]}\n"
            f"تعليمات خاصة لك من المالك: {self.owner_note(job) or 'لا يوجد'}\n\n"
            "استخدم البحث في الإنترنت، ثم اقترح 3 أفكار فيديو قوية."
        )
        res = llm.ask_json(SYSTEM, prompt, IdeaList, web_search=True, mock=_mock_ideas(cat))
        return [i.model_dump() for i in res.ideas]

    def finish(self, job: Job, results: list[list[dict]]) -> None:
        all_ideas = [i for group in results for i in group]
        used = {h["title"] for h in history()}
        ranked = sorted((i for i in all_ideas if i["title"] not in used),
                        key=lambda i: i["virality_score"], reverse=True)
        # Remove duplicates by title
        seen, unique = set(), []
        for i in ranked:
            if i["title"] not in seen:
                seen.add(i["title"])
                unique.append(i)
        job.put("ideas", unique[:5])

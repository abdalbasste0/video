"""Bot 9 — the manager: receives the owner's instructions, hands each bot its task, and watches the schedule.

- Receives owner commands (Telegram or `python -m factory command "..."`) and understands them with Claude.
- Starts the work at 08:00 and runs the stages in order according to the schedule in config.py.
- Watches every stage: if it falls behind or its units fail, it calls helper 7 and then helper 8.
- Asks the owner for approval at every key step: idea choice, script, final video.
- Publishes nothing without the owner's final approval, and only before 13:00.
"""
from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel

from .. import llm
from ..approval import ApprovalDesk, Telegram, pop_commands, read_decision
from ..config import HELPER_TRIGGER_RATIO, PUBLISH_HARD_LIMIT, SCHEDULE, WORK_START, Stage, settings
from ..log import log
from ..publishers import NAMES_AR, PLATFORMS, Post, enabled_platforms, publish_all
from ..state import Job, add_history, clear_active, set_active
from .base import ProductionBot
from .editor import Editor
from .helpers import make_helpers
from .media_hunter import MediaHunter
from .qa import QABot
from .script_writer import Script, ScriptWriter
from .trend_scout import CATEGORIES, TrendScout
from .voice import VoiceBot

STAGES = {s.key: s for s in SCHEDULE}
DAY_STARTED = "بدأ يوم العمل"
REDO_ORDER = ["script", "voice", "media", "edit", "qa"]


class OwnerCommand(BaseModel):
    action: Literal["set_brief", "status", "pause", "resume", "cancel", "note_to_bot", "start_now", "unknown"]
    category: Optional[str] = None
    topic: Optional[str] = None
    notes: Optional[str] = None
    minutes: Optional[float] = None
    target_bot: Optional[str] = None
    reply_ar: str = ""


COMMAND_SYSTEM = (
    "أنت مدير مصنع فيديوهات (البوت التاسع). حوّل رسالة المالك إلى أمر منظم.\n"
    "الفئات: stickman (ستيك مان) | mystery (غموض) | riddles (ألغاز).\n"
    "البوتات: bot1_trend_scout (البحث) bot2_script_writer (السكريبت) bot3_voice (الصوت) "
    "bot4_media_hunter (الصور والفيديو) bot5_editor (المونتاج) bot6_qa (الفحص).\n"
    "set_brief: تحديد فئة/موضوع/مدة/ملاحظات فيديو اليوم. note_to_bot: تعليمات لبوت معين. "
    "status: سؤال عن الحالة. pause/resume/cancel: إيقاف/استئناف/إلغاء عمل اليوم. "
    "start_now: البدء فوراً دون انتظار الثامنة. reply_ar: رد قصير للمالك يؤكد ما فهمته."
)


def _keyword_command(text: str) -> OwnerCommand:
    """Simple keyword-based fallback parser (used in test mode or if Claude is unavailable)."""
    t = text.strip()
    starts = lambda *ws: any(t.lower().startswith(w) for w in ws)  # noqa: E731
    if starts("استمر", "استأنف", "استئناف", "كمل", "resume"):
        return OwnerCommand(action="resume", reply_ar="تم الاستئناف.")
    if any(w in t for w in ("الحالة", "وين وصلت", "status")):
        return OwnerCommand(action="status")
    if starts("توقف", "أوقف", "اوقف", "إيقاف", "pause"):
        return OwnerCommand(action="pause", reply_ar="تم الإيقاف المؤقت.")
    if starts("ألغ", "الغ", "الغاء", "إلغاء", "cancel"):
        return OwnerCommand(action="cancel", reply_ar="تم إلغاء عمل اليوم.")
    if starts("ابدأ", "ابدا", "start"):
        return OwnerCommand(action="start_now", reply_ar="سنبدأ الآن.")
    cat = "stickman" if "ستيك" in t else "mystery" if "غموض" in t else "riddles" if "لغز" in t or "ألغاز" in t else None
    return OwnerCommand(action="set_brief", category=cat, notes=t, reply_ar="تم تسجيل تعليماتك لفيديو اليوم.")


class Manager:
    name = "bot9_manager"
    title_ar = "البوت التاسع — المدير وموزع المهام"

    def __init__(self) -> None:
        self.tg = Telegram()
        self.desk = ApprovalDesk(self.tg)
        self.helpers = make_helpers()
        self.bots: dict[str, ProductionBot] = {}
        self.paused = False
        self.cancelled = False
        self.start_now = False
        self.job: Job | None = None
        self._last_reminder = 0.0
        self.shift = timedelta(0)  # how far the schedule moves when the run starts outside the normal window

    def at(self, t, day=None) -> datetime:
        """The time of a stage's deadline in this run (the fixed schedule, or shifted for a run started by hand)."""
        return settings.at(t, day or (self.job.day if self.job else None)) + self.shift

    # ======================================================================
    # Owner messages
    # ======================================================================
    def tick(self) -> None:
        """Reads new owner messages (Telegram + CLI) and handles them."""
        msgs = self.tg.poll() + pop_commands()
        for m in msgs:
            if self.job and self.desk.handle_owner_message(self.job, m):
                continue
            self.handle_command(m)

    def handle_command(self, text: str) -> str:
        job = self.job or Job()
        try:
            cmd = (_keyword_command(text) if settings.dry_run
                   else llm.ask_json(COMMAND_SYSTEM, f"رسالة المالك: {text}", OwnerCommand, effort="low"))
        except Exception as e:  # noqa: BLE001
            log.warning("Could not parse the command with Claude: %s", e)
            cmd = _keyword_command(text)
        job.event(self.name, f"أمر من المالك: {text} → {cmd.action}")

        if cmd.action == "status":
            reply = self.status_text(job)
        elif cmd.action == "pause":
            self.paused, reply = True, cmd.reply_ar or "تم الإيقاف المؤقت."
        elif cmd.action == "resume":
            self.paused, reply = False, cmd.reply_ar or "تم الاستئناف."
        elif cmd.action == "cancel":
            self.cancelled, reply = True, cmd.reply_ar or "تم إلغاء عمل اليوم."
        elif cmd.action == "start_now":
            self.start_now, reply = True, cmd.reply_ar or "سنبدأ الآن."
        elif cmd.action == "note_to_bot" and cmd.target_bot:
            notes = dict(job.brief.get("bot_notes", {}))
            notes[cmd.target_bot] = (notes.get(cmd.target_bot, "") + "\n" + (cmd.notes or text)).strip()
            job.update_brief(bot_notes=notes)
            reply = cmd.reply_ar or f"تم إبلاغ {cmd.target_bot}."
        else:
            category = cmd.category if cmd.category in CATEGORIES else None
            old_notes = job.brief.get("notes", "")
            job.update_brief(category=category, topic=cmd.topic, minutes=cmd.minutes,
                             notes=(old_notes + "\n" + cmd.notes).strip() if cmd.notes else None)
            reply = cmd.reply_ar or "تم تسجيل تعليماتك."
        self.tg.send("🤖 " + reply)
        print("🤖", reply, flush=True)
        return reply

    def status_text(self, job: Job) -> str:
        lines = [f"📊 حالة مصنع اليوم {job.day} — الساعة {settings.now():%H:%M}"]
        for s in SCHEDULE:
            st = job.stage(s.key)
            icon = {"done": "✅", "running": "⏳", "failed": "❌"}.get(st.get("status", ""), "▫️")
            extra = f" (موافقة: {st['approval']})" if st.get("approval") else ""
            lines.append(f"{icon} {s.title_ar} — الموعد {self.at(s.deadline, job.day):%H:%M}{extra}")
        for h in self.helpers:
            if h.busy:
                lines.append(f"🆘 {h.name} يساعد {h.assisting}")
        return "\n".join(lines)

    # ======================================================================
    # Running the stages and watching the schedule
    # ======================================================================
    def _bot(self, stage: str) -> ProductionBot:
        factory = {"research": TrendScout, "script": ScriptWriter, "voice": VoiceBot,
                   "media": MediaHunter, "edit": Editor, "qa": QABot}
        self.bots[stage] = factory[stage]()  # a fresh bot for every run
        return self.bots[stage]

    def _wait_if_paused(self) -> None:
        while self.paused and not self.cancelled:
            self.tick()
            time.sleep(1)

    def run_stage(self, job: Job, key: str, attempts: int = 2) -> bool:
        stage: Stage = STAGES[key]
        for attempt in range(1, attempts + 1):
            self._wait_if_paused()
            if self.cancelled:
                return False
            bot = self._bot(key)
            started = settings.now()
            deadline = self.at(stage.deadline, job.day)
            job.set_stage(key, status="running", bot=bot.name, started=started.strftime("%H:%M:%S"), attempt=attempt)
            log.info("▶ %s (%s) — deadline %s", stage.title_ar, bot.name, stage.deadline)

            error: list[BaseException] = []
            t = threading.Thread(target=lambda: self._safe_run(bot, job, error), name=bot.name, daemon=True)
            t.start()
            warned = False
            while t.is_alive():
                self.tick()
                self._supervise(job, bot, started, deadline, force=attempt > 1)
                if settings.now() > deadline and not warned:
                    warned = True
                    msg = f"⚠️ تأخير: مرحلة «{stage.title_ar}» تجاوزت موعدها {deadline:%H:%M}. المساعدون يعملون عليها."
                    job.event(self.name, msg)
                    self.tg.send(msg)
                t.join(timeout=1.0)

            if not error:
                job.set_stage(key, status="done", finished=settings.now().strftime("%H:%M:%S"))
                return True
            job.set_stage(key, status="failed", error=str(error[0])[:500])
            job.event(self.name, f"فشلت المرحلة {key} (محاولة {attempt}): {error[0]}")
            log.error("Stage %s failed: %s", key, error[0])
        self.tg.send(f"❌ فشلت مرحلة «{stage.title_ar}» بعد {attempts} محاولات. التفاصيل في سجل اليوم.\n"
                     f"{job.stage(key).get('error', '')}")
        return False

    @staticmethod
    def _safe_run(bot: ProductionBot, job: Job, error: list) -> None:
        try:
            bot.run(job)
        except BaseException as e:  # noqa: BLE001
            error.append(e)

    def _supervise(self, job: Job, bot: ProductionBot, started: datetime, deadline: datetime, force: bool) -> None:
        """Decides whether to call helper 7 / 8 for the current bot."""
        board = bot.board
        if board is None or not board.pending:
            return
        budget = (deadline - started).total_seconds()
        used = (settings.now() - started).total_seconds()
        ratio = 1.0 if budget <= 0 else used / budget
        behind = ratio >= HELPER_TRIGGER_RATIO and board.progress < ratio
        failing = bool(board.errors)
        if not (force or behind or failing):
            return
        reason = ("إعادة محاولة بعد فشل" if force else "تكرار أخطاء في الوحدات" if failing
                  else f"استهلك {ratio:.0%} من الوقت وأنجز {board.progress:.0%} فقط")
        need = 2 if (ratio >= 0.85 or force) else 1
        active = sum(1 for h in self.helpers if h.busy and h.assisting == bot.name)
        for h in self.helpers:
            if active >= need:
                break
            if h.assist(bot, job, reason):
                active += 1

    # ======================================================================
    # Approval steps
    # ======================================================================
    def _approval_tick(self) -> None:
        self.tick()
        # Remind the owner every 15 minutes while an approval is pending
        if self.desk.pending and time.monotonic() - self._last_reminder > (5 if settings.dry_run else 900):
            if self._last_reminder:
                self.tg.send(f"⏰ تذكير: ننتظر موافقتك على «{self.desk.pending}» حتى نلحق موعد النشر قبل 13:00.")
            self._last_reminder = time.monotonic()

    def _wait_owner(self, job: Job, stage: str) -> dict:
        self._last_reminder = 0.0
        return self.desk.wait(job, stage, self.at(PUBLISH_HARD_LIMIT, job.day), on_tick=self._approval_tick)

    def research_and_choose(self, job: Job) -> bool:
        for _round in range(3):
            if not self.run_stage(job, "research"):
                return False
            ideas = job.get("ideas", [])
            text = "🔎 البوت الأول وجد هذه الأفكار الفيروسية لفيديو اليوم:\n\n" + "\n\n".join(
                f"{n}) {i['title']}  [{i['category']}] — قوة الانتشار {i['virality_score']}/10\n"
                f"   الخطاف: {i['hook']}\n   السبب: {i['why_viral']}\n   المصادر: {', '.join(i['sources'][:2])}"
                for n, i in enumerate(ideas, 1))
            self.desk.ask(job, "research", text + "\n\nاختر رقم الفكرة (مثال: «موافق 2») أو «رفض: ملاحظاتك».")
            d = self._wait_owner(job, "research")
            if d["status"] == "approved":
                idx = int(d["value"]) - 1 if d["value"].isdigit() else 0
                if not 0 <= idx < len(ideas):
                    idx = 0
                job.put("chosen_idea", ideas[idx])
                job.update_brief(category=ideas[idx]["category"])
                return True
            if d["status"] == "timeout":
                return False
            job.update_brief(notes=(job.brief.get("notes", "") + "\nملاحظة المالك على الأفكار: " + d["note"]).strip())
        return False

    def write_and_approve_script(self, job: Job) -> bool:
        for _round in range(4):
            if not self.run_stage(job, "script"):
                return False
            s = job.get("script")
            checks = job.get("fact_checks", [])
            fc = "\n".join(f"• {c['claim']} → {c['verdict']}" + (f" (تصحيح: {c['correction']})" if c["correction"] else "")
                           for c in checks) or "لا توجد تواريخ/أرقام للتدقيق"
            body = "\n".join(f"[{n}] {sc['narration']}" for n, sc in enumerate(s["scenes"], 1))
            (job.dir / "script.txt").write_text(f"{s['title']}\n\n{body}", encoding="utf-8")
            text = (f"✍️ السكريبت جاهز (البوت الثاني):\n\nالعنوان: {s['title']}\nنص الصورة المصغرة: {s['thumbnail_text']}\n"
                    f"عدد المشاهد: {len(s['scenes'])}\n\nتدقيق التواريخ والأوقات:\n{fc}\n\nالنص:\n{body}")
            self.desk.ask(job, "script", text, files=[str(job.dir / "script.txt")])
            d = self._wait_owner(job, "script")
            if d["status"] == "approved":
                return True
            if d["status"] == "timeout":
                return False
            job.update_brief(script_feedback=d["note"])
        return False

    def final_review(self, job: Job) -> str:
        """Returns: approved / rejected / timeout. On rejection with feedback, redoes the relevant stage and asks again."""
        for _round in range(3):
            v, s, qa = job.get("video"), job.get("script"), job.get("qa_report", {})
            qa_lines = "\n".join(f"{'✅' if c['ok'] else '⚠️'} {c['check']}: {c['detail']}" for c in qa.get("checks", []))
            text = (f"🎬 الفيديو النهائي جاهز للمراجعة ({v['duration']:.0f} ثانية)\n\n"
                    f"العنوان: {s['title']}\n\nالوصف:\n{self._description(job)}\n\nالوسوم: {', '.join(s['tags'])}\n\n"
                    f"تقرير الفحص (البوت السادس):\n{qa_lines}\n\n"
                    f"سيُنشر على: {'، '.join(NAMES_AR[p] for p in enabled_platforms()) or 'لا توجد منصة مضبوطة'}\n"
                    "هل أنشر الآن؟ «موافق» للنشر على الكل، أو «موافق يوتيوب تيكتوك» لمنصات محددة، "
                    "أو «رفض: ملاحظاتك» للتعديل.")
            files = [v["thumbnail"], job.get("preview_sheet", ""), v["path"]]
            self.desk.ask(job, "final_review", text, files=[f for f in files if f])
            d = self._wait_owner(job, "final_review")
            if d["status"] == "approved":
                job.set_stage("final_review", status="done", finished=settings.now().strftime("%H:%M:%S"))
            if d["status"] != "rejected":
                return d["status"]
            redo = self._stage_for_feedback(d["note"])
            job.event(self.name, f"المالك طلب تعديلاً: {d['note']} → إعادة من مرحلة {redo}")
            self.tg.send(f"🔁 سأعيد العمل من مرحلة «{STAGES[redo].title_ar}» حسب ملاحظتك.")
            if redo == "script":
                job.update_brief(script_feedback=d["note"])
                if not self.write_and_approve_script(job):
                    return "failed"
            else:
                job.update_brief(bot_notes={**job.brief.get("bot_notes", {}), STAGES[redo].bot: d["note"]})
                self._apply_feedback_to_plan(job, redo, d["note"])
            start = REDO_ORDER.index(redo) + (1 if redo == "script" else 0)
            for key in REDO_ORDER[start:]:
                if not self.run_stage(job, key):
                    return "failed"
        return "rejected"

    def _apply_feedback_to_plan(self, job: Job, stage: str, note: str) -> None:
        """Turns the owner's note into concrete changes to the scene plan (search terms, poses, mood, on-screen text, narration)."""
        prompt = (
            f"السكريبت الحالي:\n{json.dumps(job.get('script'), ensure_ascii=False, indent=2)}\n\n"
            f"ملاحظة المالك على الفيديو النهائي (تخص مرحلة {stage}): {note}\n"
            "عدّل حقول المشاهد اللازمة فقط لتطبيق الملاحظة (visual_query_en / visual_type / stickman_pose / mood / "
            "on_screen_text، أو علامات الترقيم في narration لتحسين الإلقاء). لا تغيّر المعنى ولا عدد المشاهد."
        )
        revised = llm.ask_json("أنت مخرج فيديو ينفذ ملاحظات المالك بدقة.", prompt, Script, effort="medium",
                               mock=job.get("script"))
        job.put("script", revised.model_dump())

    @staticmethod
    def _stage_for_feedback(note: str) -> str:
        if any(w in note for w in ("صوت", "التعليق", "النطق", "القراءة")):
            return "voice"
        if any(w in note for w in ("صور", "لقطة", "لقطات", "مشهد", "فيديوهات")):
            return "media"
        if any(w in note for w in ("مونتاج", "ترجمة", "موسيقى", "انتقال", "خط", "سرعة")):
            return "edit"
        return "script"

    def _description(self, job: Job) -> str:
        s = job.get("script")
        credits = sorted({m["credit"] for m in job.get("media", []) if not m["credit"].startswith("stickman")})
        desc = s["description"]
        if credits:
            desc += ("\n\n🎞️ Footage credits:\n" if settings.language == "en" else "\n\n🎞️ مصادر اللقطات:\n") + "\n".join(credits)
        desc += "\n\n" + " ".join("#" + t.replace(" ", "_") for t in s["tags"][:5])
        return desc

    # ======================================================================
    # Publishing — guarded by the owner's approval
    # ======================================================================
    def publish(self, job: Job, *, allow_late: bool = False, platforms: list[str] | None = None) -> dict | None:
        d = read_decision(job, "final_review")
        if not d or d["status"] != "approved":
            raise PermissionError("لا يمكن النشر: لا توجد موافقة نهائية من المالك على هذا الفيديو.")
        if settings.now() >= self.at(PUBLISH_HARD_LIMIT, job.day) and not allow_late:
            msg = (f"⏰ وصلت موافقتك بعد موعد النشر {self.at(PUBLISH_HARD_LIMIT, job.day):%H:%M}. لم أنشر تلقائياً حفاظاً على القاعدة. "
                   "للنشر رغم التأخير: من التطبيق زر «انشر رغم التأخير» أو python -m factory publish --late")
            self.tg.send(msg)
            job.event(self.name, msg)
            return None
        # Platforms: whatever the owner named in the approval, otherwise every enabled platform
        chosen = platforms or [p for p in (d.get("value") or "").split(",") if p in PLATFORMS] or enabled_platforms()
        if not chosen:
            raise RuntimeError("لا توجد منصة نشر مضبوطة. أضف بيانات يوتيوب/تيك توك/إنستغرام في الإعدادات.")
        s, v = job.get("script"), job.get("video")
        post = Post(video=Path(v["path"]), vertical_video=Path(v["vertical"]) if v.get("vertical") else None,
                    thumbnail=Path(v["thumbnail"]), title=s["title"], description=self._description(job), tags=s["tags"])
        results = publish_all(post, chosen, already=job.get("published") or {})
        job.put("published", results)
        ok = {k: r for k, r in results.items() if r.get("url")}
        failed = {k: r for k, r in results.items() if r.get("error")}
        if ok:
            job.set_stage("publish", status="done" if not failed else "partial",
                          finished=settings.now().strftime("%H:%M:%S"))
            add_history({"date": job.day.isoformat(), "title": s["title"], "category": job.brief.get("category"),
                         "urls": {k: r["url"] for k, r in ok.items()}})
        lines = [f"🚀 {NAMES_AR[k]}: {r['url']}" for k, r in ok.items()]
        lines += [f"❌ {NAMES_AR[k]}: {r['error']}" for k, r in failed.items()]
        msg = "نتيجة النشر:\n" + "\n".join(lines)
        self.tg.send(msg)
        job.event(self.name, msg)
        return results

    # ======================================================================
    # The full workday
    # ======================================================================
    def missing_keys(self) -> list[str]:
        """Keys that must be set before starting (in Arabic, as the owner sees them in Settings)."""
        if settings.dry_run:
            return []
        from ..config import env
        need = {"ANTHROPIC_API_KEY": "مفتاح Claude", "ELEVENLABS_API_KEY": "مفتاح ElevenLabs",
                "ELEVENLABS_VOICE_ID": "معرّف صوت ElevenLabs"}
        return [label for key, label in need.items() if not env(key)]

    def halt(self, job: Job, reason: str) -> None:
        """Stop the day with a clear reason, shown in the app and on Telegram."""
        job.data["halt_reason"] = reason
        job.save()
        job.event(self.name, "🛑 " + reason)
        self.tg.send("🛑 " + reason)

    def run_day(self, start_now: bool = False) -> None:
        self.job = job = Job()
        self.start_now = start_now
        start = settings.at(WORK_START, job.day)
        if not start_now and settings.now() < start:
            self.tg.send(f"🌙 المصنع جاهز. سيبدأ العمل الساعة {WORK_START:%H:%M}. أرسل تعليماتك لفيديو اليوم في أي وقت.")
            while settings.now() < start and not self.start_now and not self.cancelled:
                self.tick()
                time.sleep(2)

        self.tick()  # read any instructions the owner sent before work started
        missing = self.missing_keys()
        if missing:
            self.halt(job, "لم يبدأ العمل: أدخل في تبويب «الإعدادات»: " + "، ".join(missing) + " ثم اضغط «ابدأ الآن».")
            return

        if any(e.get("msg") == DAY_STARTED for e in job.data.get("events", [])):
            job.reset_run()  # a second run on the same day starts clean

        # A run started by hand outside the normal window (at night, for example) gets the same 5-hour
        # schedule counted from now, instead of deadlines that have already passed.
        now = settings.now()
        if now > settings.at(WORK_START, job.day) + timedelta(minutes=15) and now >= settings.at(PUBLISH_HARD_LIMIT, job.day) - timedelta(hours=1):
            self.shift = now - settings.at(WORK_START, job.day)
        elif now < settings.at(WORK_START, job.day):
            self.shift = now - settings.at(WORK_START, job.day)
        job.data["schedule"] = {st.key: self.at(st.deadline, job.day).strftime("%H:%M") for st in SCHEDULE}
        job.save()

        set_active(job.day)
        try:
            self._run(job)
        finally:
            clear_active()

    def _run(self, job: Job) -> None:
        job.event(self.name, DAY_STARTED)
        brief = json.dumps(job.brief, ensure_ascii=False) if job.brief else "لا توجد تعليمات خاصة (سأختار الأفضل)"
        self.tg.send(f"☀️ بدأ العمل. تعليمات اليوم: {brief}\nموعد النشر: قبل {self.at(PUBLISH_HARD_LIMIT, job.day):%H:%M}. "
                     "سأستشيرك قبل كل خطوة مهمة وقبل أي نشر.")

        ok = (self.research_and_choose(job) and self.write_and_approve_script(job)
              and all(self.run_stage(job, k) for k in ("voice", "media", "edit", "qa")))
        if self.cancelled:
            self.halt(job, "تم إلغاء عمل اليوم بطلبك.")
            return
        if not ok:
            failed = next((s for s in SCHEDULE if job.stage(s.key).get("status") == "failed"), None)
            timeout = next((s for s in SCHEDULE if job.stage(s.key).get("approval") == "timeout"), None)
            if failed:
                reason = f"توقف العمل: فشلت مرحلة «{failed.title_ar}». السبب: {job.stage(failed.key).get('error', '')}"
            elif timeout:
                reason = f"توقف العمل: انتهى وقت انتظار موافقتك على «{timeout.title_ar}»."
            else:
                reason = "توقف العمل قبل الوصول للنشر."
            self.halt(job, reason + " يمكنك الضغط على «ابدأ الآن» للمحاولة من جديد.")
            return
        decision = self.final_review(job)
        if decision == "approved":
            self.publish(job)
        else:
            self.tg.send(f"📭 لم يُنشر فيديو اليوم (القرار: {decision}). الفيديو محفوظ في {job.dir}")
        job.event(self.name, "انتهى يوم العمل")

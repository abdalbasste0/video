"""Orchestrator — receives an idea, runs the agent pipeline, tracks status, retries,
routes QA failures and revision notes to the responsible agent, resumes after crashes.

Idea → Script → (Voice ∥ Assets) → Editor → Motion → Colorist → VFX → Sound → Draft
     → QA(draft) → Render → QA(export) → Approval → [WAIT for owner] → Publisher (only on ✅)
"""
from __future__ import annotations

import logging
import re
import shutil
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import llm, media
from .agents.approval_agent import ApprovalAgent
from .agents.assets_agent import AssetsAgent
from .agents.base import AgentContext
from .agents.colorist_agent import ColoristAgent
from .agents.editor_agent import EditorAgent
from .agents.motion_agent import MotionAgent
from .agents.publisher_agent import PublisherAgent
from .agents.qa_agent import QAAgent
from .agents.render_agent import RenderAgent
from .agents.script_agent import ScriptAgent
from .agents.sound_agent import SoundAgent
from .agents.vfx_agent import VFXAgent
from .agents.voice_agent import VoiceAgent
from .capcut.draft_builder import DraftBuilder
from .config import Settings
from .project import Project
from .state import Store
from .telegram import Telegram

log = logging.getLogger("orchestrator")

PIPELINE = ["script", "voice", "assets", "editor", "motion", "colorist", "vfx", "sound",
            "draft", "qa_draft", "render", "qa_export", "approval"]
PARALLEL = {"voice", "assets"}
AGENTS = {"script": ScriptAgent, "voice": VoiceAgent, "assets": AssetsAgent, "editor": EditorAgent,
          "motion": MotionAgent, "colorist": ColoristAgent, "vfx": VFXAgent, "sound": SoundAgent,
          "render": RenderAgent, "approval": ApprovalAgent}
STEP_RETRIES = 3

# revision-note routing (fallback when Claude is not configured)
ROUTES = [
    ("colorist", r"colou?r|grade|warm|cold|cool|bright|dark|saturat|contrast|لون|ألوان|الوان|دافئ|بارد|إضاءة|اضاءة|سطوع|تشبع"),
    ("sound", r"music|sound|audio|volume|loud|quiet|sfx|موسيقى|صوت عالي|الصوت|مؤثرات صوتية|هادئ"),
    ("voice", r"voice|narrat|speak|faster|slower|accent|المعلق|التعليق الصوتي|أسرع|ابطأ|أبطأ|نبرة"),
    ("motion", r"caption|subtitle|text|font|title|lower third|ترجمة|نص|خط|عنوان|الكتابة"),
    ("vfx", r"effect|grain|glow|shake|vignette|blur|تأثير|مؤثرات بصرية|اهتزاز|ضبابية"),
    ("assets", r"image|clip|footage|b-roll|picture|stock|صورة|صور|لقطة|مقطع"),
    ("editor", r"cut|pace|pacing|transition|zoom|rhythm|قص|انتقال|إيقاع|زوم|تقريب"),
    ("script", r"script|hook|story|wording|cta|سكربت|نص الفيديو|الخطاف|القصة|البداية"),
]


class Orchestrator:
    def __init__(self, settings: Settings, store: Store):
        self.s = settings
        self.store = store
        self.max_qa = int(settings.get("runtime.max_retries", 3))
        self.tg = Telegram(settings.env("TELEGRAM_BOT_TOKEN"), settings.env("TELEGRAM_OWNER_ID"))

    # ================================================================ public
    def submit(self, idea: str, fmt: str | None = None, language: str | None = None) -> str:
        fmt = fmt or self.s.get("channel.default_format", "9:16")
        language = language or self.s.get("channel.language", "ar")
        vid = self.store.create_video(idea, fmt, language)
        self.store.reset_tasks(vid, PIPELINE)
        self.store.log(vid, "orchestrator", f"new idea queued: {idea!r} ({fmt}, {language})")
        return vid

    def process(self, vid: str) -> str:
        """Run (or resume) a video up to PENDING_APPROVAL. Never publishes."""
        v = self.store.video(vid)
        if v["status"] in ("PENDING_APPROVAL", "APPROVED", "PUBLISHING", "PUBLISHED", "REJECTED"):
            return v["status"]
        self.store.set_video_status(vid, "IN_PROGRESS")
        project = Project.open(self.s.projects_dir, vid)
        qa_rounds = int(v["meta"].get("qa_rounds", 0))
        try:
            while True:
                for step in self._pending_steps(vid):
                    if step == "voice":   # Voice ∥ Assets
                        group = [s for s in ("voice", "assets") if self._is_pending(vid, s)]
                        with ThreadPoolExecutor(max_workers=2) as ex:
                            for f in [ex.submit(self._run_step, vid, project, s) for s in group]:
                                f.result()
                        continue
                    if step == "assets" and not self._is_pending(vid, "assets"):
                        continue
                    if step in ("qa_draft", "qa_export"):
                        report = self._run_step(vid, project, step)
                        if not report["passed"]:
                            qa_rounds += 1
                            self.store.merge_meta(vid, qa_rounds=qa_rounds)
                            if qa_rounds > self.max_qa:
                                raise RuntimeError(f"QA still failing after {self.max_qa} retries: "
                                                   f"{[i['reason'] for i in report['issues']][:5]}")
                            self._route_qa(vid, report)
                            break   # restart loop from the earliest reset step
                        continue
                    self._run_step(vid, project, step)
                else:
                    break
                if not self._pending_steps(vid):
                    break
            self.store.set_video_status(vid, "PENDING_APPROVAL")
            self.store.log(vid, "orchestrator", "waiting for owner decision (PENDING_APPROVAL)")
            return "PENDING_APPROVAL"
        except Exception as e:
            self.store.set_video_status(vid, "FAILED")
            self.store.log(vid, "orchestrator", f"FAILED: {e}", "ERROR")
            log.error("video %s failed: %s\n%s", vid, e, traceback.format_exc())
            self._notify(f"❌ Video {vid} failed: {e}\nResume after fixing: /resume {vid}")
            return "FAILED"

    def resume_all(self) -> None:
        for status in ("IN_PROGRESS", "REVISING", "QUEUED"):
            for v in self.store.videos(status):
                self.process(v["id"])

    def revise(self, vid: str, notes: str) -> list[str]:
        """Owner asked for changes → route ONLY to the responsible agent(s), rebuild downstream."""
        agents = self.route_notes(notes)
        v = self.store.video(vid)
        overrides = v["meta"].get("overrides", {})
        for a in agents:
            for k, val in self._note_to_params(a, notes).items():
                cur = overrides.setdefault(a, {}).get(k)
                overrides[a][k] = (cur or 0) + val if isinstance(val, (int, float)) and not isinstance(val, bool) else val
        self.store.update_video(vid, revision=v["revision"] + 1)
        self.store.merge_meta(vid, overrides=overrides, qa_rounds=0)
        self._reset_from(vid, agents, notes)
        self.store.set_video_status(vid, "REVISING")
        self.store.log(vid, "orchestrator", f"revision routed to {agents}: {notes}")
        return agents

    def publish(self, vid: str) -> dict:
        """Called ONLY by the approval bot / CLI after the owner's ✅ is recorded."""
        project = Project.open(self.s.projects_dir, vid)
        ctx = AgentContext(self.s, self.store, project, self.store.video(vid))
        return PublisherAgent(ctx).run()   # PublisherAgent re-verifies the owner approval itself

    # ================================================================ routing
    def route_notes(self, notes: str) -> list[str]:
        if llm.available():
            try:
                out = llm.json_call(
                    "Route a video-revision note to the responsible production agents. Agents: script (wording, "
                    "hook, story), voice (narration speed/voice), assets (images/clips/music choice), editor (cuts, "
                    "pacing, transitions, zoom), motion (captions, text, fonts, titles), colorist (color, "
                    "brightness, look), vfx (visual effects), sound (music volume, mix, sfx). Pick the minimum set.",
                    f"Note: {notes}",
                    {"type": "object", "properties": {"agents": {"type": "array", "items": {
                        "type": "string", "enum": list(AGENTS.keys() - {"render", "approval"})}}},
                     "required": ["agents"], "additionalProperties": False},
                    model=self.s.get("script.model", "claude-opus-5-5"), effort="low", max_tokens=1024)
                if out["agents"]:
                    return out["agents"]
            except Exception as e:
                log.warning("LLM routing failed (%s); using keywords", e)
        low = notes.lower()
        hits = [a for a, rx in ROUTES if re.search(rx, low)]
        return hits or ["script"]

    @staticmethod
    def _note_to_params(agent: str, notes: str) -> dict:
        n = notes.lower()
        more = bool(re.search(r"more|increase|higher|louder|bigger|warmer|brighter|أكثر|اكثر|أعلى|اعلى|ارفع|أكبر|اكبر", n))
        less = bool(re.search(r"less|decrease|lower|quieter|smaller|cooler|darker|أقل|اقل|اخفض|أصغر|اصغر|أهدأ", n))
        sign = 1 if more and not less else (-1 if less and not more else 0)
        if agent == "colorist":
            p = {}
            if re.search(r"warm|cold|cool|دافئ|أدفأ|ادفأ|دفء|بارد|أبرد|حرار", n):
                p["temperature"] = 8 if re.search(r"warm|دافئ|أدفأ|ادفأ|دفء", n) else -8
            if re.search(r"bright|dark|سطوع|إضاءة|اضاءة|مظلم|فاتح", n):
                p["brightness"] = 6 if re.search(r"bright|فاتح|أفتح|سطوع", n) and sign >= 0 else -6
            if re.search(r"saturat|vivid|تشبع|حيوي", n):
                p["saturation"] = 8 * (sign or 1)
            if re.search(r"contrast|تباين", n):
                p["contrast"] = 8 * (sign or 1)
            return p
        if agent == "sound":
            return {"music_db": 4 * (sign or -1)} if re.search(r"music|موسيقى", n) else {}
        if agent == "motion":
            return {"size": 8 * sign} if sign and re.search(r"caption|text|font|subtitle|خط|نص|ترجمة", n) else {}
        if agent == "voice":
            if re.search(r"faster|أسرع|اسرع", n):
                return {"rate": "+15%"}
            if re.search(r"slower|أبطأ|ابطأ", n):
                return {"rate": "-5%"}
        if agent == "vfx" and re.search(r"no effect|remove effect|بدون تأثير|ازل|أزل", n):
            return {"enabled": False}
        if agent == "editor" and re.search(r"no transition|بدون انتقال", n):
            return {"transitions": False}
        return {}

    def _route_qa(self, vid: str, report: dict) -> None:
        errs = [i for i in report["issues"] if i["severity"] == "error"]
        agents = sorted({i["agent"] for i in errs}, key=PIPELINE.index)
        reason = "; ".join(f"{i['agent']}: {i['reason']}" for i in errs)
        self.store.log(vid, "qa", f"routing back to {agents}: {reason}", "WARNING")
        self._reset_from(vid, agents, f"QA: {reason}")

    def _reset_from(self, vid: str, agents: list[str], notes: str) -> None:
        idx = min(PIPELINE.index(a) for a in agents)
        to_reset = [s for s in PIPELINE[idx:] if s not in PARALLEL or s in agents]
        if "script" in agents:
            to_reset = PIPELINE[:]          # new script → everything downstream
        self.store.reset_tasks(vid, to_reset)
        for a in agents:
            self.store.set_task(vid, a, "PENDING", notes=notes)

    # ================================================================ steps
    def _is_pending(self, vid: str, step: str) -> bool:
        t = self.store.task(vid, step)
        return not t or t["status"] != "DONE"

    def _pending_steps(self, vid: str) -> list[str]:
        return [s for s in PIPELINE if self._is_pending(vid, s)]

    def _run_step(self, vid: str, project: Project, step: str):
        last_err = None
        for attempt in range(1, STEP_RETRIES + 1):
            self.store.set_task(vid, step, "RUNNING", bump_attempt=True)
            task = self.store.task(vid, step)
            ctx = AgentContext(self.s, self.store, project, self.store.video(vid), notes=task.get("notes", ""))
            t0 = time.time()
            try:
                if step == "draft":
                    result = self._build_draft(ctx)
                elif step in ("qa_draft", "qa_export"):
                    result = QAAgent(ctx).run(stage=step.split("_")[1])
                else:
                    result = AGENTS[step](ctx).run()
                self.store.set_task(vid, step, "DONE")
                self.store.log(vid, step, f"DONE in {time.time() - t0:.1f}s (attempt {attempt})")
                return result
            except Exception as e:
                last_err = e
                self.store.set_task(vid, step, "FAILED", error=str(e)[:2000])
                self.store.log(vid, step, f"FAILED attempt {attempt}: {e}", "ERROR")
                log.warning("%s/%s attempt %d failed: %s", vid, step, attempt, e)
                time.sleep(min(2 ** attempt, 20))
        raise RuntimeError(f"step '{step}' failed {STEP_RETRIES}×: {last_err}")

    def _build_draft(self, ctx: AgentContext) -> dict:
        tl = ctx.project.read_json("draft", "timeline.json")
        v = ctx.video
        safe_title = re.sub(r"[^\w؀-ۿ -]", "", v.get("title") or "video").strip()[:40] or "video"
        name = f"VF_{v['id']}_{safe_title}".replace(" ", "_")
        template = self.s.get("capcut.template_draft") or None
        portable = self.s.runtime != "windows"
        builder = DraftBuilder(self.s, tl, name, self.s.drafts_dir, Path(template) if template else None, portable)
        out = builder.build()
        # cover image for CapCut's home screen
        first = tl["video"][0]["path"]
        try:
            media.ffmpeg("-i", first, "-frames:v", "1", "-vf", "scale=360:-2", str(out / "draft_cover.jpg"))
        except Exception:
            pass
        zip_path = None
        if portable:
            zip_path = shutil.make_archive(str(ctx.project.dir("draft") / name), "zip", out.parent, out.name)
        self.store.merge_meta(v["id"], draft_name=name, draft_dir=str(out), draft_zip=zip_path,
                              draft_skipped=builder.skipped)
        self.store.log(v["id"], "draft", f"CapCut draft written: {out}" + (f" (+zip {zip_path})" if zip_path else ""))
        return {"draft_dir": str(out), "zip": zip_path}

    def _notify(self, text: str) -> None:
        if self.tg.enabled:
            try:
                self.tg.send(text)
            except Exception as e:
                log.warning("telegram notify failed: %s", e)

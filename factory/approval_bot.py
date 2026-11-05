"""Approval Bot + always-on worker (the process that "never stops").

* Telegram long-polling: only TELEGRAM_OWNER_ID can decide anything.
* Commands: /new <idea> [16:9] [en|ar] · /status · /list · /resume <id> · /help
* Buttons:  ✅ Publish → choose platforms → 🚀 Confirm   |   ✏️ Revise → type notes   |   ❌ Reject
* A worker thread builds videos and resumes unfinished ones after a crash/reboot.
* Pending videos wait forever. Nothing here or anywhere else publishes without ✅ + 🚀.
"""
from __future__ import annotations

import json
import logging
import queue
import threading
import time
from pathlib import Path

from . import media
from .config import Settings
from .orchestrator import Orchestrator
from .project import Project
from .state import Store
from .telegram import Telegram, btn

log = logging.getLogger("approval_bot")

HELP = ("🎬 Video Factory\n"
        "/new <idea> — start a video (add 16:9 for YouTube landscape, en for English)\n"
        "/status — what is running / waiting\n/list — last videos\n/resume <id> — retry a failed video\n\n"
        "Every finished video waits for YOUR ✅ — nothing is ever published automatically.")


# ===================================================================== decisions
def owner_decide(orch: Orchestrator, store: Store, settings: Settings, vid: str, decision: str,
                 decided_by: str, notes: str = "", platforms: list[str] | None = None) -> str:
    """Single entry point for owner decisions (Telegram or local CLI)."""
    v = store.video(vid)
    if not v:
        return "unknown video id"
    if v["status"] != "PENDING_APPROVAL":
        return f"video is {v['status']}, not waiting for a decision"
    final = Project.open(settings.projects_dir, vid).final_file
    if decision == "APPROVE":
        if not platforms:
            return "choose at least one platform"
        store.record_decision(vid, "APPROVE", decided_by, render_sha256=media.sha256(final), platforms=platforms)
        store.set_video_status(vid, "APPROVED")
        return "approved"
    if decision == "REJECT":
        store.record_decision(vid, "REJECT", decided_by, notes=notes)
        store.set_video_status(vid, "REJECTED")
        return "rejected"
    if decision == "REVISE":
        store.record_decision(vid, "REVISE", decided_by, notes=notes)
        agents = orch.revise(vid, notes)
        return f"revision routed to: {', '.join(agents)}"
    return "unknown decision"


# ===================================================================== daemon
class FactoryDaemon:
    def __init__(self, settings: Settings, store: Store):
        self.s = settings
        self.store = store
        self.orch = Orchestrator(settings, store)
        self.tg = Telegram(settings.env("TELEGRAM_BOT_TOKEN"), settings.env("TELEGRAM_OWNER_ID"))
        self.jobs: queue.Queue = queue.Queue()
        self.state_file = settings.root / "bot_state.json"
        self.state = self._load_state()
        self.stop = threading.Event()

    # ---------- persistence of bot UI state ----------
    def _load_state(self) -> dict:
        try:
            return json.loads(self.state_file.read_text(encoding="utf-8"))
        except Exception:
            return {"offset": 0, "awaiting_notes": None, "platform_choice": {}}

    def _save_state(self) -> None:
        self.state_file.write_text(json.dumps(self.state), encoding="utf-8")

    # ---------- worker ----------
    def worker(self) -> None:
        self.orch.resume_all()   # crash recovery: continue unfinished videos
        poll = float(self.s.get("runtime.worker_poll_sec", 5))
        while not self.stop.is_set():
            try:
                kind, vid = self.jobs.get(timeout=poll)
            except queue.Empty:
                for st in ("QUEUED", "REVISING"):
                    for v in self.store.videos(st):
                        self.jobs.put(("process", v["id"]))
                continue
            try:
                if kind == "process":
                    self.orch.process(vid)
                elif kind == "publish":
                    res = self.orch.publish(vid)
                    self._send(f"🚀 Published {vid}:\n" + "\n".join(f"• {k}: {v}" for k, v in res.items()))
            except Exception as e:
                log.exception("job %s %s failed", kind, vid)
                self._send(f"⚠️ {kind} {vid} failed: {e}")

    # ---------- telegram ----------
    def _send(self, text: str, buttons=None) -> None:
        if self.tg.enabled:
            try:
                self.tg.send(text, buttons)
            except Exception as e:
                log.warning("send failed: %s", e)
        else:
            print(text)

    def bot(self) -> None:
        if not self.tg.enabled:
            log.warning("Telegram not configured (TELEGRAM_BOT_TOKEN / TELEGRAM_OWNER_ID) — bot disabled")
            self.stop.wait()
            return
        self._send("🟢 Video Factory is online.\n" + HELP)
        backoff = 2
        while not self.stop.is_set():
            try:
                for u in self.tg.updates(self.state["offset"], int(self.s.get("telegram.poll_timeout_sec", 50))):
                    self.state["offset"] = u["update_id"] + 1
                    self._save_state()
                    try:
                        self.handle(u)
                    except Exception as e:
                        log.exception("update failed")
                        self._send(f"⚠️ {e}")
                backoff = 2
            except Exception as e:   # network drop on the phone etc. → keep going
                log.warning("polling error: %s (retry in %ss)", e, backoff)
                time.sleep(backoff)
                backoff = min(backoff * 2, 120)

    def _is_owner(self, user: dict) -> bool:
        return str(user.get("id")) == self.tg.owner_id

    def handle(self, u: dict) -> None:
        if "callback_query" in u:
            cq = u["callback_query"]
            if not self._is_owner(cq["from"]):
                self.tg.answer(cq["id"], "Not authorized")
                return
            self.on_button(cq)
            return
        msg = u.get("message") or {}
        if not msg or not self._is_owner(msg.get("from", {})):
            return   # silently ignore strangers
        text = (msg.get("text") or "").strip()
        if text.startswith("/"):
            self.on_command(text)
        elif self.state.get("awaiting_notes"):
            vid = self.state["awaiting_notes"]
            self.state["awaiting_notes"] = None
            self._save_state()
            res = owner_decide(self.orch, self.store, self.s, vid, "REVISE", self.tg.owner_id, notes=text)
            self._send(f"✏️ {res}\nRebuilding… you will get the new version for approval.")
            self.jobs.put(("process", vid))
        elif text:
            self._send("Send /new <idea> to start a video, or /help.")

    def on_command(self, text: str) -> None:
        cmd, _, arg = text.partition(" ")
        cmd = cmd.split("@")[0].lower()
        if cmd in ("/start", "/help"):
            self._send(HELP)
        elif cmd == "/new":
            if not arg.strip():
                self._send("Usage: /new <your idea>")
                return
            words = arg.split()
            fmt = "16:9" if "16:9" in words else None
            lang = "en" if "en" in words else ("ar" if "ar" in words else None)
            idea = " ".join(w for w in words if w not in ("16:9", "9:16", "en", "ar"))
            vid = self.orch.submit(idea, fmt, lang)
            self._send(f"🏭 Queued {vid}\n💡 {idea}\nI'll message you when it is ready for your decision.")
            self.jobs.put(("process", vid))
        elif cmd == "/status":
            rows = [v for v in self.store.videos() if v["status"] not in ("PUBLISHED", "REJECTED")][:15]
            lines = []
            for v in rows:
                tasks = {t["agent"]: t["status"] for t in self.store.tasks(v["id"])}
                running = [a for a, s in tasks.items() if s == "RUNNING"]
                lines.append(f"• {v['id']} — {v['status']}" + (f" ({', '.join(running)})" if running else "")
                             + f"\n  {v['title'] or v['idea'][:50]}")
            self._send("\n".join(lines) or "Nothing in progress.")
        elif cmd == "/list":
            self._send("\n".join(f"• {v['id']} {v['status']} — {v['title'] or v['idea'][:40]}"
                                 for v in self.store.videos()[:20]) or "No videos yet.")
        elif cmd == "/resume" and arg.strip():
            vid = arg.strip()
            v = self.store.video(vid)
            if v and v["status"] == "FAILED":
                self.store.merge_meta(vid, qa_rounds=0)
                self.store.set_video_status(vid, "QUEUED")
                self.jobs.put(("process", vid))
                self._send(f"🔁 Resuming {vid} from the last successful step")
            else:
                self._send("Only FAILED videos can be resumed.")
        else:
            self._send(HELP)

    def on_button(self, cq: dict) -> None:
        data = cq.get("data", "")
        kind, _, rest = data.partition(":")
        msg = cq.get("message", {})
        chat, mid = msg.get("chat", {}).get("id"), msg.get("message_id")
        if kind in ("pl", "go", "bk"):
            vid = rest.split(":")[0]
        else:
            vid = rest
        v = self.store.video(vid)
        if not v or v["status"] != "PENDING_APPROVAL":
            self.tg.answer(cq["id"], f"Video is {v['status'] if v else 'unknown'}")
            return
        if kind == "ap":
            fmt_key = f"platforms.default_for_{v['fmt'].replace(':', '_')}"
            self.state["platform_choice"][vid] = list(self.s.get(fmt_key, []))
            self._save_state()
            self.tg.answer(cq["id"])
            self.tg.edit_buttons(chat, mid, self._platform_buttons(vid))
        elif kind == "pl":
            p = rest.split(":")[1]
            sel = self.state["platform_choice"].setdefault(vid, [])
            sel.remove(p) if p in sel else sel.append(p)
            self._save_state()
            self.tg.answer(cq["id"])
            self.tg.edit_buttons(chat, mid, self._platform_buttons(vid))
        elif kind == "go":
            platforms = self.state["platform_choice"].get(vid, [])
            res = owner_decide(self.orch, self.store, self.s, vid, "APPROVE", str(cq["from"]["id"]),
                               platforms=platforms)
            self.tg.answer(cq["id"], res)
            if res == "approved":
                self.tg.edit_buttons(chat, mid, None)
                self._send(f"✅ Approved by you → publishing to {', '.join(platforms)}…")
                self.jobs.put(("publish", vid))
            else:
                self._send(f"⚠️ {res}")
        elif kind == "bk":
            from .agents.approval_agent import decision_buttons
            self.tg.answer(cq["id"])
            self.tg.edit_buttons(chat, mid, decision_buttons(vid))
        elif kind == "rv":
            self.state["awaiting_notes"] = vid
            self._save_state()
            self.tg.answer(cq["id"])
            self._send("✏️ Write your notes in one message (e.g. 'warmer colors, music lower, bigger captions').")
        elif kind == "rj":
            res = owner_decide(self.orch, self.store, self.s, vid, "REJECT", str(cq["from"]["id"]))
            self.tg.answer(cq["id"], res)
            self.tg.edit_buttons(chat, mid, None)
            self._send(f"❌ {vid} rejected. It will never be published.")

    def _platform_buttons(self, vid: str) -> list[list[dict]]:
        sel = self.state["platform_choice"].get(vid, [])
        row = [btn(("☑️ " if p in sel else "⬜ ") + p, f"pl:{vid}:{p}") for p in self.s.get("platforms.available", [])]
        return [row, [btn("🚀 Confirm publish", f"go:{vid}"), btn("↩️ Back", f"bk:{vid}")]]

    # ---------- run ----------
    def run_forever(self) -> None:
        threads = [threading.Thread(target=self.worker, name="worker", daemon=True),
                   threading.Thread(target=self.bot, name="bot", daemon=True)]
        for t in threads:
            t.start()
        try:
            while True:
                for i, t in enumerate(threads):
                    if not t.is_alive():         # self-heal a crashed thread
                        log.error("thread %s died → restarting", t.name)
                        target = self.worker if t.name == "worker" else self.bot
                        threads[i] = threading.Thread(target=target, name=t.name, daemon=True)
                        threads[i].start()
                (self.s.root / "heartbeat.txt").write_text(time.strftime("%Y-%m-%d %H:%M:%S"))
                time.sleep(15)
        except KeyboardInterrupt:
            self.stop.set()

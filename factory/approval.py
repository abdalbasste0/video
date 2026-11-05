"""The owner approval desk and the owner's message inbox.

Rule: nothing moves to the next stage, and nothing is ever published, without the owner's explicit approval.

Two channels for talking to the owner:
 1. Telegram (if TELEGRAM_BOT_TOKEN and TELEGRAM_OWNER_CHAT_ID are set): the bots send the
    summary, video, and thumbnail, and the owner replies in plain words.
 2. Command line: python -m factory approve/reject ... (always works, with or without Telegram).

Decisions are saved as separate files in workspace/<date>/approvals/<stage>.json
so different processes can write them without clashing.
"""
from __future__ import annotations

import json
import re
import time
import uuid
from datetime import datetime
from pathlib import Path

import requests

from .config import settings
from .log import log
from .state import Job

APPROVE_WORDS = ("موافق", "موافقة", "نعم", "تمام", "اعتمد", "معتمد", "انشر", "ok", "yes", "approve", "✅", "👍")
REJECT_WORDS = ("رفض", "ارفض", "لا", "عدل", "عدّل", "تعديل", "غير", "no", "reject", "❌")

INBOX = settings.workspace / "inbox"


# ---------------------------------------------------------------------------
# Decision files
# ---------------------------------------------------------------------------
def _decision_path(job: Job, stage: str) -> Path:
    d = job.dir / "approvals"
    d.mkdir(exist_ok=True)
    return d / f"{stage}.json"


def record_decision(job: Job, stage: str, status: str, value: str = "", note: str = "", by: str = "cli") -> None:
    data = {"status": status, "value": value, "note": note, "by": by, "at": settings.now().isoformat()}
    _decision_path(job, stage).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_decision(job: Job, stage: str) -> dict | None:
    p = _decision_path(job, stage)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def clear_decision(job: Job, stage: str) -> None:
    _decision_path(job, stage).unlink(missing_ok=True)


def parse_reply(text: str) -> tuple[str, str, str] | None:
    """Turns the owner's reply into (decision, value, note). Example: "موافق 2" / "رفض: البداية ضعيفة"."""
    t = text.strip()
    low = t.lower()
    num = re.search(r"\b(\d{1,2})\b", t)
    if any(low.startswith(w) for w in REJECT_WORDS):
        note = re.sub(r"^\S+\s*[:：\-–]?\s*", "", t, count=1)
        return "rejected", "", note
    if any(low.startswith(w) for w in APPROVE_WORDS):
        return "approved", num.group(1) if num else "", ""
    if re.fullmatch(r"\d{1,2}", t):
        return "approved", t, ""
    return None


# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------
class Telegram:
    def __init__(self) -> None:
        self.enabled = bool(settings.telegram_token and settings.telegram_chat)
        self.base = f"https://api.telegram.org/bot{settings.telegram_token}"
        self.offset = 0

    def send(self, text: str) -> None:
        if not self.enabled:
            return
        for i in range(0, len(text), 3900):  # Telegram message length limit
            try:
                requests.post(f"{self.base}/sendMessage", timeout=30,
                              data={"chat_id": settings.telegram_chat, "text": text[i:i + 3900]})
            except requests.RequestException as e:
                log.warning("Telegram sendMessage failed: %s", e)

    def send_file(self, path: str | Path, caption: str = "") -> None:
        if not self.enabled:
            return
        p = Path(path)
        if not p.exists():
            return
        size_mb = p.stat().st_size / 1e6
        if size_mb > 49:  # The Bot API upload limit is 50 MB
            self.send(f"📁 الملف كبير ({size_mb:.0f}MB) ولا يمكن إرساله عبر تيليجرام. مساره على الخادم:\n{p}")
            return
        method, field = ("sendPhoto", "photo") if p.suffix.lower() in {".jpg", ".jpeg", ".png"} else (
            ("sendVideo", "video") if p.suffix.lower() == ".mp4" else ("sendDocument", "document"))
        try:
            with open(p, "rb") as f:
                requests.post(f"{self.base}/{method}", timeout=600,
                              data={"chat_id": settings.telegram_chat, "caption": caption[:1000]},
                              files={field: f})
        except requests.RequestException as e:
            log.warning("Telegram %s failed: %s", method, e)

    def poll(self) -> list[str]:
        """Returns new text messages from the owner only (other chats are ignored)."""
        if not self.enabled:
            return []
        try:
            r = requests.get(f"{self.base}/getUpdates", params={"offset": self.offset, "timeout": 0}, timeout=30)
            updates = r.json().get("result", [])
        except (requests.RequestException, ValueError) as e:
            log.warning("Telegram getUpdates failed: %s", e)
            return []
        msgs = []
        for u in updates:
            self.offset = max(self.offset, u["update_id"] + 1)
            m = u.get("message") or {}
            if str(m.get("chat", {}).get("id")) == str(settings.telegram_chat) and m.get("text"):
                msgs.append(m["text"])
        return msgs


# ---------------------------------------------------------------------------
# Owner command inbox from the CLI (python -m factory command "...")
# ---------------------------------------------------------------------------
def push_command(text: str) -> Path:
    INBOX.mkdir(parents=True, exist_ok=True)
    p = INBOX / f"{datetime.now():%Y%m%d%H%M%S}_{uuid.uuid4().hex[:6]}.json"
    p.write_text(json.dumps({"text": text}, ensure_ascii=False), encoding="utf-8")
    return p


def pop_commands() -> list[str]:
    if not INBOX.exists():
        return []
    out = []
    for p in sorted(INBOX.glob("*.json")):
        try:
            out.append(json.loads(p.read_text(encoding="utf-8"))["text"])
        finally:
            p.unlink(missing_ok=True)
    return out


# ---------------------------------------------------------------------------
# The approval desk
# ---------------------------------------------------------------------------
class ApprovalDesk:
    def __init__(self, telegram: Telegram):
        self.tg = telegram
        self.pending: str | None = None  # the stage currently awaiting the owner's decision

    def ask(self, job: Job, stage: str, text: str, files: list[str] | None = None) -> None:
        clear_decision(job, stage)
        self.pending = stage
        job.set_stage(stage, approval="pending", asked_at=settings.now().strftime("%H:%M"))
        job.event("approval", f"طلب موافقة المالك على: {stage}")
        how = (f"\n\n↩️ للرد: «موافق» أو «رفض: ملاحظاتك»"
               f"\n(أو من الطرفية: python -m factory approve {stage} [رقم] / python -m factory reject {stage} \"ملاحظات\")")
        msg = text + how
        print("\n" + "=" * 70 + "\n" + msg + "\n" + "=" * 70 + "\n", flush=True)
        self.tg.send(msg)
        for f in files or []:
            self.tg.send_file(f)

    def handle_owner_message(self, job: Job, text: str) -> bool:
        """If a message is a reply to a pending approval, record it and return True."""
        if not self.pending:
            return False
        parsed = parse_reply(text)
        if not parsed:
            return False
        status, value, note = parsed
        record_decision(job, self.pending, status, value, note, by="telegram")
        self.tg.send(f"✔️ تم تسجيل قرارك على «{self.pending}»: {'موافقة' if status == 'approved' else 'رفض/تعديل'}")
        return True

    def check(self, job: Job, stage: str) -> dict | None:
        d = read_decision(job, stage)
        if d:
            self.pending = None
            job.set_stage(stage, approval=d["status"])
        return d

    def wait(self, job: Job, stage: str, until: datetime, on_tick=None) -> dict:
        """Waits for the owner's decision until the given time. on_tick runs every poll cycle (for inbound messages)."""
        while settings.now() < until:
            if on_tick:
                on_tick()
            d = self.check(job, stage)
            if d:
                return d
            time.sleep(0.5 if settings.dry_run else 5)
        self.pending = None
        job.set_stage(stage, approval="timeout")
        return {"status": "timeout", "value": "", "note": ""}

"""Control the factory from your phone (or any device) through a Telegram bot.

Commands:
  /video <موضوع>   make a video about a topic
  /auto [n]         let the factory pick n topics itself (default 1)
  /status           what is being built now
  /id               shows your chat id (put it in allowed_chat_ids)
"""
import threading
import time

import requests

from . import settings as cfg
from .pipeline import get_factory

HELP = ("🏭 مصنع الفيديوهات\n"
        "/video موضوع الفيديو — اعمل فيديو عن موضوع\n"
        "/auto 3 — المصنع يختار 3 مواضيع بنفسه\n"
        "/status — حالة الشغل\n/id — رقم المحادثة")


class Bot:
    def __init__(self):
        self.offset = 0
        self.stop = threading.Event()
        self.waiting = {}  # job id -> chat id
        get_factory().listeners.append(self._on_done)

    def _api(self, method, **data):
        token = cfg.load()["control"]["telegram_bot_token"]
        r = requests.post(f"https://api.telegram.org/bot{token}/{method}", data=data, timeout=70)
        r.raise_for_status()
        return r.json().get("result")

    def say(self, chat, text):
        try:
            self._api("sendMessage", chat_id=chat, text=text[:4000])
        except Exception:
            pass

    def _allowed(self, chat):
        allowed = [x.strip() for x in cfg.load()["control"].get("allowed_chat_ids", "").split(",") if x.strip()]
        return not allowed or str(chat) in allowed

    def _on_done(self, job):
        chat = self.waiting.pop(job["id"], None)
        if not chat:
            return
        if job["status"] == "done":
            lines = [f"{'✅' if r['ok'] else '⚠️'} {r['connector']}: {r['msg']}" for r in job.get("publish", [])]
            self.say(chat, "🎬 الفيديو جاهز!\n" + (job["steps"]["seo_publisher"].get("output") or {}).get("title", "") + "\n\n" + "\n".join(lines))
        else:
            self.say(chat, f"❌ الفيديو وقف: {job.get('error')}\nتقدر تكمله من لوحة التحكم (زرار استكمال).")

    def handle(self, msg):
        chat = msg["chat"]["id"]
        text = (msg.get("text") or "").strip()
        if text.startswith("/id"):
            return self.say(chat, f"Chat ID: {chat}")
        if not self._allowed(chat):
            return self.say(chat, "غير مسموح. ضيف رقم المحادثة في الإعدادات ← التحكم.")
        f = get_factory()
        if text.startswith("/video"):
            topic = text[len("/video"):].strip()
            if not topic:
                return self.say(chat, "اكتب الموضوع بعد الأمر: /video ليه السيارات في إنجلترا على الشمال؟")
            jid = f.submit(topic)
            self.waiting[jid] = chat
            return self.say(chat, f"👷 15 عامل بدأوا على: {topic}")
        if text.startswith("/auto"):
            parts = text.split()
            n = min(int(parts[1]), 10) if len(parts) > 1 and parts[1].isdigit() else 1
            for _ in range(n):
                self.waiting[f.submit(None)] = chat
            return self.say(chat, f"👷 المصنع هيختار {n} موضوع ويبدأ.")
        if text.startswith("/status"):
            active = [j for j in f.list() if j["status"] in ("running", "queued")]
            if not active:
                return self.say(chat, "مفيش شغل دلوقتي.")
            return self.say(chat, "\n".join(f"• {j.get('topic') or 'موضوع تلقائي'} — {j['status']} — العامل: {j.get('current') or '-'}" for j in active))
        return self.say(chat, HELP)

    def loop(self):
        while not self.stop.is_set():
            if not cfg.load()["control"].get("telegram_bot_token"):
                time.sleep(10)
                continue
            try:
                updates = self._api("getUpdates", offset=self.offset, timeout=50) or []
                for u in updates:
                    self.offset = u["update_id"] + 1
                    if "message" in u:
                        self.handle(u["message"])
            except Exception:
                time.sleep(5)


def start_in_background():
    bot = Bot()
    threading.Thread(target=bot.loop, daemon=True, name="telegram-bot").start()
    return bot

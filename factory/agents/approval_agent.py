"""Approval Agent — sends "Task complete" + preview + QA report + buttons, then the
video WAITS in PENDING_APPROVAL. This agent can never approve anything itself."""
from __future__ import annotations

from ..telegram import Telegram, btn
from .base import BaseAgent


def decision_buttons(vid: str) -> list[list[dict]]:
    return [[btn("✅ Publish", f"ap:{vid}"), btn("✏️ Revise", f"rv:{vid}"), btn("❌ Reject", f"rj:{vid}")]]


class ApprovalAgent(BaseAgent):
    name = "approval"

    def run(self) -> dict:
        v = self.ctx.store.video(self.ctx.video_id)
        script = self.p.read_json("script", "script.json")
        qa = self.p.read_json("logs", "qa_report.json", default={})
        info = (v["meta"] or {}).get("export_info", {})
        rev = v.get("revision", 0)
        fmt = v["fmt"]
        platforms = self.s.get(f"platforms.default_for_{fmt.replace(':', '_')}", [])
        warnings = [i["reason"] for st in qa.values() for i in st.get("issues", []) if i["severity"] == "warning"]

        text = (
            f"✅ Task complete: {script['title']}" + (f"  (revision {rev})" if rev else "") + "\n\n"
            f"⏱ {info.get('duration', 0):.1f}s · 📐 {info.get('width')}x{info.get('height')} @ {info.get('fps')}fps"
            f" · 🔊 {info.get('lufs')} LUFS\n"
            f"📱 Suggested platform: {script.get('suggested_platform', '-')}  (defaults: {', '.join(platforms)})\n\n"
            f"📝 Title: {script['title']}\n"
            f"📄 Description: {script.get('description', '')}\n"
            f"#️⃣ {' '.join(script.get('hashtags', []))}\n\n"
            f"🧪 QA: " + ("PASS" if all(s.get("passed") for s in qa.values()) else "issues") +
            (f" · warnings: {'; '.join(warnings)[:600]}" if warnings else "") + "\n"
            f"🎬 CapCut draft: {v['meta'].get('draft_name')}\n"
            f"🆔 {self.ctx.video_id}\n\n"
            f"Status: PENDING_APPROVAL — nothing is published until you press ✅."
        )
        self.p.write_json("logs", "approval_request.json", {"text": text, "video_id": self.ctx.video_id})

        tg = Telegram(self.s.env("TELEGRAM_BOT_TOKEN"), self.s.env("TELEGRAM_OWNER_ID"))
        if tg.enabled:
            if self.p.thumb_file.exists():
                tg.send_photo(self.p.thumb_file, caption=f"🖼 {script['title']}")
            tg.send_video(self.p.preview_file, caption=f"▶️ Preview: {script['title']}", thumb=self.p.thumb_file)
            tg.send(text, decision_buttons(self.ctx.video_id))
            self.info("approval request sent to Telegram")
        else:
            self.warn("Telegram not configured — decide from the terminal: "
                      f"python main.py decide {self.ctx.video_id} publish|revise|reject")
        print("\n" + text + "\n")
        return {"sent": tg.enabled}

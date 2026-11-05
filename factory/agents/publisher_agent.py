"""Publisher Agent — runs ONLY after the owner's ✅ approval.

`assert_owner_approval()` is the single gate every publish goes through. It requires:
  1. the latest decision for this video is APPROVE,
  2. it was made by the configured owner (Telegram id, or 'cli-owner' at your own terminal),
  3. the approved render hash equals the file being published (a revision invalidates approval).
There is no flag, config value, or code path that skips this check.
"""
from __future__ import annotations

from pathlib import Path

from .. import media
from ..telegram import Telegram
from .base import BaseAgent


class NotApproved(PermissionError):
    pass


def assert_owner_approval(store, settings, video_id: str, final_file: Path) -> dict:
    appr = store.latest_approval(video_id)
    owner = str(settings.env("TELEGRAM_OWNER_ID"))
    if not appr or appr["decision"] != "APPROVE":
        raise NotApproved(f"{video_id}: no owner approval — publishing refused")
    if appr["decided_by"] not in {owner, "cli-owner"} or not appr["decided_by"]:
        raise NotApproved(f"{video_id}: approval not from the owner — publishing refused")
    if not final_file.exists() or media.sha256(final_file) != appr["render_sha256"]:
        raise NotApproved(f"{video_id}: file changed after approval — re-approval required")
    return appr


class PublisherAgent(BaseAgent):
    name = "publisher"

    def run(self) -> dict:
        appr = assert_owner_approval(self.ctx.store, self.s, self.ctx.video_id, self.p.final_file)
        self.ctx.store.set_video_status(self.ctx.video_id, "PUBLISHING")
        script = self.p.read_json("script", "script.json")
        caption = f"{script['title']}\n\n{script.get('description', '')}\n\n{' '.join(script.get('hashtags', []))}"
        results = {}
        for platform in appr["platforms"]:
            try:
                if platform == "youtube" and Path(self.s.env("YOUTUBE_CLIENT_SECRETS", "client_secret.json")).exists():
                    results[platform] = self._youtube(script)
                else:
                    results[platform] = self._handoff(platform, caption)
            except Exception as e:
                results[platform] = f"FAILED: {e}"
                self.warn(f"{platform}: {e}")
        self.ctx.store.merge_meta(self.ctx.video_id, publish_results=results)
        self.ctx.store.set_video_status(self.ctx.video_id, "PUBLISHED")
        self.info(f"published: {results}")
        return results

    def _youtube(self, script: dict) -> str:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload

        scopes = ["https://www.googleapis.com/auth/youtube.upload"]
        token = self.s.root / "youtube_token.json"
        creds = Credentials.from_authorized_user_file(str(token), scopes) if token.exists() else None
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.s.env("YOUTUBE_CLIENT_SECRETS"), scopes)
                creds = flow.run_local_server(port=0)
            token.write_text(creds.to_json())
        yt = build("youtube", "v3", credentials=creds)
        body = {"snippet": {"title": script["title"][:100],
                            "description": script.get("description", "") + "\n\n" + " ".join(script.get("hashtags", [])),
                            "tags": [h.lstrip("#") for h in script.get("hashtags", [])]},
                "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}
        req = yt.videos().insert(part="snippet,status", body=body,
                                 media_body=MediaFileUpload(str(self.p.final_file), chunksize=-1, resumable=True))
        resp = None
        while resp is None:
            _, resp = req.next_chunk()
        return f"https://youtu.be/{resp['id']}"

    def _handoff(self, platform: str, caption: str) -> str:
        """TikTok / Instagram content-posting APIs need an approved developer app. Until you
        add one, the approved file + ready caption are sent to you for a 10-second manual post."""
        tg = Telegram(self.s.env("TELEGRAM_BOT_TOKEN"), self.s.env("TELEGRAM_OWNER_ID"))
        if tg.enabled:
            tg.send_document(self.p.final_file, caption=f"📤 Ready for {platform}:\n\n{caption}")
        return "handoff-sent" if tg.enabled else f"handoff: {self.p.final_file}"

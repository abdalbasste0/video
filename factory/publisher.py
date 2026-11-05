"""Publish to YouTube (called only by bot 9, and only after the owner's final approval).

Uses the YouTube Data API v3 directly with a refresh token (resumable upload, then thumbnail).
The refresh token is created once — see README.md under "YouTube setup".
"""
from __future__ import annotations

import json
from pathlib import Path

import requests

from .config import env, settings
from .log import log

TOKEN_URL = "https://oauth2.googleapis.com/token"
UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
THUMB_URL = "https://www.googleapis.com/upload/youtube/v3/thumbnails/set"


def _access_token() -> str:
    r = requests.post(TOKEN_URL, timeout=30, data={
        "client_id": settings.yt_client_id,
        "client_secret": settings.yt_client_secret,
        "refresh_token": settings.yt_refresh_token,
        "grant_type": "refresh_token",
    })
    r.raise_for_status()
    return r.json()["access_token"]


def publish_youtube(video: Path, thumbnail: Path | None, title: str, description: str, tags: list[str]) -> dict:
    if settings.dry_run:
        log.info("[dry-run] would have published to YouTube: %s", title)
        return {"platform": "youtube", "id": "DRY_RUN", "url": "https://youtube.com/watch?v=DRY_RUN"}
    if not (settings.yt_client_id and settings.yt_client_secret and settings.yt_refresh_token):
        raise RuntimeError("بيانات YouTube غير مضبوطة في .env")

    token = _access_token()
    meta = {
        "snippet": {
            "title": title[:100],
            "description": description[:4900],
            "tags": tags[:30],
            "categoryId": "24",  # Entertainment
            "defaultLanguage": settings.language,
            "defaultAudioLanguage": settings.language,
        },
        "status": {
            "privacyStatus": env("YOUTUBE_PRIVACY", "public"),
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": True,  # AI-generated voice, disclosed per YouTube policy
        },
    }
    size = video.stat().st_size
    init = requests.post(
        UPLOAD_URL, params={"uploadType": "resumable", "part": "snippet,status"}, timeout=60,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=UTF-8",
                 "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)},
        data=json.dumps(meta, ensure_ascii=False).encode("utf-8"),
    )
    init.raise_for_status()
    with open(video, "rb") as f:
        up = requests.put(init.headers["Location"], data=f, timeout=3600,
                          headers={"Authorization": f"Bearer {token}", "Content-Type": "video/mp4"})
    up.raise_for_status()
    vid = up.json()["id"]

    if thumbnail and thumbnail.exists():
        with open(thumbnail, "rb") as f:
            t = requests.post(THUMB_URL, params={"videoId": vid}, data=f, timeout=120,
                              headers={"Authorization": f"Bearer {token}", "Content-Type": "image/jpeg"})
        if t.status_code >= 300:
            log.warning("Thumbnail upload failed (the channel must be verified to set custom thumbnails): %s", t.text[:200])
    return {"platform": "youtube", "id": vid, "url": f"https://youtu.be/{vid}"}

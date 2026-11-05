"""YouTube Data API wrapper used by the Discord bot.

Every linked YouTube channel has its own OAuth token stored in
``tokens/<alias>.json``. All functions here are blocking; the bot calls
them through ``asyncio.to_thread`` so Discord stays responsive.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = [
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube.upload",
]

ALIAS_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")
VIDEO_ID_RE = re.compile(r"(?:v=|youtu\.be/|shorts/|embed/|live/)([A-Za-z0-9_-]{11})")


def extract_video_id(value: str) -> str:
    """Accept a bare video id or any common YouTube URL."""
    value = value.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        return value
    match = VIDEO_ID_RE.search(value)
    if not match:
        raise ValueError(f"لم أتعرف على معرف الفيديو: {value}")
    return match.group(1)


@dataclass
class VideoInfo:
    id: str
    title: str
    privacy: str
    published_at: str
    views: int
    likes: int
    comments: int

    @property
    def url(self) -> str:
        return f"https://youtu.be/{self.id}"


class ChannelStore:
    """Loads and refreshes OAuth credentials for each linked channel."""

    def __init__(self, tokens_dir: Path):
        self.tokens_dir = tokens_dir
        self.tokens_dir.mkdir(parents=True, exist_ok=True)
        self._services: dict[str, object] = {}

    def aliases(self) -> list[str]:
        return sorted(p.stem for p in self.tokens_dir.glob("*.json"))

    def token_path(self, alias: str) -> Path:
        if not ALIAS_RE.match(alias):
            raise ValueError("اسم القناة يجب أن يكون حروفاً إنجليزية/أرقام/-/_ فقط")
        return self.tokens_dir / f"{alias}.json"

    def save(self, alias: str, creds: Credentials) -> None:
        self.token_path(alias).write_text(creds.to_json(), encoding="utf-8")
        self._services.pop(alias, None)

    def service(self, alias: str):
        path = self.token_path(alias)
        if not path.exists():
            raise KeyError(f"القناة '{alias}' غير مربوطة. شغّل: python auth.py {alias}")
        creds = Credentials.from_authorized_user_info(
            json.loads(path.read_text(encoding="utf-8")), SCOPES
        )
        if not creds.valid:
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                self.save(alias, creds)
            else:
                raise PermissionError(
                    f"صلاحية القناة '{alias}' انتهت. أعد الربط: python auth.py {alias}"
                )
        # Rebuild when the token was refreshed so the service uses fresh creds.
        cached = self._services.get(alias)
        if cached is None or cached[0] != creds.token:
            self._services[alias] = (
                creds.token,
                build("youtube", "v3", credentials=creds, cache_discovery=False),
            )
        return self._services[alias][1]


# ---------------------------------------------------------------- channel ---

def channel_stats(yt) -> dict:
    res = yt.channels().list(part="snippet,statistics,contentDetails", mine=True).execute()
    if not res.get("items"):
        raise RuntimeError("لا توجد قناة يوتيوب على هذا الحساب")
    item = res["items"][0]
    stats = item["statistics"]
    return {
        "id": item["id"],
        "title": item["snippet"]["title"],
        "thumbnail": item["snippet"]["thumbnails"].get("default", {}).get("url"),
        "subscribers": int(stats.get("subscriberCount", 0)),
        "hidden_subs": stats.get("hiddenSubscriberCount", False),
        "views": int(stats.get("viewCount", 0)),
        "videos": int(stats.get("videoCount", 0)),
        "uploads_playlist": item["contentDetails"]["relatedPlaylists"]["uploads"],
    }


def recent_videos(yt, count: int = 5) -> list[VideoInfo]:
    uploads = channel_stats(yt)["uploads_playlist"]
    res = yt.playlistItems().list(
        part="contentDetails", playlistId=uploads, maxResults=min(count, 50)
    ).execute()
    ids = [i["contentDetails"]["videoId"] for i in res.get("items", [])]
    return get_videos(yt, ids)


def get_videos(yt, ids: list[str]) -> list[VideoInfo]:
    if not ids:
        return []
    res = yt.videos().list(part="snippet,statistics,status", id=",".join(ids)).execute()
    out = []
    for v in res.get("items", []):
        s = v.get("statistics", {})
        out.append(
            VideoInfo(
                id=v["id"],
                title=v["snippet"]["title"],
                privacy=v["status"]["privacyStatus"],
                published_at=v["status"].get("publishAt") or v["snippet"]["publishedAt"],
                views=int(s.get("viewCount", 0)),
                likes=int(s.get("likeCount", 0)),
                comments=int(s.get("commentCount", 0)),
            )
        )
    return out


# ----------------------------------------------------------------- videos ---

def upload_video(
    yt,
    file_path: Path,
    title: str,
    description: str = "",
    tags: Optional[list[str]] = None,
    privacy: str = "private",
    publish_at: Optional[datetime] = None,
    category_id: str = "22",
    made_for_kids: bool = False,
    on_progress: Optional[Callable[[float], None]] = None,
) -> str:
    status: dict = {"privacyStatus": privacy, "selfDeclaredMadeForKids": made_for_kids}
    if publish_at is not None:
        # YouTube only schedules private videos.
        status["privacyStatus"] = "private"
        status["publishAt"] = publish_at.astimezone(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags or [],
            "categoryId": category_id,
        },
        "status": status,
    }
    media = MediaFileUpload(str(file_path), chunksize=8 * 1024 * 1024, resumable=True)
    request = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        progress, response = request.next_chunk()
        if progress and on_progress:
            on_progress(progress.progress())
    return response["id"]


def update_video(
    yt,
    video_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[list[str]] = None,
) -> None:
    res = yt.videos().list(part="snippet", id=video_id).execute()
    if not res.get("items"):
        raise LookupError("الفيديو غير موجود في هذه القناة")
    snippet = res["items"][0]["snippet"]
    if title is not None:
        snippet["title"] = title[:100]
    if description is not None:
        snippet["description"] = description[:5000]
    if tags is not None:
        snippet["tags"] = tags
    body = {
        "id": video_id,
        "snippet": {
            "title": snippet["title"],
            "description": snippet.get("description", ""),
            "tags": snippet.get("tags", []),
            "categoryId": snippet["categoryId"],
        },
    }
    yt.videos().update(part="snippet", body=body).execute()


def set_privacy(
    yt, video_id: str, privacy: str, publish_at: Optional[datetime] = None
) -> None:
    res = yt.videos().list(part="status", id=video_id).execute()
    if not res.get("items"):
        raise LookupError("الفيديو غير موجود في هذه القناة")
    status = res["items"][0]["status"]
    new_status = {
        "privacyStatus": privacy,
        "selfDeclaredMadeForKids": status.get("selfDeclaredMadeForKids", False),
    }
    if publish_at is not None:
        new_status["privacyStatus"] = "private"
        new_status["publishAt"] = publish_at.astimezone(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    yt.videos().update(part="status", body={"id": video_id, "status": new_status}).execute()


def set_thumbnail(yt, video_id: str, image_path: Path) -> None:
    yt.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(str(image_path))).execute()


def delete_video(yt, video_id: str) -> None:
    yt.videos().delete(id=video_id).execute()


# --------------------------------------------------------------- comments ---

def list_comments(yt, video_id: str, count: int = 10) -> list[dict]:
    res = yt.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=min(count, 100),
        order="time",
        textFormat="plainText",
    ).execute()
    out = []
    for t in res.get("items", []):
        c = t["snippet"]["topLevelComment"]
        s = c["snippet"]
        out.append(
            {
                "id": c["id"],
                "author": s["authorDisplayName"],
                "text": s["textDisplay"],
                "likes": s.get("likeCount", 0),
                "replies": t["snippet"].get("totalReplyCount", 0),
            }
        )
    return out


def reply_comment(yt, comment_id: str, text: str) -> str:
    res = yt.comments().insert(
        part="snippet", body={"snippet": {"parentId": comment_id, "textOriginal": text}}
    ).execute()
    return res["id"]

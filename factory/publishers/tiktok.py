"""Publish to TikTok via the Content Posting API (Direct Post).

Steps: refresh the token → query the account's allowed privacy settings → init the upload →
upload the file in chunks → poll the publish status.

Important: until TikTok approves your app (app audit), the API only allows posting as private (SELF_ONLY).
After approval, set TIKTOK_PRIVACY=PUBLIC_TO_EVERYONE.
"""
from __future__ import annotations

import time

import requests

from ..config import env, settings
from ..log import log

API = "https://open.tiktokapis.com/v2"
CHUNK = 10 * 1024 * 1024  # 10MB (TikTok requires 5–64MB per chunk)


def configured() -> bool:
    return bool(env("TIKTOK_CLIENT_KEY") and env("TIKTOK_CLIENT_SECRET") and env("TIKTOK_REFRESH_TOKEN"))


def _token() -> str:
    r = requests.post(f"{API}/oauth/token/", timeout=30, headers={"Content-Type": "application/x-www-form-urlencoded"},
                      data={"client_key": env("TIKTOK_CLIENT_KEY"), "client_secret": env("TIKTOK_CLIENT_SECRET"),
                            "grant_type": "refresh_token", "refresh_token": env("TIKTOK_REFRESH_TOKEN")})
    r.raise_for_status()
    data = r.json()
    if "access_token" not in data:
        raise RuntimeError(f"TikTok token: {data}")
    return data["access_token"]


def _post(token: str, path: str, body: dict) -> dict:
    r = requests.post(f"{API}{path}", json=body, timeout=60,
                      headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=UTF-8"})
    data = r.json()
    if r.status_code >= 300 or data.get("error", {}).get("code", "ok") != "ok":
        raise RuntimeError(f"TikTok {path}: {data.get('error', data)}")
    return data["data"]


def publish(post) -> dict:
    video = post.vertical_video or post.video
    if settings.dry_run:
        log.info("[dry-run] would have published to TikTok: %s", post.title)
        return {"platform": "tiktok", "id": "DRY_RUN", "url": "https://tiktok.com/@me/video/DRY_RUN"}
    if not configured():
        raise RuntimeError("بيانات TikTok غير مضبوطة في .env")

    token = _token()
    creator = _post(token, "/post/publish/creator_info/query/", {})
    wanted = env("TIKTOK_PRIVACY", "SELF_ONLY")
    options = creator.get("privacy_level_options", [])
    privacy = wanted if wanted in options else ("SELF_ONLY" if "SELF_ONLY" in options else options[0])
    if privacy != wanted:
        log.warning("TikTok: privacy setting %s is not available for this account, using %s", wanted, privacy)

    size = video.stat().st_size
    chunk = size if size <= 64 * 1024 * 1024 else CHUNK
    count = 1 if chunk == size else size // chunk  # TikTok appends the remainder to the last chunk
    caption = f"{post.title}\n\n" + " ".join("#" + t.replace(" ", "") for t in post.tags[:6])
    init = _post(token, "/post/publish/video/init/", {
        "post_info": {
            "title": caption[:2200],
            "privacy_level": privacy,
            "disable_duet": False, "disable_comment": False, "disable_stitch": False,
            "is_aigc": True,  # disclose AI-generated content (voice and images)
        },
        "source_info": {"source": "FILE_UPLOAD", "video_size": size, "chunk_size": chunk, "total_chunk_count": count},
    })
    upload_url, publish_id = init["upload_url"], init["publish_id"]

    with open(video, "rb") as f:
        for i in range(count):
            start = i * chunk
            end = size - 1 if i == count - 1 else start + chunk - 1
            f.seek(start)
            body = f.read(end - start + 1)
            r = requests.put(upload_url, data=body, timeout=600, headers={
                "Content-Type": "video/mp4", "Content-Length": str(len(body)),
                "Content-Range": f"bytes {start}-{end}/{size}"})
            if r.status_code not in (200, 201, 206):
                raise RuntimeError(f"TikTok upload chunk {i + 1}/{count}: {r.status_code} {r.text[:200]}")

    for _ in range(60):  # up to ~5 minutes
        st = _post(token, "/post/publish/status/fetch/", {"publish_id": publish_id})
        status = st.get("status")
        if status == "PUBLISH_COMPLETE":
            ids = st.get("publicaly_available_post_id") or st.get("publicly_available_post_id") or []
            url = f"https://www.tiktok.com/@me/video/{ids[0]}" if ids else "(منشور خاص — راجعه في تطبيق تيك توك)"
            return {"platform": "tiktok", "id": str(ids[0]) if ids else publish_id, "url": url, "privacy": privacy}
        if status == "FAILED":
            raise RuntimeError(f"TikTok publish failed: {st.get('fail_reason')}")
        time.sleep(5)
    return {"platform": "tiktok", "id": publish_id, "url": "(قيد المعالجة لدى تيك توك)", "privacy": privacy}


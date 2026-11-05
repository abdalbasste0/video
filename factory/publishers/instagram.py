"""Publish a Reel to Instagram via the Instagram Graph API (needs a Business or Creator account).

Uses resumable upload so the video doesn't need to be hosted at a public URL:
 1. create a REELS container with upload_type=resumable
 2. upload the file to rupload.facebook.com
 3. wait for processing (status_code=FINISHED)
 4. media_publish
Required: IG_USER_ID (the Instagram account ID) and IG_ACCESS_TOKEN (a long-lived token).
"""
from __future__ import annotations

import time

import requests

from ..config import env, settings
from ..log import log


def _ver() -> str:
    return env("IG_GRAPH_VERSION", "v21.0")


def configured() -> bool:
    return bool(env("IG_USER_ID") and env("IG_ACCESS_TOKEN"))


def publish(post) -> dict:
    video = post.vertical_video or post.video
    if settings.dry_run:
        log.info("[dry-run] would have published to Instagram: %s", post.title)
        return {"platform": "instagram", "id": "DRY_RUN", "url": "https://instagram.com/reel/DRY_RUN"}
    if not configured():
        raise RuntimeError("بيانات Instagram غير مضبوطة في .env")

    user, token = env("IG_USER_ID"), env("IG_ACCESS_TOKEN")
    graph = f"https://graph.facebook.com/{_ver()}"
    caption = f"{post.title}\n\n{post.description}"[:2200]

    r = requests.post(f"{graph}/{user}/media", timeout=60, data={
        "media_type": "REELS", "upload_type": "resumable", "caption": caption,
        "share_to_feed": "true", "access_token": token})
    data = r.json()
    if "id" not in data:
        raise RuntimeError(f"Instagram container: {data.get('error', data)}")
    container = data["id"]

    size = video.stat().st_size
    with open(video, "rb") as f:
        up = requests.post(f"https://rupload.facebook.com/ig-api-upload/{_ver()}/{container}", data=f, timeout=1800,
                           headers={"Authorization": f"OAuth {token}", "offset": "0", "file_size": str(size)})
    if up.status_code >= 300:
        raise RuntimeError(f"Instagram upload: {up.status_code} {up.text[:300]}")

    for _ in range(90):  # up to ~7.5 minutes for processing
        st = requests.get(f"{graph}/{container}", timeout=30,
                          params={"fields": "status_code,status", "access_token": token}).json()
        code = st.get("status_code")
        if code == "FINISHED":
            break
        if code in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram processing: {st}")
        time.sleep(5)
    else:
        raise RuntimeError("Instagram: processing took too long")

    pub = requests.post(f"{graph}/{user}/media_publish", timeout=60,
                        data={"creation_id": container, "access_token": token}).json()
    if "id" not in pub:
        raise RuntimeError(f"Instagram publish: {pub.get('error', pub)}")
    link = requests.get(f"{graph}/{pub['id']}", timeout=30,
                        params={"fields": "permalink", "access_token": token}).json().get("permalink", "")
    return {"platform": "instagram", "id": pub["id"], "url": link or "https://instagram.com"}

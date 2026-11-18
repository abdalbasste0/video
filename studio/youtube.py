"""Upload to YouTube with the official Data API v3 (no third-party service).

One-time setup (5 minutes, free):
  1. console.cloud.google.com -> new project -> enable "YouTube Data API v3".
  2. OAuth consent screen: External, add your Gmail as a Test user.
  3. Credentials -> Create OAuth client ID -> type "TVs and Limited Input devices".
  4. Put the client id/secret in env vars YT_CLIENT_ID / YT_CLIENT_SECRET
     (or secrets/client.json: {"client_id": "...", "client_secret": "..."}).
  5. python -m studio.youtube auth   -> open the link on your phone, type the code.

Then:
  python -m studio.youtube upload output/001-zero-viewers --publish-at 2026-11-20T17:00:00Z
Videos are uploaded as private and scheduled (publishAt), so you can review
them in YouTube Studio before they go public.
"""
import argparse
import json
import os
import sys
import time

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRETS = os.path.join(ROOT, "secrets")
TOKEN = os.path.join(SECRETS, "youtube_token.json")
SCOPE = "https://www.googleapis.com/auth/youtube"


def client():
    cid, sec = os.environ.get("YT_CLIENT_ID"), os.environ.get("YT_CLIENT_SECRET")
    if not cid:
        d = json.load(open(os.path.join(SECRETS, "client.json")))
        cid, sec = d["client_id"], d["client_secret"]
    return cid, sec


def auth():
    cid, sec = client()
    r = requests.post("https://oauth2.googleapis.com/device/code", data={"client_id": cid, "scope": SCOPE}).json()
    print(f"\nOpen {r['verification_url']} and enter the code:  {r['user_code']}\n")
    while True:
        time.sleep(r.get("interval", 5))
        t = requests.post("https://oauth2.googleapis.com/token", data={
            "client_id": cid, "client_secret": sec, "device_code": r["device_code"],
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code"}).json()
        if "access_token" in t:
            os.makedirs(SECRETS, exist_ok=True)
            json.dump(t, open(TOKEN, "w"))
            print("Authorized. Refresh token saved to secrets/ (git-ignored).")
            return
        if t.get("error") not in ("authorization_pending", "slow_down"):
            sys.exit(f"auth failed: {t}")


def access_token():
    cid, sec = client()
    rt = os.environ.get("YT_REFRESH_TOKEN") or json.load(open(TOKEN))["refresh_token"]
    t = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": cid, "client_secret": sec, "refresh_token": rt, "grant_type": "refresh_token"}).json()
    return t["access_token"]


def upload(folder, publish_at=None, short=False):
    meta = json.load(open(os.path.join(folder, "metadata.json")))
    video = os.path.join(folder, "short.mp4" if short else "video.mp4")
    tok = access_token()
    title = meta["title"]
    desc = meta.get("description", "")
    if short:
        title = (title.split("|")[0].strip() + " #shorts")[:100]
    status = {"privacyStatus": "private", "selfDeclaredMadeForKids": False}
    if publish_at:
        status["publishAt"] = publish_at
    body = {"snippet": {"title": title[:100], "description": desc, "tags": meta.get("tags", []),
                        "categoryId": "1"},  # Film & Animation
            "status": status}
    size = os.path.getsize(video)
    init = requests.post(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json",
                 "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)},
        data=json.dumps(body))
    init.raise_for_status()
    with open(video, "rb") as f:
        r = requests.put(init.headers["Location"], data=f,
                         headers={"Authorization": f"Bearer {tok}", "Content-Type": "video/mp4"})
    r.raise_for_status()
    vid = r.json()["id"]
    print("uploaded:", f"https://youtu.be/{vid}")
    thumb = os.path.join(folder, "thumbnail.png")
    if not short and os.path.exists(thumb):
        with open(thumb, "rb") as f:
            t = requests.post(f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}",
                              headers={"Authorization": f"Bearer {tok}", "Content-Type": "image/png"}, data=f)
        print("thumbnail:", "ok" if t.ok else t.text[:200])
    log = os.path.join(ROOT, "schedule", "uploads.jsonl")
    os.makedirs(os.path.dirname(log), exist_ok=True)
    with open(log, "a") as f:
        f.write(json.dumps({"folder": folder, "id": vid, "short": short, "publish_at": publish_at}) + "\n")
    return vid


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["auth", "upload"])
    ap.add_argument("folder", nargs="?")
    ap.add_argument("--publish-at", help="RFC3339 UTC time, e.g. 2026-11-20T17:00:00Z")
    ap.add_argument("--short", action="store_true")
    a = ap.parse_args()
    auth() if a.cmd == "auth" else upload(a.folder, a.publish_at, a.short)

"""Where finished videos go. Add, remove or switch connectors from the dashboard (tab: الربط).

Every connector type declares its fields, so the dashboard builds its form automatically.
To add a new platform: write a `publish(cfg, pkg)` function and register it in TYPES.

pkg = {video, short, thumbnail, srt, title, description, tags, short_title, pinned_comment, job_id, job_dir}
"""
import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path

import requests

from .settings import ROOT

T = 120


def _f(key, label, kind="text", help=""):
    return {"key": key, "label": label, "type": kind, "help": help}


def _caption(pkg, limit=1000):
    return f"🎬 {pkg['title']}\n\n{pkg['description']}"[:limit]


def _size_mb(p):
    return os.path.getsize(p) / 1e6 if p and os.path.exists(p) else 0


# ------------------------------------------------------------------ on the computer
def local_folder(cfg, pkg):
    dest = Path(cfg.get("path") or "output/ready")
    dest = dest if dest.is_absolute() else ROOT / dest
    dest = dest / pkg["job_id"]
    dest.mkdir(parents=True, exist_ok=True)
    for k in ("video", "short", "thumbnail", "srt"):
        if pkg.get(k) and os.path.exists(pkg[k]):
            shutil.copy2(pkg[k], dest / Path(pkg[k]).name)
    (dest / "metadata.txt").write_text(
        f"{pkg['title']}\n\n{pkg['description']}\n\nTAGS: {', '.join(pkg['tags'])}\n\n"
        f"تعليق مثبت: {pkg['pinned_comment']}\nعنوان الشورتس: {pkg['short_title']}\n", encoding="utf-8")
    return f"اتنسخ في {dest}"


def command(cfg, pkg):
    """Run any program on this computer: rclone to Drive, adb push to an Android phone, a Dropbox folder copy..."""
    values = {k: shlex.quote(str(pkg.get(k) or "")) for k in ("video", "short", "thumbnail", "srt", "title", "job_id", "job_dir")}
    cmd = cfg["command"].format(**values)
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=3600)
    if p.returncode:
        raise RuntimeError(p.stderr[-800:] or f"exit {p.returncode}")
    return (p.stdout or "تم").strip()[-300:]


# ------------------------------------------------------------------ automation hubs (connect anything)
def webhook(cfg, pkg):
    meta = {k: v for k, v in pkg.items() if k not in ("job_dir",)}
    headers = {}
    if cfg.get("auth_header"):
        n, _, v = cfg["auth_header"].partition(":")
        headers[n.strip()] = v.strip()
    if cfg.get("send_file") and pkg.get("video"):
        which = pkg["short"] if cfg.get("send_short_instead") and pkg.get("short") else pkg["video"]
        with open(which, "rb") as fh:
            r = requests.post(cfg["url"], data={"meta": json.dumps(meta, ensure_ascii=False)},
                              files={"video": (Path(which).name, fh, "video/mp4")}, headers=headers, timeout=900)
    else:
        r = requests.post(cfg["url"], json=meta, headers=headers, timeout=T)
    r.raise_for_status()
    return f"HTTP {r.status_code}"


# ------------------------------------------------------------------ phone / chat apps
def telegram(cfg, pkg):
    base = f"https://api.telegram.org/bot{cfg['bot_token']}"
    chat = cfg["chat_id"]
    if pkg.get("thumbnail"):
        with open(pkg["thumbnail"], "rb") as fh:
            requests.post(f"{base}/sendPhoto", data={"chat_id": chat, "caption": pkg["title"][:1000]},
                          files={"photo": fh}, timeout=T).raise_for_status()
    sent = []
    for key in ("short", "video") if cfg.get("send_video", True) else ():
        p = pkg.get(key)
        if p and _size_mb(p) < 49:
            with open(p, "rb") as fh:
                requests.post(f"{base}/sendVideo", data={"chat_id": chat, "caption": (pkg["short_title"] if key == "short" else pkg["title"])[:1000],
                                                       "supports_streaming": "true"}, files={"video": fh}, timeout=900).raise_for_status()
            sent.append(key)
    requests.post(f"{base}/sendMessage", data={"chat_id": chat, "text": _caption(pkg, 4000) + (
        "" if "video" in sent else f"\n\n📁 الفيديو الكامل أكبر من 50MB، موجود على الحاسوب:\n{pkg.get('video')}")}, timeout=T).raise_for_status()
    return "اتبعت على تيليجرام"


def discord(cfg, pkg):
    files, opened = {}, []
    for key in ("thumbnail", "short"):
        p = pkg.get(key)
        if p and _size_mb(p) < 24:
            fh = open(p, "rb")
            opened.append(fh)
            files[key] = (Path(p).name, fh)
    try:
        r = requests.post(cfg["webhook_url"], data={"content": _caption(pkg, 1900)}, files=files or None, timeout=600)
    finally:
        for fh in opened:
            fh.close()
    r.raise_for_status()
    return "اتبعت على ديسكورد"


def slack(cfg, pkg):
    requests.post(cfg["webhook_url"], json={"text": _caption(pkg, 3000) + f"\n{pkg.get('video')}"}, timeout=T).raise_for_status()
    return "اتبعت على سلاك"


def ntfy(cfg, pkg):
    server = (cfg.get("server") or "https://ntfy.sh").rstrip("/")
    requests.post(f"{server}/{cfg['topic']}", data=f"{pkg['title']}\n{pkg.get('video')}".encode(),
                  headers={"Title": "Video ready", "Tags": "movie_camera"}, timeout=T).raise_for_status()
    return "إشعار على الموبايل"


def whatsapp_callmebot(cfg, pkg):
    r = requests.get("https://api.callmebot.com/whatsapp.php",
                     params={"phone": cfg["phone"], "apikey": cfg["apikey"], "text": f"🎬 {pkg['title']}\n{pkg.get('video')}"}, timeout=T)
    r.raise_for_status()
    return "رسالة واتساب"


# ------------------------------------------------------------------ video platforms
def _google_token(cfg):
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": cfg["client_id"], "client_secret": cfg["client_secret"],
        "refresh_token": cfg["refresh_token"], "grant_type": "refresh_token"}, timeout=T)
    r.raise_for_status()
    return r.json()["access_token"]


def _yt_upload(token, path, title, desc, tags, cfg):
    body = {"snippet": {"title": title[:100], "description": desc[:4900], "tags": tags[:30],
                        "categoryId": cfg.get("category_id") or "27", "defaultLanguage": "ar"},
            "status": {"privacyStatus": cfg.get("privacy") or "private", "selfDeclaredMadeForKids": False}}
    init = requests.post("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
                         headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=UTF-8",
                                  "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(os.path.getsize(path))},
                         data=json.dumps(body), timeout=T)
    init.raise_for_status()
    with open(path, "rb") as fh:
        up = requests.put(init.headers["Location"], data=fh, headers={"Authorization": f"Bearer {token}", "Content-Type": "video/mp4"}, timeout=7200)
    up.raise_for_status()
    return up.json()["id"]


def youtube(cfg, pkg):
    token = _google_token(cfg)
    vid = _yt_upload(token, pkg["video"], pkg["title"], pkg["description"], pkg["tags"], cfg)
    if pkg.get("thumbnail"):
        with open(pkg["thumbnail"], "rb") as fh:
            requests.post(f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}",
                          headers={"Authorization": f"Bearer {token}", "Content-Type": "image/jpeg"}, data=fh, timeout=T)
    msg = f"https://youtu.be/{vid}"
    if cfg.get("upload_short") and pkg.get("short"):
        sid = _yt_upload(token, pkg["short"], pkg["short_title"] + " #shorts", pkg["title"], pkg["tags"], cfg)
        msg += f" + https://youtube.com/shorts/{sid}"
    return msg


def facebook_page(cfg, pkg):
    ver = cfg.get("api_version") or "v21.0"
    path = pkg["short"] if cfg.get("post_short") and pkg.get("short") else pkg["video"]
    with open(path, "rb") as fh:
        r = requests.post(f"https://graph-video.facebook.com/{ver}/{cfg['page_id']}/videos",
                          data={"access_token": cfg["page_access_token"], "title": pkg["title"], "description": pkg["description"]},
                          files={"source": fh}, timeout=7200)
    r.raise_for_status()
    return f"Facebook video id {r.json().get('id')}"


def tiktok(cfg, pkg):
    path = pkg.get("short") or pkg["video"]
    size = os.path.getsize(path)
    if size > 64 * 1024 * 1024:
        raise RuntimeError("الملف أكبر من 64MB - استخدم الشورتس")
    h = {"Authorization": f"Bearer {cfg['access_token']}", "Content-Type": "application/json; charset=UTF-8"}
    init = requests.post("https://open.tiktokapis.com/v2/post/publish/video/init/", headers=h, json={
        "post_info": {"title": f"{pkg['short_title']} {' '.join('#' + t.lstrip('#') for t in pkg.get('hashtags', [])[:5])}"[:2200],
                      "privacy_level": cfg.get("privacy_level") or "SELF_ONLY"},
        "source_info": {"source": "FILE_UPLOAD", "video_size": size, "chunk_size": size, "total_chunk_count": 1}}, timeout=T)
    init.raise_for_status()
    data = init.json()["data"]
    with open(path, "rb") as fh:
        requests.put(data["upload_url"], data=fh, headers={"Content-Type": "video/mp4", "Content-Range": f"bytes 0-{size - 1}/{size}"},
                     timeout=3600).raise_for_status()
    return f"TikTok publish_id {data['publish_id']}"


TYPES = {
    "local_folder": {"label": "📁 مجلد على الحاسوب", "fn": local_folder, "fields": [
        _f("path", "مسار المجلد", help="مثال: D:/Videos/Ready أو output/ready")]},
    "command": {"label": "💻 أمر/برنامج على الحاسوب", "fn": command, "fields": [
        _f("command", "الأمر", "textarea", "متغيرات: {video} {short} {thumbnail} {title}. أمثلة: rclone copy {video} gdrive:Videos  |  adb push {short} /sdcard/Movies/")]},
    "webhook": {"label": "🔗 Webhook (n8n / Make / Zapier / أي تطبيق)", "fn": webhook, "fields": [
        _f("url", "رابط الويب هوك"), _f("auth_header", "هيدر توثيق (اختياري)", "password", "مثال: Authorization: Bearer xxx"),
        _f("send_file", "ارفع ملف الفيديو نفسه", "checkbox"), _f("send_short_instead", "ارفع الشورتس بدل الفيديو الطويل", "checkbox")]},
    "telegram": {"label": "✈️ تيليجرام (موبايل/كمبيوتر)", "fn": telegram, "fields": [
        _f("bot_token", "توكن البوت", "password", "من @BotFather"), _f("chat_id", "Chat ID", help="ابعت /start للبوت ثم /id"),
        _f("send_video", "ابعت ملفات الفيديو (أقل من 50MB)", "checkbox")]},
    "discord": {"label": "🎮 ديسكورد", "fn": discord, "fields": [_f("webhook_url", "Webhook URL", "password")]},
    "slack": {"label": "💬 سلاك", "fn": slack, "fields": [_f("webhook_url", "Incoming Webhook URL", "password")]},
    "ntfy": {"label": "🔔 إشعار للموبايل (تطبيق ntfy)", "fn": ntfy, "fields": [
        _f("topic", "اسم القناة (topic)", help="اسم صعب التخمين، واشترك فيه من تطبيق ntfy"), _f("server", "السيرفر", help="فاضي = ntfy.sh")]},
    "whatsapp_callmebot": {"label": "🟢 واتساب (CallMeBot)", "fn": whatsapp_callmebot, "fields": [
        _f("phone", "رقمك بالكود الدولي"), _f("apikey", "API key", "password", "من callmebot.com")]},
    "youtube": {"label": "▶️ يوتيوب (رفع تلقائي)", "fn": youtube, "fields": [
        _f("client_id", "OAuth Client ID"), _f("client_secret", "Client Secret", "password"),
        _f("refresh_token", "Refresh Token", "password", "شوف docs/connect-youtube.md"),
        _f("privacy", "الخصوصية", help="private / unlisted / public"), _f("category_id", "Category ID", help="27 = تعليم"),
        _f("upload_short", "ارفع الشورتس كمان", "checkbox")]},
    "facebook_page": {"label": "📘 صفحة فيسبوك", "fn": facebook_page, "fields": [
        _f("page_id", "Page ID"), _f("page_access_token", "Page Access Token", "password"),
        _f("post_short", "انشر الشورتس بدل الطويل", "checkbox"), _f("api_version", "Graph API version", help="مثال v21.0")]},
    "tiktok": {"label": "🎵 تيك توك (الشورتس)", "fn": tiktok, "fields": [
        _f("access_token", "Access Token", "password", "تطبيق TikTok Developers بصلاحية video.publish"),
        _f("privacy_level", "الخصوصية", help="SELF_ONLY للتطبيقات غير المعتمدة، أو PUBLIC_TO_EVERYONE")]},
}


def public_types():
    return {k: {"label": v["label"], "fields": v["fields"]} for k, v in TYPES.items()}


def publish_all(settings, pkg, only_id=None):
    results = []
    for c in settings["connectors"]:
        if only_id and c.get("id") != only_id:
            continue
        if not only_id and not c.get("enabled"):
            continue
        t = TYPES.get(c.get("type"))
        if not t:
            results.append({"connector": c.get("name"), "ok": False, "msg": "نوع غير معروف"})
            continue
        try:
            results.append({"connector": c.get("name") or t["label"], "ok": True, "msg": t["fn"](c, pkg)})
        except Exception as e:  # one broken connector must not stop the others
            results.append({"connector": c.get("name") or t["label"], "ok": False, "msg": str(e)[:500]})
    return results

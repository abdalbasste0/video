"""The private app: a password-protected control panel that runs on the owner's computer only.

- Listens on 127.0.0.1 only (it can't be opened from another device) unless APP_HOST is changed on purpose.
- The password is stored as a hash (PBKDF2), never as plain text, and the session cookie is HttpOnly + SameSite=Strict.
- Runs the factory in the background (it starts itself at 08:00) and shows everything in the panel:
  stage progress, the helper bots, approvals (idea / script / final video), commands, publishing, history, and settings.

Run it: python -m factory app   (or from the desktop shortcut)
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import mimetypes
import os
import secrets
import threading
import time
import webbrowser
from datetime import timedelta
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from html import escape as _h
from urllib.parse import parse_qs, unquote, urlparse

from .. import config
from ..approval import push_command, read_decision, record_decision
from ..config import PUBLISH_HARD_LIMIT, SCHEDULE, WORK_START, env, save_env, settings
from ..log import log
from ..state import Job, current_job, history

STATIC = Path(__file__).parent / "static"
SESSION_TTL = 12 * 3600
COOKIE = "vf_session"

# Keys shown on the settings page. secret=True → the value is never sent back to the browser (only whether it is set).
SETTING_KEYS = [
    ("ANTHROPIC_API_KEY", "Claude (البحث والكتابة والمراجعة)", True),
    ("ELEVENLABS_API_KEY", "ElevenLabs — مفتاح", True),
    ("ELEVENLABS_VOICE_ID", "ElevenLabs — معرّف الصوت الإنجليزي", False),
    ("PEXELS_API_KEY", "Pexels — مفتاح", True),
    ("PIXABAY_API_KEY", "Pixabay — مفتاح", True),
    ("TELEGRAM_BOT_TOKEN", "Telegram — توكن البوت", True),
    ("TELEGRAM_OWNER_CHAT_ID", "Telegram — رقم محادثتك", False),
    ("YOUTUBE_CLIENT_ID", "YouTube — Client ID", False),
    ("YOUTUBE_CLIENT_SECRET", "YouTube — Client Secret", True),
    ("YOUTUBE_REFRESH_TOKEN", "YouTube — Refresh Token", True),
    ("YOUTUBE_PRIVACY", "YouTube — الخصوصية (public / unlisted / private)", False),
    ("TIKTOK_CLIENT_KEY", "TikTok — Client Key", False),
    ("TIKTOK_CLIENT_SECRET", "TikTok — Client Secret", True),
    ("TIKTOK_REFRESH_TOKEN", "TikTok — Refresh Token", True),
    ("TIKTOK_PRIVACY", "TikTok — الخصوصية (SELF_ONLY حتى اعتماد التطبيق ثم PUBLIC_TO_EVERYONE)", False),
    ("IG_USER_ID", "Instagram — رقم الحساب (IG User ID)", False),
    ("IG_ACCESS_TOKEN", "Instagram — Access Token طويل المدة", True),
    ("FACTORY_PLATFORMS", "منصات النشر (youtube,tiktok,instagram)", False),
    ("FACTORY_LANGUAGE", "لغة الفيديو والتعليق الصوتي (en)", False),
    ("FACTORY_FORMAT", "شكل الفيديو (landscape / vertical)", False),
    ("FACTORY_TIMEZONE", "المنطقة الزمنية (مثال Africa/Cairo)", False),
]
ALLOWED_KEYS = {k for k, _, _ in SETTING_KEYS}


# ===========================================================================
# Password and sessions
# ===========================================================================
def _auth_file() -> Path:
    return settings.workspace / "app_auth.json"


def password_is_set() -> bool:
    return _auth_file().exists()


def set_password(pw: str) -> None:
    salt = secrets.token_bytes(16)
    h = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 300_000)
    settings.workspace.mkdir(parents=True, exist_ok=True)
    _auth_file().write_text(json.dumps({"salt": salt.hex(), "hash": h.hex()}), encoding="utf-8")
    try:
        _auth_file().chmod(0o600)
    except OSError:
        pass


def check_password(pw: str) -> bool:
    if not password_is_set():
        return False
    d = json.loads(_auth_file().read_text(encoding="utf-8"))
    h = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(d["salt"]), 300_000)
    return hmac.compare_digest(h.hex(), d["hash"])


class Sessions:
    def __init__(self) -> None:
        self._s: dict[str, float] = {}
        self._fails: list[float] = []
        self._lock = threading.Lock()

    def new(self) -> str:
        tok = secrets.token_urlsafe(32)
        with self._lock:
            self._s[tok] = time.time() + SESSION_TTL
        return tok

    def valid(self, tok: str | None) -> bool:
        with self._lock:
            return bool(tok) and self._s.get(tok, 0) > time.time()

    def drop(self, tok: str | None) -> None:
        with self._lock:
            self._s.pop(tok or "", None)

    def locked_out(self) -> bool:
        """Brute-force protection: 5 failed attempts within a minute → a one-minute lockout."""
        with self._lock:
            now = time.time()
            self._fails = [t for t in self._fails if now - t < 60]
            return len(self._fails) >= 5

    def fail(self) -> None:
        with self._lock:
            self._fails.append(time.time())


SESSIONS = Sessions()


# ===========================================================================
# Running the factory in the background
# ===========================================================================
class FactoryRunner(threading.Thread):
    """Starts the workday by itself at 08:00 (or immediately from the "Start now" button)."""

    def __init__(self) -> None:
        super().__init__(name="factory-runner", daemon=True)
        self.manager = None
        self.kick = threading.Event()
        self.running_day = False
        self.last_error = ""
        self.auto_tried: set = set()

    def start_now(self) -> str:
        if self.running_day and self.manager:
            if self.manager.paused:
                self.manager.paused = False
                return "تم: استؤنف العمل."
            self.manager.start_now = True
            return "المصنع يعمل بالفعل."
        self.kick.set()
        return "تم: بدأ يوم العمل الآن."

    def resume(self) -> str:
        if self.manager:
            self.manager.paused = False
        return "تم الاستئناف ▶"

    def run(self) -> None:
        from ..bots.manager import DAY_STARTED, Manager

        while True:
            job = Job()
            started = any(e.get("msg") == DAY_STARTED for e in job.data.get("events", []))
            now = settings.now()
            in_window = settings.at(WORK_START) - timedelta(minutes=10) <= now < settings.at(PUBLISH_HARD_LIMIT)
            auto = in_window and not started and job.day not in self.auto_tried
            if self.kick.is_set() or auto:
                self.auto_tried.add(job.day)
                forced = self.kick.is_set()
                self.kick.clear()
                self.manager = Manager()
                self.running_day = True
                try:
                    self.manager.run_day(start_now=forced)
                except Exception as e:  # noqa: BLE001
                    self.last_error = str(e)
                    log.exception("Workday error")
                finally:
                    self.running_day = False
                continue
            self.kick.wait(timeout=20)


RUNNER = FactoryRunner()


# ===========================================================================
# Building the panel's state
# ===========================================================================
def _media_url(path: str | None) -> str | None:
    if not path:
        return None
    try:
        rel = Path(path).resolve().relative_to(settings.workspace.resolve())
    except ValueError:
        return None
    return "/media/" + rel.as_posix()


def build_state() -> dict:
    from ..publishers import NAMES_AR, PLATFORMS, enabled_platforms

    job = current_job()
    a = job.data["artifacts"]
    sched = job.data.get("schedule", {})
    stages = []
    pending = None
    for s in SCHEDULE:
        st = job.stage(s.key)
        if st.get("approval") == "pending" and not read_decision(job, s.key):
            pending = s.key
        stages.append({"key": s.key, "title": s.title_ar, "bot": s.bot, "deadline": sched.get(s.key, s.deadline.strftime("%H:%M")),
                       "needs_approval": s.needs_approval, **st})
    video = dict(a.get("video") or {})
    if video:
        video.update(url=_media_url(video.get("path")), vertical_url=_media_url(video.get("vertical")),
                     thumbnail_url=_media_url(video.get("thumbnail")))
    m = RUNNER.manager
    helpers = [{"name": h.name, "title": h.title_ar, "busy": h.busy, "assisting": h.assisting}
               for h in (m.helpers if m else [])]
    return {
        "now": settings.now().strftime("%Y-%m-%d %H:%M:%S"),
        "date": job.day.isoformat(),
        "running": RUNNER.running_day,
        "paused": bool(m and m.paused),
        "last_error": RUNNER.last_error,
        "halt_reason": "" if RUNNER.running_day else job.data.get("halt_reason", ""),
        "brief": job.brief,
        "stages": stages,
        "pending": pending,
        "ideas": a.get("ideas", []),
        "chosen_idea": a.get("chosen_idea"),
        "script": a.get("script"),
        "fact_checks": a.get("fact_checks", []),
        "video": video or None,
        "preview_sheet": _media_url(a.get("preview_sheet")),
        "qa_report": a.get("qa_report"),
        "published": a.get("published") or {},
        "events": job.data.get("events", [])[-60:][::-1],
        "helpers": helpers,
        "platforms": [{"key": k, "name": NAMES_AR[k], "configured": settings.dry_run or PLATFORMS[k].configured(),
                       "enabled": k in enabled_platforms()} for k in PLATFORMS],
        "history": history()[-30:][::-1],
        "language": settings.language,
        "format": settings.video_format,
        "dry_run": settings.dry_run,
        "publish_limit": sched.get("publish", PUBLISH_HARD_LIMIT.strftime("%H:%M")),
    }


# ===========================================================================
# HTTP
# ===========================================================================
class Handler(BaseHTTPRequestHandler):
    server_version = "VideoFactory"

    def log_message(self, fmt, *args):  # quiet HTTP logs
        logging.getLogger("factory.http").debug(fmt, *args)

    # ---------- helpers ----------
    def _token(self) -> str | None:
        c = cookies.SimpleCookie(self.headers.get("Cookie", ""))
        return c[COOKIE].value if COOKIE in c else None

    def _authed(self) -> bool:
        return SESSIONS.valid(self._token())

    def _send(self, code: int, body: bytes, ctype: str, extra: dict | None = None) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, data, code: int = 200, extra: dict | None = None) -> None:
        self._send(code, json.dumps(data, ensure_ascii=False).encode(), "application/json; charset=utf-8", extra)

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if n > 1_000_000:
            return {}
        try:
            return json.loads(self.rfile.read(n) or b"{}")
        except json.JSONDecodeError:
            return {}

    def _same_origin(self) -> bool:
        """CSRF protection: every POST must come from the app's own page."""
        if self.headers.get("X-VF") != "1":
            return False
        origin = self.headers.get("Origin")
        return origin is None or urlparse(origin).netloc == self.headers.get("Host")

    # ---------- GET ----------
    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            return self._send(200, (STATIC / "index.html").read_bytes(), "text/html; charset=utf-8",
                              {"Content-Security-Policy": "default-src 'self'; img-src 'self' data:; media-src 'self'; "
                                                          "style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'"})
        if path in ("/icon.png", "/favicon.ico"):
            icon = config.ROOT / "assets" / "icon.png"
            return self._send(200, icon.read_bytes(), "image/png") if icon.exists() else self._send(404, b"", "text/plain")
        if path == "/oauth/youtube/callback":
            return self._youtube_callback()
        if path == "/api/auth":
            return self._json({"authed": self._authed(), "password_set": password_is_set(), "version": VERSION})
        if not self._authed():
            return self._json({"error": "unauthorized"}, 401)
        if path == "/api/state":
            return self._json(build_state())
        if path == "/api/settings":
            return self._json([{"key": k, "label": label, "secret": sec, "set": bool(env(k)),
                                "value": "" if sec else env(k)} for k, label, sec in SETTING_KEYS])
        if path.startswith("/media/"):
            return self._media(unquote(path[len("/media/"):]))
        if path == "/api/youtube/connect":
            from . import youtube_oauth
            try:
                url = youtube_oauth.start_url()
            except RuntimeError as e:
                return self._page("لم يتم الربط", str(e), ok=False)
            self.send_response(302)
            self.send_header("Location", url)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self._json({"error": "not found"}, 404)

    def _media(self, rel: str) -> None:
        root = settings.workspace.resolve()
        f = (root / rel).resolve()
        if root not in f.parents or not f.is_file() or f.name in ("app_auth.json",):
            return self._json({"error": "not found"}, 404)
        size = f.stat().st_size
        ctype = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
        rng = self.headers.get("Range", "")
        start, end = 0, size - 1
        code = 200
        if rng.startswith("bytes="):  # needed for seeking in the video player
            a, _, b = rng[6:].split(",")[0].partition("-")
            start = int(a) if a else max(size - int(b), 0)
            end = min(int(b), size - 1) if a and b else size - 1
            code = 206
        length = end - start + 1
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(length))
        if code == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        with open(f, "rb") as fh:
            fh.seek(start)
            remaining = length
            while remaining > 0:
                chunk = fh.read(min(1 << 20, remaining))
                if not chunk:
                    break
                try:
                    self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError):
                    return
                remaining -= len(chunk)

    # ---------- POST ----------
    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if not self._same_origin():
            return self._json({"error": "forbidden"}, 403)
        body = self._body()

        if path == "/api/shutdown":
            if not hmac.compare_digest(str(body.get("token", "")), _LOCK_TOKEN):
                return self._json({"error": "forbidden"}, 403)
            self._json({"ok": True})
            log.info("Closing this copy of the app so it can be replaced with the update")
            threading.Timer(0.3, lambda: os._exit(0)).start()
            return
        if path == "/api/setup":
            if password_is_set():
                return self._json({"error": "كلمة المرور مضبوطة مسبقاً"}, 400)
            pw = str(body.get("password", ""))
            if len(pw) < 8:
                return self._json({"error": "كلمة المرور يجب أن تكون 8 أحرف على الأقل"}, 400)
            set_password(pw)
            return self._login_ok()
        if path == "/api/login":
            if SESSIONS.locked_out():
                return self._json({"error": "محاولات كثيرة. انتظر دقيقة."}, 429)
            if check_password(str(body.get("password", ""))):
                return self._login_ok()
            SESSIONS.fail()
            return self._json({"error": "كلمة المرور غير صحيحة"}, 401)
        if not self._authed():
            return self._json({"error": "unauthorized"}, 401)

        if path == "/api/logout":
            SESSIONS.drop(self._token())
            return self._json({"ok": True}, extra={"Set-Cookie": f"{COOKIE}=; Max-Age=0; Path=/; HttpOnly; SameSite=Strict"})
        if path == "/api/decision":
            stage, status = body.get("stage"), body.get("status")
            if stage not in {"research", "script", "final_review"} or status not in {"approved", "rejected"}:
                return self._json({"error": "bad request"}, 400)
            record_decision(current_job(), stage, status, str(body.get("value", "")), str(body.get("note", "")), by="app")
            return self._json({"ok": True, "message": "تم تسجيل قرارك ✔"})
        if path == "/api/command":
            text = str(body.get("text", "")).strip()
            if not text:
                return self._json({"error": "اكتب التعليمات"}, 400)
            push_command(text)
            return self._json({"ok": True, "message": "تم إرسال التعليمات للبوت التاسع"})
        if path == "/api/start":
            return self._json({"ok": True, "message": RUNNER.start_now()})
        if path == "/api/resume":
            return self._json({"ok": True, "message": RUNNER.resume()})
        if path == "/api/publish":
            from ..bots.manager import Manager
            m = RUNNER.manager or Manager()
            job = current_job()
            m.job = job
            plats = [p for p in body.get("platforms", []) if isinstance(p, str)] or None
            try:
                res = m.publish(job, allow_late=bool(body.get("late")), platforms=plats)
            except (PermissionError, RuntimeError) as e:
                return self._json({"error": str(e)}, 400)
            return self._json({"ok": True, "result": res, "message": "تمت محاولة النشر — راجع النتائج"})
        if path == "/api/settings":
            updates = {k: str(v).strip() for k, v in body.items()
                       if k in ALLOWED_KEYS and isinstance(v, str) and v.strip() and "\n" not in v}
            if updates:
                save_env(updates)
            return self._json({"ok": True, "message": f"تم حفظ {len(updates)} إعداد"})
        if path == "/api/password":
            if not check_password(str(body.get("old", ""))):
                return self._json({"error": "كلمة المرور الحالية غير صحيحة"}, 400)
            new = str(body.get("new", ""))
            if len(new) < 8:
                return self._json({"error": "8 أحرف على الأقل"}, 400)
            set_password(new)
            return self._json({"ok": True, "message": "تم تغيير كلمة المرور"})
        self._json({"error": "not found"}, 404)

    def _page(self, title: str, msg: str, ok: bool = True) -> None:
        icon = "✅" if ok else "⚠️"
        html = (f'<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8">'
                f'<meta name="viewport" content="width=device-width, initial-scale=1"><title>{_h(title)}</title>'
                '<style>body{font:16px/1.7 "Segoe UI",Tahoma,sans-serif;background:#f4f5f8;color:#16181d;margin:0}'
                '.c{max-width:520px;margin:12vh auto;background:#fff;border:1px solid #e4e7ec;border-radius:14px;padding:28px;text-align:center}'
                'a{display:inline-block;margin-top:14px;background:#5b3df5;color:#fff;padding:10px 18px;border-radius:10px;text-decoration:none}'
                '@media (prefers-color-scheme:dark){body{background:#0f1115;color:#eceef3}.c{background:#181b22;border-color:#2a2f3a}}</style>'
                f'</head><body><div class="c"><h2>{icon} {_h(title)}</h2><p>{_h(msg)}</p>'
                '<a href="/">ارجع إلى التطبيق</a></div></body></html>')
        self._send(200 if ok else 400, html.encode(), "text/html; charset=utf-8")

    def _youtube_callback(self) -> None:
        # The session cookie isn't sent on the redirect back from Google (SameSite=Strict); protection relies on a
        # single-use random state value that expires after 10 minutes and is created only from a logged-in session.
        from . import youtube_oauth
        q = parse_qs(urlparse(self.path).query)
        if "error" in q:
            return self._page("لم يتم الربط", "ألغيت الموافقة في صفحة جوجل. يمكنك المحاولة مرة أخرى من الإعدادات.", ok=False)
        try:
            channel = youtube_oauth.finish(q.get("state", [""])[0], q.get("code", [""])[0])
        except Exception as e:  # noqa: BLE001
            return self._page("لم يتم الربط", str(e), ok=False)
        return self._page("تم ربط يوتيوب", f"تم ربط القناة «{channel}» بنجاح." if channel else "تم ربط حساب يوتيوب بنجاح.")

    def _login_ok(self) -> None:
        tok = SESSIONS.new()
        self._json({"ok": True}, extra={
            "Set-Cookie": f"{COOKIE}={tok}; Max-Age={SESSION_TTL}; Path=/; HttpOnly; SameSite=Strict"})


# ===========================================================================
class AppServer(ThreadingHTTPServer):
    """On Windows, Python allows two programs to share one port (SO_REUSEADDR), so requests can reach an old copy.
    We prevent that with an exclusive port binding, so a second copy can't open alongside the first."""
    daemon_threads = True
    allow_reuse_address = os.name != "nt"

    def server_bind(self):
        import socket
        if os.name == "nt" and hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def code_version() -> str:
    """A fingerprint of the code on disk: it changes with every update, so an outdated running copy can be detected."""
    h = hashlib.sha256()
    pkg = Path(__file__).resolve().parent.parent
    for f in sorted(pkg.rglob("*")):
        if f.is_file() and f.suffix in {".py", ".html"}:
            h.update(f.relative_to(pkg).as_posix().encode())
            h.update(f.read_bytes())
    return h.hexdigest()[:16]


VERSION = code_version()
_LOCK_TOKEN = secrets.token_urlsafe(24)
_HTTPD: "AppServer | None" = None


def _lock_file() -> Path:
    return settings.workspace / "app.lock"


def _replace_old_copy(port: int) -> bool:
    """If an older copy of the app is running, ask it to close (using the secret in app.lock) and wait until the port frees up."""
    import urllib.request
    try:
        info = json.loads(_lock_file().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    if info.get("version") == VERSION:
        return False  # the same version → it's already up to date
    log.info("An older copy of the app is running (%s) → closing it and starting the update (%s)", info.get("version"), VERSION)
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/api/shutdown", method="POST",
                                     data=json.dumps({"token": info.get("token", "")}).encode(),
                                     headers={"Content-Type": "application/json", "X-VF": "1"})
        urllib.request.urlopen(req, timeout=5).read()
    except Exception as e:  # noqa: BLE001
        log.warning("Could not close the old copy automatically: %s", e)
        return False
    for _ in range(40):
        time.sleep(0.25)
        try:
            import socket
            with socket.create_connection(("127.0.0.1", port), timeout=0.3):
                pass
        except OSError:
            return True  # the port is free now
    return False


def serve(open_browser: bool = True, run_factory: bool = True) -> None:
    global _HTTPD
    host = env("APP_HOST", "127.0.0.1")
    port = int(env("APP_PORT", "8765"))
    url = f"http://127.0.0.1:{port}/"
    settings.workspace.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(settings.workspace / "factory.log", encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s [%(threadName)s] %(levelname)s %(message)s"))
    log.addHandler(fh)
    try:
        httpd = AppServer((host, port), Handler)
    except OSError:
        if not _replace_old_copy(port):
            # The same version is already running → just open it
            log.info("The app is already running at %s", url)
            if open_browser:
                webbrowser.open(url)
            return
        httpd = AppServer((host, port), Handler)
    _HTTPD = httpd
    _lock_file().write_text(json.dumps({"version": VERSION, "token": _LOCK_TOKEN, "pid": os.getpid()}), encoding="utf-8")
    try:
        _lock_file().chmod(0o600)
    except OSError:
        pass
    if run_factory:
        RUNNER.start()
    log.info("🏭 The factory app (version %s) is running at %s", VERSION, url)
    if open_browser:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass

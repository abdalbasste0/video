"""Control panel. Run:  python run_factory.py
Then open http://localhost:8765 on the computer, or http://<computer-ip>:8765 on your phone (same Wi-Fi)."""
import socket
from functools import wraps
from pathlib import Path

from flask import Flask, Response, abort, jsonify, request, send_file

from factory import connectors, settings as cfg
from factory.pipeline import get_factory
from factory.roster import WORKERS

app = Flask(__name__, static_folder=None)
INDEX = Path(__file__).parent / "factory" / "static" / "index.html"


def guarded(fn):
    @wraps(fn)
    def inner(*a, **kw):
        pw = cfg.load().get("dashboard_password")
        auth = request.authorization
        if pw and not (auth and auth.password == pw):
            return Response("كلمة السر مطلوبة", 401, {"WWW-Authenticate": 'Basic realm="video-factory"'})
        return fn(*a, **kw)
    return inner


def _job_view(j):
    return {k: j.get(k) for k in ("id", "topic", "status", "current", "error", "publish", "created", "finished", "demo")} | {
        "steps": {wid: {"status": st.get("status"), "secs": st.get("secs")} for wid, st in j["steps"].items()},
        "title": ((j["steps"].get("seo_publisher") or {}).get("output") or {}).get("title")
                 or ((j["steps"].get("idea_judge") or {}).get("output") or {}).get("topic") or j.get("topic"),
        "files": [n for n in ("video.mp4", "short.mp4", "thumbnail.jpg", "captions.srt") if (Path(j["dir"]) / n).exists()],
    }


@app.get("/")
@guarded
def index():
    return send_file(INDEX)


@app.get("/api/state")
@guarded
def state():
    return jsonify(settings=cfg.masked(cfg.load()), workers=WORKERS, connector_types=connectors.public_types(),
                   jobs=[_job_view(j) for j in get_factory().list()[:40]])


@app.post("/api/settings")
@guarded
def save_settings():
    new = request.get_json(force=True)
    old = cfg.load()
    merged = cfg.unmask(new, old)
    cfg.save(merged)
    return jsonify(ok=True)


@app.post("/api/jobs")
@guarded
def new_jobs():
    body = request.get_json(force=True)
    topics = [t.strip() for t in (body.get("topics") or "").splitlines() if t.strip()]
    count = max(1, min(int(body.get("count") or 1), 20))
    from factory import llm
    if not body.get("demo") and not llm.has_key(cfg.load()):
        return jsonify(error=llm.NO_KEY), 400
    f = get_factory()
    ids = [f.submit(t, demo=bool(body.get("demo"))) for t in topics] if topics else \
          [f.submit(None, demo=bool(body.get("demo"))) for _ in range(count)]
    return jsonify(ids=ids)


@app.post("/api/jobs/<jid>/resume")
@guarded
def resume(jid):
    get_factory().resume(jid)
    return jsonify(ok=True)


@app.post("/api/jobs/<jid>/publish")
@guarded
def republish(jid):
    return jsonify(results=get_factory().republish(jid, (request.get_json(silent=True) or {}).get("connector_id")))


@app.post("/api/connectors/test")
@guarded
def test_connector():
    """Send the newest finished video (or a text-only sample) through one connector."""
    body = request.get_json(force=True)
    s = cfg.load()
    c = cfg.unmask(body["connector"], next((x for x in s["connectors"] if x.get("id") == body["connector"].get("id")), {}))
    s["connectors"] = [dict(c, enabled=True)]
    done = [j for j in get_factory().list() if j["status"] == "done"]
    if done:
        pkg = get_factory()._package(done[0])
    else:
        pkg = {"job_id": "test", "job_dir": "", "topic": "اختبار", "video": None, "short": None, "thumbnail": None, "srt": None,
               "title": "اختبار ربط مصنع الفيديوهات ✅", "description": "لو وصلتك الرسالة دي يبقى الربط شغال.", "tags": [],
               "hashtags": [], "short_title": "اختبار", "pinned_comment": ""}
    return jsonify(results=connectors.publish_all(s, pkg, only_id=c.get("id")))


@app.post("/api/images/test")
@guarded
def test_image():
    """Generate one sample picture with the chosen image service and show it in the dashboard."""
    import base64
    import io
    from factory import image_providers
    s = cfg.load()
    if not image_providers.enabled(s["images"]):
        return jsonify(ok=False, error="اختار مولّد صور وحط المفتاح الأول")
    story = s["channel"].get("format") == "story"
    style = s["images"]["story_style_prompt"] if story else s["images"]["style_prompt"]
    try:
        img = image_providers.generate("a stick figure scientist looking at a deep sea submarine. Style: " + style, s["images"], 1280, 720, seed=7)
    except Exception as e:
        return jsonify(ok=False, error=str(e)[:400])
    buf = io.BytesIO()
    img.convert("RGB").resize((640, int(640 * img.height / img.width))).save(buf, "JPEG", quality=85)
    return jsonify(ok=True, image=base64.b64encode(buf.getvalue()).decode())


@app.post("/api/claude/test")
@guarded
def test_claude():
    from factory import llm
    ok, msg = llm.check_key(cfg.load())
    return jsonify(ok=ok, message=msg)


@app.post("/api/voice/test")
@guarded
def test_voice():
    """Speak one sentence with the chosen voice settings, so voice problems show up before a whole video."""
    import base64
    import tempfile
    from factory import media
    s = cfg.load()
    text = ("This is a quick test of the factory voice." if s["channel"].get("language") == "en"
            else "ده اختبار سريع لصوت المصنع.")
    try:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "test.mp3"
            secs = media.tts(p, text, s)
            data = base64.b64encode(p.read_bytes()).decode()
    except Exception as e:
        return jsonify(ok=False, error=str(e)[:500])
    return jsonify(ok=True, seconds=round(secs, 1), audio=data)


@app.get("/files/<jid>/<name>")
@guarded
def files(jid, name):
    if name not in ("video.mp4", "short.mp4", "thumbnail.jpg", "captions.srt", "job.json"):
        abort(404)
    j = get_factory().jobs.get(jid) or abort(404)
    p = Path(j["dir"]) / name
    return send_file(p) if p.exists() else abort(404)


def lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def serve(host="0.0.0.0", port=8765):
    from factory.telegram_bot import start_in_background
    get_factory()
    start_in_background()
    print(f"\n🏭 لوحة تحكم المصنع:\n   على الحاسوب:  http://localhost:{port}\n   على الموبايل: http://{lan_ip()}:{port}  (نفس شبكة الواي فاي)\n")
    if host != "127.0.0.1" and not cfg.load().get("dashboard_password"):
        print("⚠️  حط كلمة سر للوحة (الإعدادات ← كلمة سر اللوحة) قبل ما تفتحها من أجهزة تانية.\n")
    app.run(host=host, port=port, threaded=True)

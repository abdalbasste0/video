"""Settings live in settings.json (next to run_factory.py). The dashboard edits this file."""
import copy
import json
import os
import threading
from pathlib import Path

from .roster import WORKERS

ROOT = Path(__file__).resolve().parent.parent
SETTINGS_PATH = Path(os.environ.get("FACTORY_SETTINGS", ROOT / "settings.json"))
_lock = threading.Lock()

DEFAULTS = {
    "anthropic_api_key": "",          # or set ANTHROPIC_API_KEY in the environment
    "model_main": "claude-opus-5-5",  # brains of the writing workers
    "model_fast": "claude-opus-5-5",  # light workers (ideas, thumbnail text, SEO) - switch to a faster model for speed
    "effort": "high",                 # low / medium / high / xhigh / max
    "web_research": True,             # researcher + fact checker search the web
    "parallel_videos": 2,             # how many videos the factory builds at the same time
    "parallel_scene_jobs": 6,         # images/voices generated in parallel inside one video
    "output_dir": "output",
    "dashboard_password": "",         # set this before opening the dashboard to your phone/network
    "channel": {
        "name": "قناتي",
        "niche": "ألغاز من الحياة اليومية لها جذور في الاقتصاد والتاريخ (فولت الكهربا، شكل الفيشة، لوحة المفاتيح، الأسعار...)",
        "language": "ar",                 # ar = Arabic video, en = English video
        "format": "explainer",            # explainer (لغز + درس، تقسيمة ثابتة) / story (قصة بمشاكل متتالية + رسوم ستيك مان)
        "dialect": "مصري",
        "audience": "شباب عرب فضوليين بيحبوا المعلومة المبسطة",
        "video_minutes": 5.5,
        "cta_question": "إيه الحاجة اللي شغالة عندنا غلط ومحدش قادر يغيّرها؟",
    },
    "voice": {
        "provider": "edge",                 # edge (free) / elevenlabs / piper (offline) / silent (testing)
        "edge_voice": "ar-EG-ShakirNeural",  # ar-EG-SalmaNeural, ar-SA-HamedNeural, en-US-GuyNeural, en-GB-RyanNeural...
        "edge_rate": "+5%",
        "elevenlabs_api_key": "",
        "elevenlabs_voice_id": "",
        "elevenlabs_model": "eleven_multilingual_v2",
        "piper_model": "",          # path to a Piper .onnx voice (free, offline)
        "piper_length_scale": 1.0,  # >1 = slower speech
    },
    "images": {
        "provider": "cards",  # cards (offline 2D cards) / http (any image API you connect)
        "http_url": "",
        "http_auth_header": "",
        "style_prompt": "flat 2D vector explainer illustration, muted beige background, bold red green and blue accents, clean shapes, no text",
        "story_style_prompt": ("simple hand-drawn webcomic cartoon, stick figure characters with big round white heads and large round eyes, "
                               "thin black outlines, flat muted colors, clean uncluttered background, 16:9, no text, no watermark"),
    },
    "video": {
        "width": 1920, "height": 1080, "fps": 30,
        "burn_captions": True,
        "make_short": True,
        "story_captions": False,      # the story reference shows no captions
        "story_music_volume": 0.14,   # story reference: music bed audible under the whole narration
        "music_volume": 0.06,  # reference: voice-first, music barely audible
    },
    "workers": {w["id"]: {"enabled": True, "model": w["model"]} for w in WORKERS},
    "connectors": [
        {"id": "local", "type": "local_folder", "name": "مجلد الفيديوهات الجاهزة", "enabled": True, "path": "output/ready"},
    ],
    "control": {
        "telegram_bot_token": "",
        "allowed_chat_ids": "",  # comma separated; empty = anyone who finds the bot (not recommended)
    },
}


def _merge(base, override):
    out = copy.deepcopy(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def load():
    with _lock:
        data = {}
        if SETTINGS_PATH.exists():
            data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        return _merge(DEFAULTS, data)


def save(settings):
    with _lock:
        tmp = SETTINGS_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(SETTINGS_PATH)


SECRET_HINTS = ("key", "token", "secret", "password", "auth")
MASK = "••••••"


def is_secret(name):
    return any(h in name.lower() for h in SECRET_HINTS)


def masked(obj):
    """Copy of settings safe to send to the browser."""
    if isinstance(obj, dict):
        return {k: (MASK if is_secret(k) and isinstance(v, str) and v else masked(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [masked(x) for x in obj]
    return obj


def unmask(new, old):
    """Keep the stored secret when the browser sends back the mask."""
    if isinstance(new, dict):
        old = old if isinstance(old, dict) else {}
        return {k: (old.get(k, "") if v == MASK else unmask(v, old.get(k))) for k, v in new.items()}
    if isinstance(new, list):
        old_by_id = {o.get("id"): o for o in (old or []) if isinstance(o, dict)}
        return [unmask(x, old_by_id.get(x.get("id")) if isinstance(x, dict) else None) for x in new]
    return new

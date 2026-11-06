"""Connecting a YouTube account from the app with one button (instead of fetching a Refresh Token by hand).

The flow:
 1. The owner enters the Client ID and Client Secret (an OAuth client of type "Desktop app" in Google Cloud).
 2. Clicks "Connect YouTube account" → the app opens Google's sign-in page (OAuth with PKCE).
 3. After approval, Google sends them back to http://127.0.0.1:<port>/oauth/youtube/callback
    → the app exchanges the code for a Refresh Token and saves it in .env automatically.

Google allows loopback addresses (127.0.0.1) on any port for desktop clients, with no registration needed.
"""
from __future__ import annotations

import base64
import hashlib
import secrets
import threading
import time
from urllib.parse import urlencode

import requests

from ..config import env, save_env

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]

_pending: dict[str, tuple[str, float]] = {}  # state → (code_verifier, expiry)
_lock = threading.Lock()


def redirect_uri() -> str:
    return f"http://127.0.0.1:{env('APP_PORT', '8765')}/oauth/youtube/callback"


def start_url() -> str:
    client_id = env("YOUTUBE_CLIENT_ID")
    if not client_id or not env("YOUTUBE_CLIENT_SECRET"):
        raise RuntimeError("أدخل YouTube Client ID و Client Secret في الإعدادات واضغط «حفظ» أولاً.")
    state = secrets.token_urlsafe(24)
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    with _lock:
        now = time.time()
        for k in [k for k, (_, exp) in _pending.items() if exp < now]:
            _pending.pop(k, None)
        _pending[state] = (verifier, now + 600)  # valid for 10 minutes, single use
    return AUTH_URL + "?" + urlencode({
        "client_id": client_id,
        "redirect_uri": redirect_uri(),
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",   # to get a Refresh Token
        "prompt": "consent",        # ensures a new Refresh Token is issued every time
        "include_granted_scopes": "true",
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    })


def finish(state: str, code: str) -> str:
    """Exchanges the code for a Refresh Token, saves it, and returns the channel name."""
    with _lock:
        item = _pending.pop(state, None)
    if not item or item[1] < time.time():
        raise RuntimeError("انتهت صلاحية طلب الربط. ارجع للتطبيق واضغط «ربط حساب يوتيوب» مرة أخرى.")
    r = requests.post(TOKEN_URL, timeout=30, data={
        "client_id": env("YOUTUBE_CLIENT_ID"),
        "client_secret": env("YOUTUBE_CLIENT_SECRET"),
        "code": code,
        "code_verifier": item[0],
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri(),
    })
    data = r.json()
    if "refresh_token" not in data:
        raise RuntimeError(f"لم يُرجع جوجل رمز الربط: {data.get('error_description') or data.get('error') or data}")
    save_env({"YOUTUBE_REFRESH_TOKEN": data["refresh_token"]})
    try:
        ch = requests.get("https://www.googleapis.com/youtube/v3/channels", timeout=30,
                          params={"part": "snippet", "mine": "true"},
                          headers={"Authorization": f"Bearer {data['access_token']}"}).json()
        return ch["items"][0]["snippet"]["title"]
    except (requests.RequestException, KeyError, IndexError, ValueError):
        return ""

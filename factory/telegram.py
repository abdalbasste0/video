"""Minimal Telegram Bot API client (plain HTTPS, works the same on PC and phone)."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import requests

log = logging.getLogger("telegram")


class Telegram:
    def __init__(self, token: str, owner_id: str):
        self.token = token
        self.owner_id = str(owner_id)
        self.base = f"https://api.telegram.org/bot{token}"

    @property
    def enabled(self) -> bool:
        return bool(self.token and self.owner_id)

    def _call(self, method: str, files: dict | None = None, http_timeout: int = 60, **params: Any) -> Any:
        data = {k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v)
                for k, v in params.items() if v is not None}
        r = requests.post(f"{self.base}/{method}", data=data, files=files, timeout=http_timeout)
        body = r.json()
        if not body.get("ok"):
            raise RuntimeError(f"Telegram {method}: {body.get('description')}")
        return body["result"]

    def send(self, text: str, buttons: list[list[dict]] | None = None, chat_id: str | None = None) -> dict:
        return self._call("sendMessage", chat_id=chat_id or self.owner_id, text=text[:4096],
                          reply_markup={"inline_keyboard": buttons} if buttons else None)

    def send_photo(self, path: Path, caption: str = "") -> dict:
        with open(path, "rb") as f:
            return self._call("sendPhoto", files={"photo": f}, chat_id=self.owner_id, caption=caption[:1024])

    def send_video(self, path: Path, caption: str = "", buttons: list[list[dict]] | None = None,
                   thumb: Path | None = None) -> dict:
        files = {"video": open(path, "rb")}
        if thumb and thumb.exists():
            files["thumbnail"] = open(thumb, "rb")
        try:
            return self._call("sendVideo", files=files, http_timeout=600, chat_id=self.owner_id, caption=caption[:1024],
                              supports_streaming=True,
                              reply_markup={"inline_keyboard": buttons} if buttons else None)
        finally:
            for f in files.values():
                f.close()

    def send_document(self, path: Path, caption: str = "") -> dict:
        with open(path, "rb") as f:
            return self._call("sendDocument", files={"document": f}, http_timeout=600, chat_id=self.owner_id,
                              caption=caption[:1024])

    def answer(self, callback_id: str, text: str = "") -> None:
        try:
            self._call("answerCallbackQuery", callback_query_id=callback_id, text=text[:200])
        except Exception as e:  # expired callbacks are harmless
            log.debug("answerCallback: %s", e)

    def edit_buttons(self, chat_id: Any, message_id: int, buttons: list[list[dict]] | None) -> None:
        try:
            self._call("editMessageReplyMarkup", chat_id=chat_id, message_id=message_id,
                       reply_markup={"inline_keyboard": buttons or []})
        except Exception as e:
            log.debug("editMarkup: %s", e)

    def updates(self, offset: int, timeout: int = 50) -> list[dict]:
        return self._call("getUpdates", http_timeout=timeout + 15, offset=offset, timeout=timeout,
                          allowed_updates=["message", "callback_query"])


def btn(text: str, data: str) -> dict:
    return {"text": text, "callback_data": data[:64]}

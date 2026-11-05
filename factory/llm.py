"""Single interface to Claude, shared by every bot.

- ask():       free-form text answer
- ask_json():  answer validated against a Pydantic model (with an automatic retry if the format is wrong)
- web_search:  lets the bot search the internet (for bot 1 trend research and bot 2 date checks)
"""
from __future__ import annotations

import json
import re
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from .config import settings
from .log import log

T = TypeVar("T", bound=BaseModel)

_client = None
WEB_SEARCH_TOOL = {"type": "web_search_20260209", "name": "web_search", "max_uses": 8}


def _get_client():
    global _client
    if _client is None:
        import anthropic

        _client = anthropic.Anthropic()
    return _client


def _call(system: str, messages: list[dict], web_search: bool, effort: str) -> Any:
    client = _get_client()
    kwargs: dict[str, Any] = dict(
        model=settings.model,
        max_tokens=16000,
        system=system,
        messages=messages,
        output_config={"effort": effort},
        # If a request is declined for policy reasons, the server retries it on a suitable fallback model
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    )
    if web_search:
        kwargs["tools"] = [WEB_SEARCH_TOOL]
    return client.beta.messages.create(**kwargs)


def ask(system: str, prompt: str, *, web_search: bool = False, effort: str = "high", mock: str | None = None) -> str:
    if settings.dry_run:
        return mock if mock is not None else "[dry-run] رد تجريبي"

    messages: list[dict] = [{"role": "user", "content": prompt}]
    for _ in range(6):  # web search can pause a long turn (pause_turn), so we resume it
        resp = _call(system, messages, web_search, effort)
        if resp.stop_reason == "refusal":
            raise RuntimeError(f"Claude رفض الطلب: {getattr(resp.stop_details, 'explanation', '')}")
        if resp.stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": resp.content})
            continue
        text = "".join(b.text for b in resp.content if b.type == "text").strip()
        if resp.stop_reason == "max_tokens":
            log.warning("Claude reply was cut off at max_tokens")
        return text
    raise RuntimeError("Claude did not finish its answer after several resumes")


_JSON_BLOCK = re.compile(r"```(?:json)?\s*(\{.*\}|\[.*\])\s*```", re.S)


def _extract_json(text: str) -> Any:
    m = _JSON_BLOCK.search(text)
    candidate = m.group(1) if m else text[text.find("{"): text.rfind("}") + 1]
    return json.loads(candidate)


def ask_json(
    system: str,
    prompt: str,
    schema: type[T],
    *,
    web_search: bool = False,
    effort: str = "high",
    mock: dict | None = None,
) -> T:
    if settings.dry_run:
        if mock is None:
            raise RuntimeError(f"No mock data for {schema.__name__} in dry-run mode")
        return schema.model_validate(mock)

    schema_txt = json.dumps(schema.model_json_schema(), ensure_ascii=False)
    full_prompt = (
        f"{prompt}\n\n"
        "أعد النتيجة النهائية ككائن JSON واحد داخل ```json ... ``` مطابق تماماً لهذا المخطط:\n"
        f"{schema_txt}"
    )
    last_err = ""
    for attempt in range(3):
        p = full_prompt if not last_err else f"{full_prompt}\n\nالمحاولة السابقة فشلت في التحقق: {last_err}\nأصلح الـ JSON."
        text = ask(system, p, web_search=web_search, effort=effort)
        try:
            return schema.model_validate(_extract_json(text))
        except (json.JSONDecodeError, ValidationError, ValueError) as e:
            last_err = str(e)[:1500]
            log.warning("JSON parse failed (attempt %d): %s", attempt + 1, last_err[:200])
    raise RuntimeError(f"Claude did not return valid JSON for {schema.__name__}: {last_err}")

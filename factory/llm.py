"""Thin Claude wrapper. Every caller has a non-LLM fallback, so the factory
still runs (template mode) when ANTHROPIC_API_KEY is missing or offline."""
from __future__ import annotations

import json
import logging
import os
from typing import Any

log = logging.getLogger("llm")


def available() -> bool:
    if not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        return False
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    return True


def json_call(system: str, prompt: str, schema: dict[str, Any], model: str = "claude-opus-5-5",
              effort: str = "medium", max_tokens: int = 16000) -> dict[str, Any]:
    """One structured-output request; returns the parsed JSON object."""
    import anthropic

    client = anthropic.Anthropic()
    response = client.beta.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
        output_config={"effort": effort, "format": {"type": "json_schema", "schema": schema}},
        # If a safety classifier declines, the API re-runs on its recommended fallback model.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    )
    if response.stop_reason == "refusal":
        raise RuntimeError(f"Claude declined the request: {getattr(response, 'stop_details', None)}")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("Claude output was cut off (max_tokens)")
    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)

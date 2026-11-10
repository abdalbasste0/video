"""
Talking to Claude.

Default: the Claude Code CLI  ->  `claude -p "<prompt>"`  (uses your Claude subscription/login)
Optional: the Anthropic API   ->  set llm.provider: anthropic_api and ANTHROPIC_API_KEY in .env

Every answer is cached in cache/llm/ by a hash of the prompt, so re-running a
step that already succeeded costs nothing. Network/CLI errors are retried 3x.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

from .config import CACHE, ROOT, StudioError, settings


def _cache_path(prompt: str, system: str) -> Path:
    h = hashlib.sha1((system + "\n---\n" + prompt).encode("utf-8")).hexdigest()[:24]
    return CACHE / "llm" / f"{h}.txt"


def _claude_cli(prompt: str, system: str, cfg: dict) -> str:
    exe = shutil.which(cfg.get("claude_cli_command", "claude"))
    if not exe:
        raise StudioError("The `claude` command was not found. Install Claude Code (see README) or set "
                          "llm.provider: anthropic_api in config/settings.yaml.")
    cmd = [exe, "-p", "--output-format", "text"]
    if system:
        cmd += ["--append-system-prompt", system]
    r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, encoding="utf-8",
                       timeout=cfg.get("timeout_seconds", 600), cwd=str(ROOT))
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[-300:] or "claude -p failed")
    return r.stdout.strip()


def _anthropic_api(prompt: str, system: str, cfg: dict) -> str:
    try:
        import anthropic
    except ImportError as e:
        raise StudioError("pip install anthropic   (needed for llm.provider: anthropic_api)") from e
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise StudioError("ANTHROPIC_API_KEY is missing in .env")
    client = anthropic.Anthropic()
    msg = client.messages.create(model=cfg.get("anthropic_model", "claude-opus-5-5"),
                                 max_tokens=cfg.get("max_tokens", 16000), system=system or anthropic.NOT_GIVEN,
                                 messages=[{"role": "user", "content": prompt}])
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()


def ask(prompt: str, system: str = "", use_cache: bool = True) -> str:
    cfg = settings()["llm"]
    cp = _cache_path(prompt, system)
    if use_cache and cp.exists():
        return cp.read_text(encoding="utf-8")
    fn = _anthropic_api if cfg.get("provider") == "anthropic_api" else _claude_cli
    last = None
    for i in range(cfg.get("retries", 3)):
        try:
            out = fn(prompt, system, cfg)
            cp.parent.mkdir(parents=True, exist_ok=True)
            cp.write_text(out, encoding="utf-8")
            return out
        except StudioError:
            raise
        except Exception as e:
            last = e
            time.sleep(3 * (i + 1))
    raise StudioError(f"Claude did not answer after {cfg.get('retries', 3)} tries. Last error: {last}")


def ask_json(prompt: str, system: str = "") -> dict | list:
    """Ask for JSON and parse it (strips ``` fences if Claude adds them)."""
    out = ask(prompt + "\n\nReply with valid JSON only, no commentary.", system)
    s = out.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1].rsplit("```", 1)[0]
    try:
        return json.loads(s)
    except json.JSONDecodeError as e:
        _cache_path(prompt + "\n\nReply with valid JSON only, no commentary.", system).unlink(missing_ok=True)
        raise StudioError(f"Claude's answer was not valid JSON ({e}). Run the step again.") from e

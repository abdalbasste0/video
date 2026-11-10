"""
Loads the YAML config files once and gives simple helpers.

Everything path-related is relative to the project root (the folder with make.py),
so you can run `python make.py ...` from that folder on Windows or macOS.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config"
ASSETS = ROOT / "assets"
DATA = ROOT / "data"
OUTPUT = ROOT / "output"
CACHE = ROOT / "cache"


class StudioError(Exception):
    """An error with a plain-language message for the user (no scary traceback)."""


def load_env() -> None:
    """Read keys from .env into os.environ (only if python-dotenv is installed)."""
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except ImportError:
        # Tiny fallback parser so the studio works without python-dotenv.
        env = ROOT / ".env"
        if env.exists():
            for line in env.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _read_yaml(name: str) -> dict:
    path = CONFIG / name
    if not path.exists():
        raise StudioError(f"Missing config file: config/{name}")
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        raise StudioError(f"config/{name} has a typo (YAML error): {e}") from e


@lru_cache(None)
def settings() -> dict:
    return _read_yaml("settings.yaml")


@lru_cache(None)
def languages() -> dict:
    return _read_yaml("languages.yaml")


@lru_cache(None)
def roster() -> dict:
    return _read_yaml("roster.yaml")


@lru_cache(None)
def characters_cfg() -> dict:
    return _read_yaml("characters.yaml")


def language(code: str) -> dict:
    langs = languages()
    if code not in langs:
        raise StudioError(
            f"Language '{code}' is not in config/languages.yaml. "
            f"Available: {', '.join(langs)}. Add a block there to support it."
        )
    lang = dict(langs[code])
    lang["code"] = code
    return lang


def episode_dir(ep_id: str) -> Path:
    d = OUTPUT / ep_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def read_json(path: Path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)  # atomic: never leaves half-written files

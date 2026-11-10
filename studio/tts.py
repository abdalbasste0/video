"""
Text-to-speech with a provider CHAIN per language (config/languages.yaml):

    elevenlabs -> best Arabic, paid (credit budget guard below)
    kokoro     -> free, local, great en/fr/es
    piper      -> free, offline; needs assets/voices/<voice>.onnx (+ .onnx.json)
    espeak     -> free, robotic, last resort for testing

ElevenLabs safety: BEFORE any call we count characters, print the estimated
credits and STOP if this month's usage + estimate > tts.monthly_credit_budget.
Usage is tracked in data/usage.json.

Every generated line is cached in cache/tts/ by a hash of (provider, voice, text),
so re-running never pays twice.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from . import audio
from .config import ASSETS, CACHE, DATA, StudioError, language, read_json, settings, write_json

USAGE = DATA / "usage.json"
_kokoro_pipes: dict = {}


# ── ElevenLabs credit guard ───────────────────────────────────
def _month() -> str:
    return dt.date.today().strftime("%Y-%m")


def usage_this_month() -> float:
    return float((read_json(USAGE, {}) or {}).get(_month(), {}).get("credits", 0))


def _add_usage(chars: int, credits: float):
    u = read_json(USAGE, {}) or {}
    m = u.setdefault(_month(), {"chars": 0, "credits": 0})
    m["chars"] += chars
    m["credits"] = round(m["credits"] + credits, 2)
    write_json(USAGE, u)


def estimate_credits(texts: list[str]) -> tuple[int, float]:
    chars = sum(len(t) for t in texts)
    return chars, chars * float(settings()["tts"].get("credits_per_char", 1.0))


def elevenlabs_budget_check(texts: list[str], log=print) -> None:
    """Call once with ALL lines that will go to ElevenLabs. Raises if over budget."""
    texts = [t for t in texts if not _cached_any("elevenlabs", t)]
    chars, credits = estimate_credits(texts)
    budget = float(settings()["tts"]["monthly_credit_budget"])
    used = usage_this_month()
    log(f"  ElevenLabs estimate: {chars:,} characters ≈ {credits:,.0f} credits "
        f"(used this month: {used:,.0f} / budget {budget:,.0f})")
    if used + credits > budget:
        raise StudioError(
            f"Stopped before calling ElevenLabs: this would use ~{credits:,.0f} credits, but only "
            f"{max(0, budget - used):,.0f} remain of your monthly budget ({budget:,.0f}).\n"
            f"Options: raise tts.monthly_credit_budget in config/settings.yaml, shorten the script, "
            f"or put another provider first in config/languages.yaml (tts.chain)."
        )


# ── helpers ───────────────────────────────────────────────────
def _key(provider, voice, text):
    return hashlib.sha1(f"{provider}|{voice}|{text}".encode("utf-8")).hexdigest()[:20]


def _cached_any(provider, text):
    return any((CACHE / "tts").glob(f"{provider}-*-{hashlib.sha1(text.encode()).hexdigest()[:8]}.wav"))


def _retry(fn, what, tries=None):
    tries = tries or settings()["tts"].get("retries", 3)
    last = None
    for i in range(tries):
        try:
            return fn()
        except StudioError:
            raise
        except Exception as e:  # network hiccup etc.
            last = e
            time.sleep(2 ** i)
    raise RuntimeError(f"{what} failed after {tries} tries: {last}")


# ── providers ─────────────────────────────────────────────────
def available(provider: str) -> tuple[bool, str]:
    """(ok, reason) - used by the chain and by `doctor`."""
    if provider == "elevenlabs":
        return (bool(os.environ.get("ELEVENLABS_API_KEY")), "set ELEVENLABS_API_KEY in .env")
    if provider == "kokoro":
        try:
            import kokoro  # noqa: F401
            return True, ""
        except Exception:
            return False, "pip install kokoro soundfile"
    if provider == "piper":
        try:
            import piper  # noqa: F401
            return True, ""
        except Exception:
            return False, "pip install piper-tts  (and put voice .onnx files in assets/voices/)"
    if provider == "espeak":
        return (bool(shutil.which("espeak-ng") or shutil.which("espeak")), "install espeak-ng (see README)")
    return False, f"unknown provider {provider}"


def _elevenlabs(text, voice, out_mp3: Path):
    import requests
    s = settings()["tts"]

    def call():
        r = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice}",
            params={"output_format": "mp3_44100_128"},
            headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"], "Content-Type": "application/json"},
            json={"text": text, "model_id": s.get("elevenlabs_model", "eleven_multilingual_v2"),
                  "voice_settings": {"stability": 0.45, "similarity_boost": 0.8, "style": 0.25}},
            timeout=120,
        )
        if r.status_code == 401:
            raise StudioError("ElevenLabs rejected the API key (401). Check ELEVENLABS_API_KEY in .env.")
        if r.status_code == 402 or "quota" in r.text.lower():
            raise StudioError("ElevenLabs says your account is out of credits.")
        if r.status_code >= 400:
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
        out_mp3.write_bytes(r.content)

    # the per-call guard (the big check happens once per episode)
    _, credits = estimate_credits([text])
    if usage_this_month() + credits > float(s["monthly_credit_budget"]):
        raise StudioError("ElevenLabs monthly credit budget reached - stopping (see config/settings.yaml).")
    _retry(call, "ElevenLabs")
    _add_usage(len(text), credits)


def _kokoro(text, voice, out_wav: Path):
    import numpy as np
    from kokoro import KPipeline
    lang_code, v = voice.split(":", 1) if ":" in voice else ("a", voice)
    if lang_code not in _kokoro_pipes:
        _kokoro_pipes[lang_code] = KPipeline(lang_code=lang_code)
    chunks = [a for _, _, a in _kokoro_pipes[lang_code](text, voice=v)]
    if not chunks:
        raise RuntimeError("kokoro produced no audio")
    wav = np.concatenate([np.asarray(c, dtype=np.float32) for c in chunks])
    audio.write_wav(out_wav, wav, 24000)


def _piper(text, voice, out_wav: Path):
    import wave
    from piper import PiperVoice
    model = ASSETS / "voices" / f"{voice}.onnx"
    if not model.exists():
        raise RuntimeError(f"piper voice file missing: assets/voices/{voice}.onnx")
    pv = PiperVoice.load(str(model))
    with wave.open(str(out_wav), "wb") as wf:
        if hasattr(pv, "synthesize_wav"):
            pv.synthesize_wav(text, wf)        # piper-tts >= 1.3
        else:
            pv.synthesize(text, wf)            # older piper-tts


def _espeak(text, voice, out_wav: Path):
    exe = shutil.which("espeak-ng") or shutil.which("espeak")
    parts = voice.split(":")
    v, opts = parts[0], dict(p.split("=") for p in parts[1:])
    cmd = [exe, "-v", v, "-p", opts.get("p", "50"), "-s", opts.get("s", "150"), "-w", str(out_wav), text]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not out_wav.exists() or out_wav.stat().st_size < 2000:
        # mbrola voice not installed -> plain espeak voice for the language
        base = v.replace("mb-", "")[:2]
        cmd[2] = base
        subprocess.run(cmd, capture_output=True, text=True, check=True)


PROVIDERS = {"elevenlabs": _elevenlabs, "kokoro": _kokoro, "piper": _piper, "espeak": _espeak}


def synthesize(text: str, lang_code: str, role: str, log=print) -> tuple[Path, str]:
    """
    Speak `text` with the voice for `role` (narrator/hero/ally/antagonist).
    Returns (path to 48 kHz mono wav, provider used). Cached.
    """
    lang = language(lang_code)
    tts = lang.get("tts", {})
    voices = tts.get("voices", {})
    vmap = voices.get(role) or voices.get("narrator")
    errors = []
    for provider in tts.get("chain", ["espeak"]):
        ok, why = available(provider)
        voice = (vmap or {}).get(provider)
        if not ok or not voice:
            errors.append(f"{provider}: {why if not ok else 'no voice set for ' + role}")
            continue
        if provider == "piper" and not (ASSETS / "voices" / f"{voice}.onnx").exists():
            errors.append(f"piper: voice file assets/voices/{voice}.onnx not downloaded")
            continue
        h = f"{provider}-{_key(provider, voice, text)}-{hashlib.sha1(text.encode()).hexdigest()[:8]}"
        final = CACHE / "tts" / f"{h}.wav"
        if final.exists():
            return final, provider
        final.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / ("raw.mp3" if provider == "elevenlabs" else "raw.wav")
            try:
                PROVIDERS[provider](text, voice, raw)
                audio.standardize(raw, final)
                return final, provider
            except StudioError:
                raise
            except Exception as e:
                errors.append(f"{provider}: {e}")
                log(f"    ! {provider} failed, trying next provider ({e})")
    raise StudioError("No voice provider worked for this line.\n  " + "\n  ".join(errors) +
                      "\nRun `python make.py doctor` to see what to install.")

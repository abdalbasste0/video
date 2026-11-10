"""
`python make.py doctor` - checks everything and explains how to fix problems.
✅ = good   ⚠️ = optional / works with fallback   ❌ = must fix
"""
from __future__ import annotations

import importlib
import shutil
import subprocess
import sys

from . import poses, tts
from .config import ASSETS, OUTPUT, ROOT, StudioError, languages, roster, settings
from .text import draw_text, is_shaped_arabic, missing_glyphs, shape

OK, WARN, BAD = "✅", "⚠️ ", "❌"


def run(log=print) -> bool:
    problems = 0

    def say(icon, msg, fix=""):
        nonlocal problems
        if icon == BAD:
            problems += 1
        log(f"{icon} {msg}" + (f"\n     → {fix}" if fix else ""))

    log("── Basics")
    v = sys.version_info
    say(OK if v >= (3, 10) else BAD, f"Python {v.major}.{v.minor}", "" if v >= (3, 10) else "Install Python 3.10+ (README)")
    for exe in ("ffmpeg", "ffprobe"):
        p = shutil.which(exe)
        if p:
            ver = subprocess.run([exe, "-version"], capture_output=True, text=True).stdout.split("\n")[0][:60]
            say(OK, f"{exe}: {ver}")
        else:
            say(BAD, f"{exe} not found", "Install FFmpeg and make sure it is on PATH (README step 2)")
    for mod, pkg in [("PIL", "pillow"), ("numpy", "numpy"), ("yaml", "pyyaml"), ("requests", "requests"),
                     ("arabic_reshaper", "arabic-reshaper"), ("bidi", "python-bidi")]:
        try:
            importlib.import_module(mod)
            say(OK, f"python package {pkg}")
        except ImportError:
            say(BAD, f"python package {pkg} missing", "pip install -r requirements.txt")
    for mod, pkg, why in [("dotenv", "python-dotenv", "reads .env (a fallback reader is built in)"),
                          ("faster_whisper", "faster-whisper", "word-accurate captions (fallback: timed from script)")]:
        try:
            importlib.import_module(mod)
            say(OK, f"python package {pkg}")
        except ImportError:
            say(WARN, f"optional {pkg} not installed - {why}", f"pip install {pkg}")

    log("── Config")
    try:
        s = settings()
        say(OK, f"settings.yaml  ({s['video']['width']}x{s['video']['height']} @ {s['video']['fps']} fps)")
        r = roster()
        roles, depts = r["roles"], r["departments"]
        ids = [x["id"] for x in roles]
        per = {d["key"]: sum(1 for x in roles if x["department"] == d["key"]) for d in depts}
        good = len(roles) == 100 and len(set(ids)) == 100 and len(depts) == 10 and all(n == 10 for n in per.values())
        say(OK if good else BAD, f"roster.yaml: {len(roles)} roles, {len(depts)} departments",
            "" if good else f"Need exactly 100 unique roles, 10 per department. Counts: {per}")
        missing_agents = [d["key"] for d in depts if not (ROOT / ".claude" / "agents" / f"{d['key']}.md").exists()]
        say(OK if not missing_agents else BAD, "10 department-head agents in .claude/agents/",
            f"missing: {missing_agents}" if missing_agents else "")
    except StudioError as e:
        say(BAD, str(e))

    log("── Poses")
    try:
        lib = poses.library()
        say(OK if len(lib) >= 25 else BAD, f"{len(lib)} poses in assets/poses/ (need 25+)")
    except Exception as e:
        say(BAD, f"pose library: {e}")

    log("── Languages, fonts & text")
    sample = {"ar": "اليوم الأول: من أطفأ الضوء؟", "en": "Day 1: Who turned off the light?",
              "fr": "Jour 1 : Qui a éteint la lumière ?", "es": "Día 1: ¿Quién apagó la luz?"}
    from PIL import Image
    (OUTPUT / "_doctor").mkdir(parents=True, exist_ok=True)
    for code, lang in languages().items():
        lang = dict(lang, code=code)
        txt = sample.get(code, lang.get("name", code))
        try:
            for key in ("font", "font_body"):
                shaped = shape(txt, lang["direction"])
                miss = missing_glyphs(lang[key], shaped)
                if miss:
                    say(BAD, f"{code}: {lang[key]} cannot draw {''.join(miss)!r}", "Choose a font that covers this language")
            if lang["direction"] == "rtl":
                ok = is_shaped_arabic(shape(txt, "rtl"))
                say(OK if ok else BAD, f"{code}: Arabic reshaping + bidi works", "" if ok else "pip install arabic-reshaper python-bidi")
            img = Image.new("RGB", (960, 200), (20, 22, 34))
            draw_text(img, (480, 100), txt, lang, 54, stroke=3)
            p = OUTPUT / "_doctor" / f"text_{code}.png"
            img.save(p)
            say(OK, f"{code} ({lang['english_name']}): {lang['direction']}, {lang['words_per_minute']} wpm, "
                    f"sample frame → {p.relative_to(ROOT)}")
        except Exception as e:
            say(BAD, f"{code}: {e}")

    log("── Voices (TTS)")
    for prov in ("elevenlabs", "kokoro", "piper", "espeak"):
        ok, why = tts.available(prov)
        say(OK if ok else WARN, f"{prov}: {'ready' if ok else 'not available'}", "" if ok else why)
    voices_dir = ASSETS / "voices"
    for code, lang in languages().items():
        chain = lang["tts"]["chain"]
        usable = [p for p in chain if tts.available(p)[0]]
        if "piper" in usable:
            need = {v.get("piper") for v in lang["tts"]["voices"].values() if v.get("piper")}
            have = [n for n in need if (voices_dir / f"{n}.onnx").exists()]
            if not have:
                usable.remove("piper")
        if usable:
            say(OK if usable[0] == chain[0] else WARN, f"{code}: will speak with {usable[0]} (chain {' → '.join(chain)})",
                "" if usable[0] == chain[0] else f"best quality needs {chain[0]}: {tts.available(chain[0])[1]}")
        else:
            say(BAD, f"{code}: no TTS provider available (chain {' → '.join(chain)})", "Install one (README step 5)")
    used, budget = tts.usage_this_month(), settings()["tts"]["monthly_credit_budget"]
    say(OK, f"ElevenLabs credits used this month: {used:,.0f} / {budget:,}")

    log("── LLM")
    cfg = settings()["llm"]
    if cfg["provider"] == "claude_cli":
        p = shutil.which(cfg.get("claude_cli_command", "claude"))
        say(OK if p else WARN, f"claude CLI {'found' if p else 'not found'}", "" if p else "Install Claude Code: npm i -g @anthropic-ai/claude-code")
    else:
        import os
        k = bool(os.environ.get("ANTHROPIC_API_KEY"))
        say(OK if k else BAD, "ANTHROPIC_API_KEY " + ("set" if k else "missing"), "" if k else "add it to .env")

    log("── Assets & licenses")
    from .audio import unlicensed_assets
    bad = unlicensed_assets()
    if bad:
        for b in bad:
            say(BAD, f"no license file for {b.relative_to(ROOT)}", f"create {b.name}.license.txt (source + license)")
    else:
        n = sum(1 for f in (ASSETS / "music").glob("*") if not f.name.endswith(".txt")) + \
            sum(1 for f in (ASSETS / "sfx").glob("*") if not f.name.endswith(".txt"))
        say(OK, f"all {n} music/sfx files have .license.txt")
    img_cfg = settings()["images"]
    say(OK, f"image provider: {img_cfg['provider']} (max {img_cfg['max_images_per_episode']} per episode)")

    free = shutil.disk_usage(ROOT).free / 1e9
    say(OK if free > 5 else WARN, f"free disk: {free:.1f} GB", "" if free > 5 else "A 15-min episode needs ~3-5 GB while rendering")
    log("")
    log("All good! ✨" if problems == 0 else f"{problems} problem(s) to fix (❌ above).")
    return problems == 0

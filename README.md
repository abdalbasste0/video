# Stickman Mystery Studio 🎬

**مصنع فيديوهات غموض بشخصيات ستيكمان — 100 موظف روبوت في 10 أقسام.**
تختار اللغة قبل إنشاء الفيديو (عربي، إنجليزي، فرنسي، إسباني… ويمكن إضافة لغات أخرى)،
والقصة تُكتب مباشرة بتلك اللغة (بدون ترجمة). كل شيء يُرسم بالكود: لا محرر مدفوع.
المشروع **لا يرفع أي شيء على يوتيوب** — أنت تشاهد وتوافق ثم ترفع بنفسك.

A Python pipeline that produces **original** 15-minute stickman mystery/survival videos (1920×1080, 24 fps).
One command runs everything. Every step is cached, so stopping and re-running never repeats paid work.

---

## Build progress

| Step | What | Status |
|------|------|--------|
| 1 | Skeleton, `doctor`, `roster` (100 roles, 10 department heads) | ✅ done |
| 2 | Rig demo: 20 s clip, two stickmen walking + talking (Arabic & English) | ✅ done — **waiting for your feedback** |
| 3 | Departments wired one by one (Story Room → Packaging) | next |
| 4 | 2-minute pilot of E001, then full 15 minutes | later |

---

## Setup (do this once)

### 1. Install Python 3.10 or newer
- **Windows:** download from <https://www.python.org/downloads/> → run the installer → ✅ tick **"Add python.exe to PATH"**.
- **macOS:** install Homebrew (<https://brew.sh>), then in Terminal: `brew install python`

Check: open a terminal (Windows: *PowerShell*, macOS: *Terminal*) and type `python --version`
(on macOS you may need `python3` instead of `python` everywhere below).

### 2. Install FFmpeg (turns our frames into video)
- **Windows:** `winget install Gyan.FFmpeg` (then close and reopen PowerShell)
- **macOS:** `brew install ffmpeg`

Check: `ffmpeg -version`

### 3. Get the project and install the Python packages
```bash
cd path/to/this/folder
python -m venv .venv
# Windows:            .venv\Scripts\activate
# macOS:              source .venv/bin/activate
pip install -r requirements.txt
```
(The `.venv` is a private box for this project's packages. Activate it each time you open a new terminal.)

### 4. Keys (only what you use)
Copy `.env.example` to `.env` and fill in:
- `ELEVENLABS_API_KEY` — best Arabic voice (paid). The studio counts characters and **stops before going over**
  `tts.monthly_credit_budget` in `config/settings.yaml`. Usage is saved in `data/usage.json`.
- `ANTHROPIC_API_KEY` — only if you switch `llm.provider` to `anthropic_api`.
  By default the studio uses **Claude Code** (`claude -p`), install it with `npm i -g @anthropic-ai/claude-code`.

### 5. Voices (pick at least one free one)
| Provider | Languages | Install |
|----------|-----------|---------|
| ElevenLabs | Arabic (default) + all | key in `.env` |
| Kokoro | en / fr / es (default) | `pip install kokoro soundfile` |
| Piper | free offline fallback | `pip install piper-tts`, then put voice files (e.g. `ar_JO-kareem-medium.onnx` + `.onnx.json`) from <https://huggingface.co/rhasspy/piper-voices> into `assets/voices/` |
| eSpeak NG | robotic, testing only | Windows: installer from <https://github.com/espeak-ng/espeak-ng/releases> · macOS: `brew install espeak-ng` |

The order each language tries them is `tts.chain` in `config/languages.yaml`.

### 6. Check everything
```bash
python make.py doctor
```
✅ = good, ⚠️ = optional/fallback works, ❌ = must fix (it tells you how).
It also writes a sample text frame per language to `output/_doctor/` so you can see Arabic is shaped correctly.

---

## Commands

```bash
python make.py doctor                          # check Python, FFmpeg, fonts, voices, keys
python make.py roster                          # the 100 roles + last run status
python make.py demo --lang ar en               # 20 s rig test clip(s) → output/_demo/
python make.py episode --id E001 --lang ar     # full pipeline
python make.py episode --id E001               # no --lang → asks you to choose
python make.py review --id E001 --approve      # approve the script (after reading review.md)
python make.py review --id E001 --reject "the twist is too obvious"
python make.py review --id E001 --final-approve
python make.py status --id E001
python -m pytest -q                            # tests (pip install pytest)
```

## How an episode flows

```
Story Room → Characters → Script → Fact & Logic ──► review.md  ⏸ YOU approve
   → Storyboard → Art → Animation → Sound → Quality Control ──► (rework max 2×, then flags you)
   → Packaging ──► final.mp4 + captions.srt + thumbnail  ⏸ YOU watch, then --final-approve
```
- A department cannot start until the previous one passed.
- Each department is **one** head agent (`.claude/agents/<department>.md`) that works through its 10 role cards
  from `config/roster.yaml` as checklist stages and writes `output/<id>/reports/<department>.md`.
- Nothing renders until you approve the script.

## Language freedom

`config/languages.yaml` holds, per language: direction (rtl/ltr), fonts, TTS chain + voices per role,
words-per-minute (used to hit 15:00), and caption style. To add a language, copy a block and change it,
then run `doctor`.

Arabic text is shaped with **arabic-reshaper + python-bidi** before drawing. The Arabic font must contain
"presentation form" glyphs (Noto Sans Arabic does; `doctor` checks this). In Arabic episodes, characters
travel right→left so "forward" matches the reading direction.

## Quality bar (QC)

Each scored 1–10, anything below 8 goes back for rework: story clarity, mystery fairness, pacing (no static
screen > 8 s), animation smoothness, character distinguishability, audio clarity, sync, text readability,
originality (similarity to `data/history.jsonl` must be < 0.6).

## Sounds & licenses

Music and SFX come **only** from `assets/music` and `assets/sfx`, and each file needs a
`<file>.license.txt` next to it (source + license). The renderer refuses files without one.
The demo creates a few sounds by code (CC0) so it works out of the box.

## Folder map

```
make.py                  the one command
config/                  settings, languages, roster (100 roles), characters (colors/accessories)
.claude/agents/          10 department heads
studio/                  the engine
  rig.py poses.py        stickman skeleton, faces, accessories, pose library + easing
  shots.py render.py     shot format, camera, parallel rendering → FFmpeg, shot cache
  backgrounds.py effects.py   code-drawn parallax places, flashlight/darkness/alarm/rain/fog
  tts.py audio.py captions.py voices + credit guard, mixing/ducking/-14 LUFS, .srt
  llm.py queue.py qc.py  Claude calls (cached), episode state & gates, QC checks
assets/poses/            39 poses (JSON, editable by hand)
assets/fonts/            OFL fonts (see assets/fonts/README.md)
data/                    episodes.csv, history.jsonl, usage.json
output/<id>/             everything for one episode
```

## When something goes wrong

Errors are written in plain language with the fix. Re-running the same command continues where it stopped
(voices, LLM answers and rendered shots are cached in `cache/`). Delete `cache/` to force a full redo.

# 🎬 Video Factory — multi-agent short-video production with CapCut drafts

Idea in → script, voice, footage, edit, captions, color, VFX, and sound → a **CapCut Desktop draft** plus a rendered MP4 → **you approve on Telegram** → it gets published.

> **Golden rule:** nothing is ever published without your explicit ✅.
> A finished video stays `PENDING_APPROVAL` until you decide, however long that takes.
> There is no auto-publish setting, flag, or code path (see [The approval gate](#the-approval-gate)).

---

## 1. Architecture

```
                         ┌────────────────────── you (Telegram / phone widget / CLI) ─────────────────────┐
                         │ /new "idea"                                         ✅ Publish ✏️ Revise ❌ Reject │
                         ▼                                                                  ▲            │
┌──────────────────────────────────────────── ORCHESTRATOR ─────────────────────────────────┼────────────┼─┐
│  queue + status (SQLite: PENDING/RUNNING/DONE/FAILED) · retries · resume after crash      │            │ │
│                                                                                           │            ▼ │
│  Script ──► ┌ Voice  (TTS + word timestamps) ┐                                    Approval Agent  Revise │
│             └ Assets (clips, music, SFX)     ┘  ← run in parallel                  (notify + WAIT)   notes│
│                         │                                                                ▲          │   │
│                         ▼              DRAFT BUILD (timeline.json)                        │          │   │
│        Editor ─► Motion ─► Colorist ─► VFX ─► Sound ─► draft_builder ─► QA(draft) ─► Render ─► QA(export)
│          ▲         ▲         ▲         ▲       ▲            │              │                          │   │
│          └─────────┴─────────┴─────────┴───────┴── QA failure / your note is routed ONLY to the ─────┘   │
│                                                    responsible agent (max 3 QA retries)                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                         │ only after ✅ + 🚀 confirm by YOUR Telegram id
                         ▼
                   Publisher Agent ──► YouTube API · TikTok / Instagram (file + caption handed to you)
```

**How the agents connect.** Every agent reads and writes files in `projects/{video_id}/`. The draft-build agents enrich one engine-neutral `draft/timeline.json`, measured in seconds. That timeline is then compiled two ways:

* `factory/capcut/draft_builder.py` → **CapCut draft**: `draft_content.json`, `draft_meta_info.json`, and `materials/`. Times are in µs. It contains tracks, segments, keyframes (Ken Burns scale/position, text scale/position, volume ducking), Adjust effects, a filter adjustment layer, effect tracks, text animations, transitions, and audio fades.
* `factory/agents/render_agent.py` → **FFmpeg render** of the same timeline, used on the phone or when CapCut isn't available. It does Ken Burns, Adjust via `eq`, LUT, VFX, xfade transitions, karaoke captions (RTL), ducking keyframes, SFX, and loudness normalisation to −14 LUFS.

| # | Agent | File | Does |
|---|---|---|---|
| 1 | Orchestrator | `factory/orchestrator.py` | pipeline, parallel Voice ∥ Assets, retries, QA routing, revision routing, resume |
| 2 | Script | `agents/script_agent.py` | Claude writes a hook in the first 3 s, then scenes with duration, visual, search query, and keywords (template fallback) |
| 3 | Voice | `agents/voice_agent.py` | edge-tts (Arabic/English) + `timestamps.json` per sentence and word |
| 4 | Assets | `agents/assets_agent.py` | Pexels clips/photos, then `library/`, then generated; `s01_main.mp4`, `music_01`, `sfx_whoosh` |
| 5 | Editor | `agents/editor_agent.py` | 1080×1920 / 1920×1080 @ 30 fps, cuts on voice timing, rhythm cuts, transitions, Ken Burns |
| 6 | Motion | `agents/motion_agent.py` | hook title, synced captions with keyword highlight, lower thirds, In/Out/Loop animations, RTL |
| 7 | Colorist | `agents/colorist_agent.py` | per-clip Adjust with exposure matching across shots, plus one channel look (filter or `.cube` LUT) |
| 8 | VFX | `agents/vfx_agent.py` | grain, vignette, light leak, etc. at subtle intensity |
| 9 | Sound | `agents/sound_agent.py` | voice normalisation, music ducking keyframes, fades, transition SFX |
| 10 | QA | `agents/qa_agent.py` | gaps, cut-off audio, caption-vs-speech match, safe zone, duration, draft JSON integrity, export resolution/fps/LUFS |
| 11 | Render | `agents/render_agent.py` | `ffmpeg` / `capcut_ui` / `manual` backends, preview copy + thumbnail |
| 12 | Approval | `agents/approval_agent.py` + `factory/approval_bot.py` | "Task complete" message, preview, QA report, buttons |
| 13 | Publisher | `agents/publisher_agent.py` | runs only after it verifies your approval itself |

---

## 2. The sample draft to create in CapCut

The builder can copy the exact JSON of **your** CapCut version (*template mode*). Make this one draft by hand, once:

1. CapCut Desktop → **New project** → set ratio **9:16**, **30 fps**. Name it **`FactorySample`**.
2. Import **2 photos and 1 short video clip**. Put them on the main track back to back.
3. Add a **transition** between clip 1 and clip 2. Use the one you want as your default, e.g. *Dissolve*.
4. On clip 1, add **2 keyframes**: scale 100% at the start, 115% at the end (this is Ken Burns).
5. On clip 2, open **Adjust** and move Brightness, Contrast, Saturation, Temperature, Highlights, and Shadows (any values).
6. Add a **Filter** from the Filters panel and stretch it over the whole timeline (your channel look).
7. Add 1–2 **Effects** you like (Film grain, Vignette, …) on the effect track.
8. Add a **Text** layer: your caption font, stroke, and background. Add an **In** animation, an **Out** animation, and a **Loop** animation. Add one more text in **Arabic**.
9. Add **music**, lower its volume, add 2 **volume keyframes**, and add a fade in/out. Add one **sound effect**.
10. Close the project so CapCut saves it.

Then run:

```bash
python main.py learn-draft "%LOCALAPPDATA%/CapCut/User Data/Projects/com.lveditor.draft/FactorySample"
```

This does three things:

* tells you right away whether your CapCut **encrypts** drafts,
* prints the structure (tracks, materials, keyframe property names) and saves it to `learned_draft_structure.json`,
* fills `effects_library.json` with the real **resource IDs** of your transitions, effects, filters, and text animations.

Then set `capcut.template_draft:` in `config.yaml` to that folder.

> Until IDs are learned, any effect whose `resource_id` is `null` is **skipped**, so the draft always opens. QA lists what was skipped as a warning. The FFmpeg render still applies its own version of each effect.

### 2b. If your CapCut encrypts drafts

Recent CapCut releases may store `draft_content.json` encrypted. `learn-draft` detects this from the file's byte entropy. You have three options:

* **A — older CapCut (recommended for full drafts):** install an older CapCut Desktop that still writes plain JSON. Community reports point to the 5.x line. Turn off auto-update, then recreate `FactorySample`.
* **B — keep your CapCut, render with FFmpeg:** set `render.backend: ffmpeg`. You get the finished video without CapCut. Drafts are still produced for any compatible install.
* **C — template workflow:** keep one unencrypted *template* draft per format and let the builder fill it (template mode above).

---

## 3. Setup from scratch

### A) Windows PC (CapCut Desktop)

```powershell
# 1. Install Python 3.10+ (python.org, tick "Add to PATH") and FFmpeg (winget install Gyan.FFmpeg)
git clone -b claude/capcut-video-factory-system-su2b6s https://github.com/abdalbasste0/video.git
cd video
pip install -r requirements.txt
pip install pywinauto pyautogui            # only for render.backend: capcut_ui
copy .env.example .env                     # then edit .env (see "Keys" below)
python main.py doctor                      # checks FFmpeg, keys, CapCut drafts folder
python main.py learn-draft "<path to FactorySample>"   # section 2
python main.py run "3 morning habits that change your day" --lang en   # first test video
powershell -ExecutionPolicy Bypass -File windows\create_desktop_shortcut.ps1
```

The last command puts **Video Factory** and **New Video** shortcuts on your desktop and registers the factory to start automatically at logon. The `.bat` file restarts it if it ever exits.

Render backend on Windows (`render.backend` in `config.yaml`):
* `manual` (default): the draft appears in CapCut. You press **Export** and the factory picks up the file.
* `capcut_ui`: fully automatic. Needs the screenshots described in `windows/ui/README.md`.
* `ffmpeg`: no CapCut involvement.

### B) Android phone (Termux) — runs non-stop, with buttons on your home screen

1. Install **Termux**, **Termux:Widget**, **Termux:Boot**, and **Termux:API** from **F-Droid**. The Play Store versions are outdated.
2. In Termux:
   ```bash
   pkg install -y git
   git clone -b claude/capcut-video-factory-system-su2b6s https://github.com/abdalbasste0/video.git ~/video
   bash ~/video/phone/termux_setup.sh
   nano ~/video/.env            # paste TELEGRAM_BOT_TOKEN, TELEGRAM_OWNER_ID, keys
   ```
   (If the repo is private, use `git clone https://<token>@github.com/...`, or copy the folder to the phone.)
3. **Home screen:** long-press the home screen → *Widgets* → **Termux:Widget** → place it. It shows:
   * **🎬 Video Factory** — starts the always-on factory in the background
   * **➕ New Video** — type an idea and pick 9:16 or 16:9. It's queued, and you get the result on Telegram
   * **📊 Factory Status** and **⏹ Stop Factory**
4. **So it never stops:**
   * Android Settings → Apps → **Termux** (and Termux:Boot / Termux:API) → Battery → **Unrestricted**.
   * Open **Termux:Boot** once. The factory then restarts by itself after every phone reboot.
   * `phone/start_forever.sh` holds a wake-lock and shows an ongoing notification. It restarts the daemon if it crashes, and kills and restarts it if the heartbeat goes stale for 5 minutes.
   * If the network drops, the Telegram bot backs off and reconnects. Unfinished videos resume from the last completed step.

On the phone, the video is rendered with **FFmpeg**, since CapCut Desktop doesn't run on Android. The CapCut draft is still built and zipped (`projects/<id>/draft/*.zip`). To edit it on your PC, run `python main.py install-draft <zip>`, which copies it into CapCut's drafts folder and fixes the media paths.

### Keys (`.env`)

| Key | Where to get it | Needed? |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Telegram → **@BotFather** → `/newbot` | yes (approval) |
| `TELEGRAM_OWNER_ID` | Telegram → **@userinfobot** → your numeric id | yes; **only this id can approve** |
| `ANTHROPIC_API_KEY` | console.anthropic.com | recommended (real scripts + smart revision routing) |
| `PEXELS_API_KEY` | pexels.com/api | optional (stock footage; otherwise uses `library/` or generated backgrounds) |
| `YOUTUBE_CLIENT_SECRETS` | Google Cloud → OAuth client (Desktop) → `client_secret.json` | optional (direct YouTube upload) |

Put your own music in `library/music/`, SFX in `library/sfx/`, fonts in `library/fonts/`, LUTs in `library/luts/`, and fallback images or clips in `library/images/`.

---

## 4. Daily use

* Telegram: `/new 5 أخطاء شائعة في شرب القهوة`. Add `16:9` for YouTube landscape or `en` for English. `/status` and `/list` show progress.
* When a video is done you receive the **thumbnail, a preview, and a "✅ Task complete"** message. It shows duration, resolution, LUFS, suggested platform, title, description, hashtags, the QA report, and the **CapCut draft name**.
  * **✅ Publish** → tick platforms → **🚀 Confirm publish**. YouTube uploads directly. For TikTok and Instagram you receive the approved file plus a ready caption to post. Their content-posting APIs require an approved developer app, which you can add later.
  * **✏️ Revise** → write notes, e.g. `ألوان أدفأ والموسيقى أخفض`. The Orchestrator routes each note **only** to the responsible agent (colors → Colorist, music → Sound, captions → Motion, …), rebuilds, re-renders, and sends you the new version for approval.
  * **❌ Reject** → the video is closed and can never be published.
* CLI equivalents: `python main.py decide <id> publish --platforms youtube`, `… revise --notes "…"`, `… reject`.

### The approval gate

* `state.py` refuses to set `APPROVED`, `PUBLISHING`, or `PUBLISHED` unless an `APPROVE` decision is recorded.
* `owner_decide()` accepts a decision only while the video is `PENDING_APPROVAL`, and only from your Telegram id. Taps from other users are ignored.
* `assert_owner_approval()` runs inside the Publisher itself. It checks three things: the latest decision is `APPROVE`, it was made by the owner, and the **SHA-256 of the file matches the approved render**. A revision therefore invalidates an older approval.
* `tests/test_golden_rule.py` proves all of this. Run it with `python tests/test_golden_rule.py`.

### Folder layout

```
projects/{video_id}/script/   script.json
                   voice/    s01.wav … voice.wav, timestamps.json
                   assets/   s01_main.mp4|jpg, music_01.*, sfx_whoosh.*, assets.json
                   draft/    timeline.json (+ draft zip on the phone)
                   renders/  final.mp4, preview.mp4, thumbnail.jpg
                   logs/     script.log, voice.log, … qa_report.json, approval_request.json
```

---

## 5. MVP status and next improvements

**Tested in the development container:**
* the offline pipeline end to end, producing a 1080×1920 / 30 fps / −14 LUFS MP4 with both QA stages passing;
* a revision routed to the Colorist only and re-rendered;
* the draft re-read by the inspector and relinked by `install-draft`;
* the golden-rule tests.

**Not yet tested:**
* opening a generated draft inside a real CapCut (needs your Windows PC and your `FactorySample`);
* the Telegram bot against a real bot token;
* edge-tts, Pexels, and Claude calls with real keys;
* `capcut_ui` export automation;
* the Termux scripts on a real phone.

Suggested next steps:
1. Run `learn-draft` on your sample and use template mode. This is the most important step for drafts that open cleanly.
2. Word-level captions in CapCut as separate segments per word (CapCut-native karaoke).
3. Whisper alignment on the final voice for even tighter caption sync.
4. Beat detection on the music to snap cuts to the beat (true rhythm editing).
5. Official TikTok Content Posting API and Instagram Graph API publishing once your developer apps are approved.
6. A/B hooks: generate 2 hooks, render both previews, and you pick one in Telegram.
7. Per-channel style presets (several `config.yaml` profiles) and a weekly content calendar.

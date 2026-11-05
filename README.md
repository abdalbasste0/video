# 🏭 Automated Video Factory: stickman stories, mystery, and riddles

A system of **9 bots** that produces one complete video every day **with an English voice-over**,
and publishes it to **YouTube, TikTok and Instagram**. Work starts at **08:00** and the video is published **before 13:00**.
**Nothing moves to the next step and nothing is published without the owner's approval.**

## 🖥️ The private app and the desktop shortcut (quickest way)

The factory is a **private app just for you**: a control panel that opens in your browser, runs on your own computer only
(`127.0.0.1`, so no other device can reach it), and is protected by a password you set the first time you run it.

**Easiest way: one file on your desktop** — download the file for your system from the `launchers/` folder and put it on your desktop:
- Windows: `launchers/VideoFactory-Windows.bat`
- Mac: `launchers/VideoFactory-Mac.command`

Double-click it: the first time it installs everything (Git, Python, FFmpeg, the project and its libraries) and creates the
«مصنع الفيديو» icon. After that, every time you open it, it updates the project automatically and opens the app.

**Or create the desktop shortcut by hand (once):**
```bash
python -m factory shortcut
```
An «مصنع الفيديو» (Video Factory) icon appears on your desktop (Windows / Mac / Linux). Double-click it and the app opens.
Leave the app open (or minimised), and the factory starts by itself at 08:00.

**What you can do in the app:**
| Tab | Contents |
|---------|----------|
| Today | Stage progress live, which helper bot is assisting, and **approval cards**: pick an idea · review the script and date checks · watch the final video (landscape + vertical) with the QA report, then **choose the platforms** and approve publishing |
| Commands | Send instructions to bot 9 in plain Arabic, plus quick buttons (stickman / mystery / riddles / pause / resume / cancel) |
| Publishing | Platform status, links to what was published, retry failed platforms, and publish late with your approval |
| History | Every published video with its links |
| Settings | Enter all your keys (secret keys are never shown after saving) and change the password |

You can also open it without the shortcut: `python -m factory app`, then go to `http://127.0.0.1:8765`.

## 👥 The team

| # | Bot | Role | File |
|---|-----|------|------|
| 1 | Trend scout | Searches the web for viral topics in the category (YouTube/TikTok/Google Trends/anniversaries) and ranks them | `factory/bots/trend_scout.py` |
| 2 | Script writer | Writes the script, extracts every date, time, and number, **checks each one** with a web search, then does a professional edit | `factory/bots/script_writer.py` |
| 3 | Voice-over | Turns each scene into **English** narration with **ElevenLabs** (keeps the voice continuous between scenes) | `factory/bots/voice.py` |
| 4 | Media hunter | Fetches videos/images from Pexels and Pixabay, or draws stickman frames, and logs each clip's source | `factory/bots/media_hunter.py` |
| 5 | Editor | Crop/zoom (Ken Burns), subtitles, transitions, background music with automatic ducking, -14 LUFS loudness, thumbnail, plus a **vertical 9:16 version** for TikTok and Instagram | `factory/bots/editor.py` |
| 6 | QA | Checks sync, resolution, black frames, silence, loudness, plus an editorial review of the content and a preview board | `factory/bots/qa.py` |
| 7 and 8 | Helpers on call | Stay idle until called. When a bot falls behind schedule or fails, they join it and take over part of its work in parallel | `factory/bots/helpers.py` |
| 9 | Manager | Receives your instructions, assigns each bot its task, watches the schedule, calls the helpers, asks for your approval, and publishes after your approval | `factory/bots/manager.py` |

## ⏰ Daily schedule (`factory/config.py`)

| Deadline | Stage | Your approval |
|--------|---------|-------------|
| 08:00 | Work starts | — |
| 08:40 | Viral idea research | ✅ You pick the idea number |
| 09:30 | Script + date and time checks | ✅ Approve or send changes |
| 10:00 | Voice-over | — |
| 10:40 | Videos and images | — |
| 11:40 | Editing | — |
| 12:00 | QA | — |
| 12:45 | The final video is shown to you (video + thumbnail + title + description + QA report) | ✅ Approve publishing or send changes |
| 12:55 | Publishing to YouTube + TikTok + Instagram | Only after your approval, and only to the platforms you pick |

**How helpers 7 and 8 get called:** once a stage has used 60% of its time and completed less than that share of its work,
or its work units fail, the manager calls helper 7. Past 85% (or when retrying after a failure) it also calls helper 8.
Every bot's work is split into small units (scenes / searches / checks) on a shared board, so the helpers
pull the remaining units and finish them in parallel.

**The publishing rule:** if your final approval arrives after 13:00, the bot does **not** publish automatically. It
tells you instead. To publish anyway: `python -m factory publish --late`.

## 🗣️ Video language
The voice-over, subtitles, title and description are in **English** (`FACTORY_LANGUAGE=en`), while every message to you
(the app, Telegram, approvals) stays in Arabic. Pick an English voice in ElevenLabs and put its ID in `ELEVENLABS_VOICE_ID`.
To switch back to Arabic: `FACTORY_LANGUAGE=ar`.

## 📤 Publishing to the three platforms
| Platform | Which version | What you need |
|--------|--------------|-------------|
| YouTube | The main video (landscape) + thumbnail | `YOUTUBE_CLIENT_ID/SECRET/REFRESH_TOKEN` |
| TikTok | The vertical 9:16 version | A TikTok for Developers app with the Content Posting API: `TIKTOK_CLIENT_KEY/SECRET/REFRESH_TOKEN`. **Until TikTok approves your app it only allows private posts** (`TIKTOK_PRIVACY=SELF_ONLY`); after approval, set `PUBLIC_TO_EVERYONE` |
| Instagram | The vertical version as a Reel | An Instagram Business or Creator account linked to a Facebook page, plus a Meta app with the `instagram_content_publish` permission: `IG_USER_ID` + a long-lived `IG_ACCESS_TOKEN` |

Each platform publishes separately: if one fails, the others still go out, and you see the reason in the app and can retry it.
On Telegram you can name the platforms in your approval: `موافق يوتيوب تيكتوك` ("approve YouTube TikTok"). A plain `موافق` ("approve") publishes to every enabled platform.

## 💬 Talking to the factory

### Through Telegram (recommended)
Once `TELEGRAM_BOT_TOKEN` and `TELEGRAM_OWNER_CHAT_ID` are set, the factory sends you every step and you reply in plain words:
- Picking an idea: `موافق 2` ("approve 2") or just `2`
- Approving: `موافق` ("approve") / `تمام` ("OK") / `انشر` ("publish")
- Asking for changes: `رفض: اجعل البداية أقوى والقصة أقصر` ("reject: make the opening stronger and the story shorter")
- Instructions for the manager (anytime, even the night before):
  `اليوم قصة ستيك مان عن النجاح بعد الفشل، مدتها 5 دقائق` ("today a stickman story about success after failure, 5 minutes long")
  `البوت الرابع استخدم لقطات ليلية فقط` ("bot 4, use night footage only")
  `الحالة` ("status") · `توقف` ("pause") · `استمر` ("resume") · `إلغاء` ("cancel") · `ابدأ الآن` ("start now")

If you ask for changes on the final video, the manager works out which stage the note belongs to (script / voice /
footage / editing), applies it, redoes only what is needed, and shows you the video again.

### Through the command line
```bash
python -m factory command "اليوم لغز بوليسي"      # an instruction for bot 9 ("today a detective riddle")
python -m factory status                           # today's status
python -m factory approve research 2               # pick idea 2
python -m factory approve script
python -m factory reject script "الخاتمة ضعيفة"    # "the ending is weak"
python -m factory approve final                    # approve publishing to every platform
python -m factory approve final youtube,tiktok     # approve publishing to specific platforms
python -m factory publish --platforms instagram    # retry one platform
```

## 🚀 Setup

```bash
sudo apt install ffmpeg            # needs ffmpeg with libass (included in standard builds)
pip install -r requirements.txt
cp .env.example .env               # then fill in the keys
```

Required keys in `.env`:
- `ANTHROPIC_API_KEY`: Claude, for research, writing, checking, and review (`claude-opus-5-5` with web search)
- `ELEVENLABS_API_KEY` and `ELEVENLABS_VOICE_ID`: the voice-over
- `PEXELS_API_KEY` and/or `PIXABAY_API_KEY`: free footage (both are free)
- `TELEGRAM_BOT_TOKEN` + `TELEGRAM_OWNER_CHAT_ID`: create a bot through @BotFather, then message it and get your chat id
- `YOUTUBE_CLIENT_ID/SECRET/REFRESH_TOKEN`, `TIKTOK_*`, and `IG_*`: publishing (see the table above)

💡 You can type every key from the app's **Settings** tab instead of editing `.env` by hand.

**Optional extras:**
- Background music: put files in `assets/music/`. If the name contains the mood (`suspense_1.mp3`, `happy.mp3`, ...),
  it is picked automatically to match the video's mood. Use only royalty-free music.
- A proper Arabic font: put a `.ttf` file (such as Cairo or Noto Naskh Arabic) in `assets/fonts/` and set `FACTORY_FONT=Cairo`.
- Custom stickman illustrations: `assets/stickman/<pose>.png` (standing, walking, running, thinking, shocked,
  pointing, sitting, sad, happy) replaces the built-in drawing.
- Shorts format: `FACTORY_FORMAT=vertical`.

### YouTube setup (once)
1. In Google Cloud Console, enable **YouTube Data API v3** and create an OAuth client of type *Desktop*.
2. Get a refresh token with the `https://www.googleapis.com/auth/youtube.upload` scope (for example from
   OAuth Playground, using your own client credentials) and put it in `.env`.
3. To test first, set `YOUTUBE_PRIVACY=private` and the video is uploaded as private.

## ▶️ Running

```bash
python -m factory app          # the private app + the factory (recommended; this is what the shortcut opens)
python -m factory serve        # runs permanently with no interface (for servers) and starts every day at 08:00
python -m factory run --now    # one workday, starting immediately
```
To run it permanently on a server: `deploy/video-factory.service` (systemd).

## 🧪 Free test run (no paid API calls)
```bash
PYTHONPATH=. python tests/test_dry_run.py              # full day: research → … → editing → QA → approval → simulated publish
PYTHONPATH=. python tests/test_helpers_and_approval.py # helpers 7/8 + parsing owner replies
```

## 📂 Daily output
Everything goes in `workspace/<date>/`: `job.json` (full state and log), `script.txt`, `audio/`, `media/`,
`clips/`, `final.mp4`, `final_vertical.mp4`, `thumbnail.jpg`, `preview_sheet.jpg`, `approvals/` (your decisions).
The publishing log is in `workspace/history.json`, so ideas are never repeated. The app log is in `workspace/factory.log`.

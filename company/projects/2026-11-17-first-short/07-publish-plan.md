# 07 - Publish plan - T-001

- Author: Youssef (publisher)
- Date: 2026-11-17
- Input: `brief.md`, `03-hooks.md` (Hala), `05-captions-notes.md` (Reem), `06-cover.md` (Tariq), `08-seo.md` (Sara), `09-community.md` (Dana), `company/config.json`
- Status: **PLAN ONLY. Nothing is posted or scheduled.** Publishing needs the owner's approval (needs_you item "Approve publishing 2026-11-17-first-short"). After approval, `/publish` schedules it through the connected scheduler.
- Video: "Is this Black Friday deal fake? One AI prompt checks it"

## 0. Blocking conditions (do not schedule until all are true)

1. Owner has recorded the real demo + voiceover (N-002, N-005).
2. Khaled has rendered **`edit/vertical_9x16.mp4`** (path relative to this project folder) from that recording. The file does not exist yet.
3. The 0:31 verdict line, on-screen card and SRT cues 23-25 match the real demo verdict, and all 4 SRTs are re-timed to the VO (N-006).
4. "-40%" and the cover prices are replaced with the real numbers (06-cover.md, step 1).
5. Owner has approved the cover (N-004) and the community replies (N-003).

If 1-3 slip past Monday 23 Nov, use the Tuesday 24 Nov fallback (last day per brief). Never stage a verdict to hit a date.

## 1. Schedule (Sara's slots, `08-seo.md`)

DST has ended on both sides: New York EST (UTC-5), Paris CET (UTC+1), 6 h apart. Owner timezone (`schedule.owner_timezone`) = **Europe/Paris**, so owner time = Paris time. Checked with Python `zoneinfo`.

**Main date: Friday 20 Nov 2026**

| Order | Platform | New York (EST) | Paris (CET) | Owner time (Europe/Paris) | Window fit |
|---|---|---|---|---|---|
| 1 | Facebook Reels | Fri 20 Nov 09:00 | Fri 20 Nov 15:00 | Fri 20 Nov 15:00 | NY 09-12 and Paris 13-15 |
| 2 | **YouTube Shorts (main, golden slot)** | Fri 20 Nov 12:00 | Fri 20 Nov 18:00 | Fri 20 Nov 18:00 | Golden slot; NY 12-15, Paris 17-19 |
| 3 | Instagram Reels | Fri 20 Nov 13:00 | Fri 20 Nov 19:00 | Fri 20 Nov 19:00 | NY 11-13, Paris 19-21 |
| 4 | TikTok | Fri 20 Nov 14:00 | Fri 20 Nov 20:00 | Fri 20 Nov 20:00 | Paris 18-21 only (EU first) |

TikTok alternative (US first, owner's call, Sara's open point 2): Fri 20 Nov 19:00 NY = Sat 21 Nov 01:00 Paris / owner.

**Fallback 1: Monday 23 Nov 2026** (same clock times)

| Platform | New York | Paris | Owner |
|---|---|---|---|
| Facebook Reels | Mon 23 Nov 09:00 | Mon 23 Nov 15:00 | Mon 23 Nov 15:00 |
| YouTube Shorts | Mon 23 Nov 12:00 | Mon 23 Nov 18:00 | Mon 23 Nov 18:00 |
| Instagram Reels | Mon 23 Nov 13:00 | Mon 23 Nov 19:00 | Mon 23 Nov 19:00 |
| TikTok | Mon 23 Nov 14:00 | Mon 23 Nov 20:00 | Mon 23 Nov 20:00 |

**Fallback 2 (last possible day): Tuesday 24 Nov 2026**

| Platform | New York | Paris | Owner |
|---|---|---|---|
| Facebook Reels | Tue 24 Nov 09:00 | Tue 24 Nov 15:00 | Tue 24 Nov 15:00 |
| YouTube Shorts | Tue 24 Nov 12:00 | Tue 24 Nov 18:00 | Tue 24 Nov 18:00 |
| Instagram Reels | Tue 24 Nov 13:00 | Tue 24 Nov 19:00 | Tue 24 Nov 19:00 |
| TikTok | Tue 24 Nov 14:00 | Tue 24 Nov 20:00 | Tue 24 Nov 20:00 |

If only one moment is possible for everything: 12:00 New York / 18:00 Paris / 18:00 owner.

All four posts fall within about 5 hours (Sara's choice: each slot sits inside the platform's config window). Dana's rule: someone replies to comments in the first 1-2 hours after each post. So the owner (or Dana's approved replies) should be available **15:00-22:00 owner time** on posting day.

## 2. Shared settings (all platforms)

- **File:** `company/projects/2026-11-17-first-short/edit/vertical_9x16.mp4`. Same clean master everywhere. Never re-upload a file downloaded from another platform (no TikTok/IG watermark).
- **Cover:** `company/projects/2026-11-17-first-short/cover_vertical.jpg` (1080x1920, Concept A, after real prices are in).
- **Audience / content language:** English (US + EU). Burned-in EN captions (from `captions/captions_en.srt`) are in the video.
- **Prompt block:** use the "Common block" from `05-captions-notes.md` (prompt + "Always click the sources... Not financial advice."). Paste it unchanged.
- **Hashtags:** Sara's final sets from `08-seo.md` (they replace Reem's earlier sets; `#chatgpt` is dropped because the prompt is tool-agnostic).
- **EU subtitle line** (`🇩🇪 Untertitel auf Deutsch · 🇫🇷 Sous-titres en français · 🇪🇸 Subtítulos en español`): add it **only** on platforms where the DE/FR/ES tracks were actually uploaded (see each section).
- **Music:** none. Voiceover only (brief). Do not add a platform sound in any app.

### AI disclosure: the rule for this video

House rule `disclose_ai_generated_content: true`, plus Noura's/Reem's rule: label only if AI made realistic media in the video.

| What the video contains | Disclosure |
|---|---|
| Human voiceover (owner) + real screen recording + chatbot answer shown on screen | **No platform AI label.** The chatbot screen is a recording of a real tool, not synthetic realistic media. No "AI-assisted" line required. |
| **AI-generated voiceover** (TTS / voice clone) | **Turn ON the AI label on every platform** + add "AI-assisted (voiceover)" as the last line of each caption/description. Realistic synthetic audio is exactly what YouTube and Meta name. |
| AI background on the cover (06-cover.md optional prompt, needs credits approval) | Add "AI-assisted" to the caption. Platform toggle not needed for a non-realistic illustration. |

Owner: tell Khaled which case applies when you hand over the recording. **Default if unknown: treat as AI voiceover and label.**

## 3. YouTube Shorts (main platform)

| Field | Value |
|---|---|
| File | `edit/vertical_9x16.mp4` (≤ 60 s per config; SRT draft ends at 0:56.8) |
| Title | `Is this Black Friday deal fake? One AI prompt checks it` (55 chars). Only if the recorded answer is ≤ 20 s: `Is this Black Friday deal fake? AI checks it in 20 sec` (54) |
| Description | Sara's description from `08-seo.md` section 1, pasted as-is, + EU subtitle line before the hashtags (tracks are uploaded here) |
| Hashtags | `#blackfriday #aitools #shoppingtips` (end of description, not in title) |
| Tags field | `fake black friday deals`, `how to check if a deal is real`, `ai prompt for shopping` |
| Cover | `cover_vertical.jpg`. Custom Shorts thumbnails: **unverified** for our upload path. Safe route: Khaled puts the cover card as the first 1-2 frames (06-cover.md step 3), then pick that frame in the mobile app's cover picker |
| AI disclosure | Studio upload → Details → "Altered or synthetic content": **Yes** only if the VO is AI-generated; otherwise **No** |
| Video language | English. Caption language: English |
| Audience | "No, it's not made for kids" |
| Pinned comment | Dana's YouTube pin (`09-community.md`), with [PROMPT] filled |

**Subtitles: supported (upload 4 tracks).** Studio → Subtitles → Add language → Upload file → "With timing":
- English: `captions/captions_en.srt` (default)
- German: `captions/captions_de.srt`
- French: `captions/captions_fr.srt`
- Spanish: `captions/captions_es.srt`

Only the re-timed versions with the real verdict (N-006). Spot-check start, middle, end in preview.

## 4. TikTok

| Field | Value |
|---|---|
| File | `edit/vertical_9x16.mp4` (≤ 90 s) |
| First caption line | `Real or fake? Check any Black Friday deal with this one AI prompt (save it)` (75 chars) |
| Full caption | First line + common block + hashtags. **No EU subtitle line** (see subtitles) |
| Hashtags | `#blackfriday #blackfridaydeals #aitools #aiprompts #shoppingtips` (5) |
| Cover | Pick the cover-card frame in "Edit cover"; uploading `cover_vertical.jpg` as an image is **unverified** for this account |
| AI disclosure | More options / Post settings → "AI-generated content": **ON** only if the VO is AI-generated. Otherwise OFF |
| Sound | Original sound only. Do not add trending music |
| Pinned comment | Dana's TikTok pin |

**Subtitles: DE/FR/ES file upload is UNVERIFIED.** Sources disagree on whether TikTok accepts an SRT; none is official. Plan: EN captions are burned in. In the upload screen, check whether (a) an SRT/caption-file import exists, or (b) auto-captions offer translation for this account. If neither exists, post with burned-in EN only and do not add the EU line. Do not burn DE/FR/ES on top of EN (cluttered frame).

## 5. Instagram Reels

| Field | Value |
|---|---|
| File | `edit/vertical_9x16.mp4` (≤ 90 s) |
| First caption line | `Before you buy on Black Friday: one AI prompt to check if the deal is real` (74 chars) |
| Full caption | First line + "Save this and send it to the friend who's about to buy that TV. Full prompt 👇" + common block + hashtags. **No EU line** unless tracks are uploaded |
| Hashtags | `#blackfriday #blackfridaydeals #aitools #aiprompts #shoppingtips` (5 = Instagram's cap, never a 6th) |
| Cover | Edit cover → "Add from camera roll" → `cover_vertical.jpg`. Check the 1:1 grid crop keeps "REAL or FAKE?" readable |
| AI disclosure | Advanced settings → "Add AI label": **ON** only if the VO is AI-generated (toggle reported by third-party sources; confirm in app) |
| Share to Facebook | **OFF.** Facebook gets its own post at its own time with its own caption |
| Pinned comment | Dana's Instagram pin |

**Subtitles: DE/FR/ES file upload is UNVERIFIED (most sources say not supported).** One guide mentions Advanced settings → Accessibility → Captions upload; check there. If absent: burned-in EN only, no EU line.

## 6. Facebook Reels (Page)

| Field | Value |
|---|---|
| File | `edit/vertical_9x16.mp4` (≤ 90 s), uploaded directly (not cross-posted from Instagram) |
| First caption line | `Is this Black Friday deal real or fake? One prompt checks it 👇 (screenshot it)` (78 chars) |
| Full caption | First line + common block + EU line (only if tracks uploaded) + hashtags |
| Hashtags | `#blackfriday #aitools #shoppingtips` (3) |
| Cover | Choose/upload `cover_vertical.jpg` as the Reel cover if offered; else the cover-card frame |
| AI disclosure | Meta requires a label for photorealistic video or realistic-sounding audio made with AI. Use the AI label option if shown **only if the VO is AI-generated**; a separate Facebook toggle is **unverified**, so if none is shown, add "AI-assisted (voiceover)" in the caption |
| Pinned comment | Dana's Facebook pin |

**Subtitles: SRT upload is supported for Facebook videos; for Reels it is UNVERIFIED.** Facebook needs the locale in the file name. Make renamed copies (do not rename the originals):
- `captions_en.srt` → `vertical_9x16.en_US.srt`
- `captions_de.srt` → `vertical_9x16.de_DE.srt`
- `captions_fr.srt` → `vertical_9x16.fr_FR.srt`
- `captions_es.srt` → `vertical_9x16.es_ES.srt`

Files must be UTF-8 plain text. If the Reels composer has no caption-file option, try adding the tracks afterwards via Meta Business Suite → the video → Captions; if that fails too, burned-in EN only and drop the EU line.

## 7. Pre-flight checklist (Khaled + owner, before `/publish`)

**File**
- [ ] `edit/vertical_9x16.mp4` exists and plays to the end
- [ ] 1080x1920, 9:16, H.264 + AAC (`ffprobe` check)
- [ ] Duration ≤ 60 s (YouTube limit in config; TikTok/IG/FB allow 90)
- [ ] No watermark from any platform or editor (no TikTok/CapCut logo)
- [ ] No music; voiceover only; audio peaks not clipping
- [ ] EN captions burned in, inside safe area (not in bottom 20% or top 200 px)
- [ ] Store logos and product brands blurred; no retailer named
- [ ] Hook frame 1 shows **"-<real %>: REAL or FAKE?"** (placeholder -40% replaced)
- [ ] 0:31 verdict VO and card = the real demo verdict (never staged)
- [ ] "20 sec" only in the YouTube title if the real answer was timed ≤ 20 s

**Subtitles**
- [ ] Cues 23-25 swapped to the real verdict in EN/DE/FR/ES; [X] filled
- [ ] All 4 SRTs re-timed to the VO; spot-checked start / middle / end
- [ ] Facebook copies renamed with locale (`.en_US`, `.de_DE`, `.fr_FR`, `.es_ES`)

**Cover**
- [ ] `cover_vertical.jpg` has the real prices/discount; currency matches the store (€ for EU)
- [ ] Owner approved Concept A (N-004)

**Text**
- [ ] Titles/first lines as above; prompt block pasted unchanged; "Not financial advice" present
- [ ] Hashtags: YT 3, TikTok 5, IG 5 (max), FB 3
- [ ] EU subtitle line only where DE/FR/ES tracks are live

**Disclosure**
- [ ] Owner confirmed: human VO or AI VO
- [ ] If AI VO: AI label ON on all 4 + "AI-assisted (voiceover)" line in each caption

**Accounts and timing**
- [ ] Owner logged in to all 4 accounts in the scheduler; IG "share to Facebook" OFF
- [ ] Times entered in the right timezone (scheduler timezone checked: 12:00 NY = 18:00 Paris)
- [ ] Spam/link filters on (N-003); Dana's pins and replies approved
- [ ] Someone free 15:00-22:00 owner time to reply in the first 1-2 h

## 8. Risks / open points

1. Video not rendered yet; the whole schedule depends on the demo + VO being recorded by Sun 22 Nov (for Mon 23) at the latest.
2. Subtitle uploads on TikTok, Instagram and Facebook Reels are unverified; YouTube is the only confirmed multi-language track platform.
3. TikTok time is EU-first (Sara). Owner may switch to 19:00 NY / 01:00 Paris.
4. Platform help centres could not be opened from this session; disclosure and subtitle notes come from search summaries (sources below). Confirm the toggles in each app at upload.

## Sources

- YouTube altered/synthetic content disclosure (realistic AI media incl. synthetic audio; minor edits exempt): https://www.nbcnews.com/tech/tech-news/youtube-says-will-require-creators-label-ai-content-rcna143937 , https://www.engadget.com/youtube-lays-out-new-rules-for-realistic-ai-generated-videos-154248008.html
- YouTube subtitle upload (Subtitles → Add language → Upload file, works for Shorts): https://www.kapwing.com/resources/a-complete-guide-to-youtube-subtitles/ , https://checksub.com/blog/add-subtitles-youtube-shorts
- TikTok "AI-generated content" toggle (More options / Post settings): https://blog.hootsuite.com/ai-disclosure-policy-for-tiktok/ , https://magichour.ai/blog/tiktok-ai-generated-content-labels
- TikTok SRT upload disputed: https://subanana.com/en/blog/how-to-add-subtitles-tiktok , https://iamtypist.dev/blog/how-to-add-captions-on-tiktok
- Meta AI labels (photorealistic video / realistic audio): https://www.meta.com/en-gb/help/artificial-intelligence/1783222608822690/ ; Instagram "Add AI label" toggle (third party): https://minter.io/blog/everything-you-need-to-know-about-ai-labels-on-instagram/
- Instagram Reels SRT upload mostly not supported (one conflicting guide): https://subanana.com/en/blog/how-to-add-subtitles-instagram-reels , https://capsai.co/blog/step-by-step-guide-to-adding-gujarati-captions-to-reels
- Facebook SRT naming `filename.en_US.srt`: https://www.rev.com/blog/resources/how-to-add-captions-subtitles-to-facebook-video-ads , https://www.syncwords.com/blog/how-to-add-captions-subtitles-to-facebook
- Schedule, hashtags, YouTube description: `08-seo.md` (Sara) and its sources.

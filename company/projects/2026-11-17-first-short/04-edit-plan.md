# 04 - Edit plan - T-001 "Is this Black Friday deal fake?"

> **QA round 1 fixes (2026-11-17, Khaled, from Badr's `10-qa.md`, verdict FIX)**
> - **Fix 2:** cover frames at the start carry **no burned-in captions**; cut 1 (hook) captions start after them and must not cover the A1 price block (price block held inside y 300-1250). Preview **not re-rendered yet**: captions are being re-timed first, and the preview waits for Tariq's moved price card (fix 1). Re-render + frame check after both land.
> - **Fix 3 + 4:** REAL row in the verdict swap table now uses the VO wording ("This is the lowest price in [X] days") and replaces "Buy it." with "Good deal, if the sources check out." (pending Youssef's final wording in 02; captions must match the VO word for word).
> - **Fix 5:** cut 3 source line corrected to **"EU Directive 98/6/EC, Art. 6a"**.
> - **Fix 10 / process 2:** one shared safe-zone spec below (top 290, pop-ups 290-1250, caption band 1290-1460, platform UI > 1536, right rail x > 900). This is the reference for the shot list and the cover.
> - **Line length:** EN caption lines ≤ 26 characters (QA measured ≤ 32; the 32-char lines run under the right-side buttons).

- Editor: Khaled (video-editor), 2026-11-17
- Input: `brief.md`, `02-script-short.md`, `03-hooks.md`, `shot-list.md` (Mariam), `captions/captions_en.srt` (Reem), `cover_vertical.jpg` (Tariq)
- Status: **no footage yet** (`company/inbox/footage/` and `raw/` are empty). This plan is ready to cut as soon as A1-A6 + VO land in `raw/`.
- Output target: one 1080x1920 cut, 30 fps, VO only, **no music**, -14 LUFS (tool does it), EN captions burned in. Length target 48-55 s (YouTube Shorts max 60 s).

## Global rules for the cut

- **Safe-zone spec (shared with shot list and cover, 1080x1920):**
  | Zone | Area | Rule |
  |---|---|---|
  | Top UI | y 0-290 | No text, prices or verdicts (platform top bar). Corner timer sits just below, y ~300. |
  | Pop-ups / prices / zooms | **y 290-1250**, **x 60-900** | All pop-ups, price blocks, verdict cards, source lines and zoom targets. |
  | Caption band | y 1290-1460 | Burned captions only (render_short.py, MarginV 70). Nothing important under it. |
  | Platform UI | y > 1536 | Caption/username/music line. Nothing. |
  | Right rail | **x > 900** (y ~900-1700) | TikTok/Reels/Shorts like, comment, share buttons. No pop-up text, badges or key numbers here; centre pop-ups so they end at x ≤ 900. |
- Zoom framing: when punching in (1.4-1.6x), frame the value so it lands inside x 60-900, y 290-1250 after the zoom, not just at the centre of the frame.
- Captions: EN lines **≤ 26 characters** (2 lines max). Longer lines reach x ~1005 and run under the right rail. If a cue cannot be shortened, split it or drop FontSize 13 -> 12 for that cue only.
- Blur on every A-shot: store logo, product brand, chatbot logo, account name/avatar, cookie text (box blur, tracked by hand if the page scrolls).
- No speed-up in A4 unless labelled **"sped up"**; the corner timer always shows real seconds.
- Zooms: smooth 0.4 s ease-in, hold, 0.3 s ease-out. Max 1.6x on screen recordings (text stays sharp at 1080 wide from a 608-720 px window).
- Pop-up text: DejaVu Sans Bold / same style as cover, white with black outline, yellow #FFD400 for key words, red #FF2D2D for FAKE, green #0A8F3C for REAL. Pop in with a 6-frame scale 90% -> 100%.
- Cut on VO: trim every breath gap longer than 0.25 s. The real VO sets the timing; times below are the script targets.

## Cut list (mapped to shot list)

| # | Script time | Draft SRT cues (time) | Source | Edit / zoom | On-screen pop-up | Notes |
|---|---|---|---|---|---|---|
| 1 | 0:00-0:03 | 1-3 (0:00.0-0:04.6) | **A1** (EU or US, whichever A8 picks), hold on price block | Start already zoomed 1.4x on "was" price + % badge; slow push to 1.5x | **-[real %]: REAL or FAKE?** top third (y 300-520). REAL / FAKE stamps flicker 2-3x over the price (B-graphic), **no stamp lands** | Frame 1 must already have text + price. Optional: first 1-2 frames = cover card (Tariq's moved version, price card y ~960-1250) for YouTube frame pick. **No burned-in captions on the cover frames**: cue 1 starts on the first A1 frame after them (shift SRT cue 1 start, or blank the cover frames). Hook captions sit in the band (y 1290-1460) and the A1 price block + % badge must stay above y 1250 and at x ≤ 900 so the captions never cover them. |
| 2 | 0:03-0:09 | 4-7 (0:04.9-0:12.6) | **B** animated price line (our graphic) | Line draws left to right: normal price, jump up, short plateau, "sale" drops back to normal | "Was" price goes up -> then **-[real %]** | Built in ffmpeg/drawbox or simple SVG->PNG sequence. No store names. |
| 3 | 0:09-0:15 | 8-11 (0:12.9-0:21.0) | **B** EU rule text card | Static card, slow 1.0 -> 1.05x push | **EU rule: "was" price = lowest price in the last 30 days** + small source line "EU Directive 98/6/EC, Art. 6a" | Keep source line above y 1250 so the caption band does not hide it. |
| 4 | 0:15-0:19 | 12-14 (0:21.3-0:26.3) | **B** prompt full-screen (from text in `02-script-short.md`) + 0.5 s flash of **A2** (empty chat, search on) | None on the prompt (must be readable). A2 cut-in at "any free chatbot" | **SCREENSHOT THIS** (yellow, top) | Prompt hold counts toward the 3 s minimum. Large monospace, max 12 lines, inside y 290-1250. |
| 5 | 0:19-0:23 | 15-17 (0:26.6-0:30.8) | **A3** paste + click on each filled value | Punch-in 1.4x on each value as Mariam clicks it (link, sale price, was price), ~1 s each | Yellow highlight boxes: **[link] [sale price] [was price]** | Do not show Enter yet. |
| 6 | 0:23-0:31 | 18-22 (0:31.1-0:38.8) | **A4** answer streaming, real time | Wide (1.0x) so the stream is visible; trim only the dead start before Enter | Corner timer 0 -> real seconds (top-right, y ~300). **REAL DEAL / FAKE DISCOUNT / NOT SURE** pop in one by one as the VO lists them | If A4 > 8 s on screen: jump-cut the middle and add **"sped up"** label, timer keeps real time. The real seconds decide the "20 sec" title (Hala). |
| 7 | **~0:31-0:37 VERDICT** | 23-25 (0:39.1-0:44.5) | **A5** verdict + price-history lines | Zoom 1.5x to the price-history lines (hold 2 s), whip to verdict line 1.6x (hold 2.5 s), pull out to show source links | Verdict card, see swap table below. 1-frame white flash + card slam on the verdict word | This is the payoff. Never stage: only what A5 shows. |
| 8 | 0:37-0:40 | 26-27 (0:44.8-0:47.5) | **A6** cursor clicks a source, page loads | Zoom 1.3x on the clicked link, then cut to loaded page | **Click the links** | Blur the source site's logo too. |
| 9 | 0:40-0:46 | 28-30 (0:47.8-0:53.6) | **B** prompt full-screen again | None (screenshot moment) | **Black Friday: Fri 27 Nov** | Second chance to screenshot. Swap date line for Cyber Monday re-post if needed. |
| 10 | 0:46-0:49 | 31-32 (0:53.9-0:56.8) | **B** end card | Static | **Follow for one AI shortcut a day** | No third-party logos. End 0.5 s after last word. |

B-roll list (all our own graphics, Part B of shot list): REAL/FAKE stamps, price line animation, EU rule card, prompt card (x2), corner timer, verdict card (3 versions), "sped up" label, end card.

## Verdict swap (0:31, pick by the real A8 result)

| Real verdict | VO cues 23-25 | Verdict card (centre, y 600-1000) | Hook / other changes |
|---|---|---|---|
| FAKE DISCOUNT | "Here, it's fake. / The "was" price / only lasted [X] days." | Red **FAKE: "was" price lasted [X] days** | Optional 2nd cut with hook #2 for A/B test (Hala). Stamp in shot 1 still must not land. |
| REAL DEAL | "Here, it's real. / This is the lowest price / in [X] days. / Good deal, if the sources check out." (no "Buy it."; final wording = Youssef's 02 line, captions must match the VO word for word) | Green **REAL: lowest price in [X] days** + small line **Check the sources** | Hook #1 only. |
| NOT SURE (current SRT) | as in `captions_en.srt` | Yellow **NOT SURE = no proof. Wait.** | Hook #1 only. |

[X] = the number in the A5 answer, confirmed by Mariam's A7 source check. Swap the same cues in DE/FR/ES SRTs (Reem's table in `05-captions-notes.md`). Also replace "-40%" in shot 1 and the cover with the real discount (EUR if EU store).

## Captions timing preview (done)

- **Status after QA round 1: outdated** (still shows the old cover with the collision). Re-render after the SRT re-timing and Tariq's moved card; do not show it to the owner before that.
- File: `edit/preview_captions_9x16.mp4` - cover as still background + silent track + `captions_en.srt` burned in by `tools/render_short.py`.
- ffprobe: 1080x1920, h264 30 fps + AAC, 57.8 s (last cue ends 56.777 s + 1 s).
- Frames checked at 0:07 (2-line cue) and 0:40 (1-line cue): captions are **readable** (white bold, black outline, ~70 px text).

**Issues found:**
1. **Collision with the cover:** the caption band (y ~1290-1460) sits right on top of the cover's price card and covers the **"NOW $299"** line. Fix for the real cut: no captions on the 1-2 cover frames at the start, and in the cut itself keep all pop-ups and price zooms above y 1250. If the cover card is also used as a video frame, Tariq should move the price card up ~200 px (to about y 880-1280).
2. **Long single lines reach the edges:** "Here, it says not sure:" spans ~x 75-1005 of 1080. Inside the frame, but tight next to the TikTok/Reels right-side buttons. Keep cues at ≤ 26 characters per line in the final SRT, or drop FontSize 13 -> 12 for those cues.
3. **Pacing is long vs the script:** the draft SRT runs 56.8 s and puts the verdict at **0:39**, the script wants it at **~0:31** and ~49 s total. Reem's timings are an estimate (2.6 words/s); the real VO must be faster (~2.8-3 words/s) or the verdict will land late. Re-time the SRT to the real VO before the final render.

## When footage arrives (my steps)

1. Check `raw/` against the shot list hand-off checklist and the A8 table.
2. Rough cut on the VO (`C-vo-full`, best hook take), then lay A1-A6 + B graphics per the cut list.
3. Re-time `captions_en.srt` to the real VO, swap cues 23-25 for the real verdict.
4. Render: `python3 tools/render_short.py <cut.mp4> company/projects/2026-11-17-first-short/edit --srt captions/captions_en.srt --formats vertical`; ffprobe (≤ 60 s), 3 frames for caption/safe-zone check; write `04-edit-notes.md`.

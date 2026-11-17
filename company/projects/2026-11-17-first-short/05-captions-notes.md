# 05 - Captions & post text - T-001

## QA round 1 fixes (Reem, 2026-11-17, from `10-qa.md`)

- **Fix 3 + 4 (REAL wording):** the REAL row now says exactly what the VO says (Noura's updated 02): "Here, it's real. This is the lowest price in [X] days. Good deal, if the sources check out." "Buy it." / "Zugreifen." / "Fonce." / "Cómpralo." are gone in all 4 languages.
- **Fix 8 (timing):** all 4 SRTs re-timed to the new script target. 2.9 words/s inside each beat + 0.1 s between beats. **Verdict starts 0:34.1, last cue ends 0:49.3** (REAL version 0:50.7). This is within QA's limit (verdict ≤ 0:35, total ≤ 52 s). It cannot reach 0:32 at 2.8 words/s: the VO has about 98 words before the verdict, which is about 34 s of speech. If Yasmin wants 0:32, the VO must be about 3.1 words/s, or lose words before the verdict.
- **Fix 9 (reading speed):** the cues QA flagged are merged or shortened (DE "Screenshot machen,", FR "Fais une capture,", "Tous ne jouent pas le jeu."). Now max **16.9 chars/s** in DE/FR/ES (limit 17) and 15.9 in EN.
- **Line length (04-edit-plan, Khaled's safe zone):** every line in all 4 languages is **≤ 26 characters**, max 2 lines. Cues went from 32 to **27**, because short cues were merged into 2-line cues.
- **Fix 2 support:** cue 1 starts at **0:00.100**, so the first 3 frames (cover frames) have no caption.
- **Fix 7:** the old hashtag sets and the old YouTube description are deleted. Hashtags below are copied from `08-seo.md` section 2; the YouTube description is a pointer to `08-seo.md` section 1 (one copy only).
- **N-006** (swap verdict cues + re-time) is team work after recording (Reem + Khaled), not an owner action.

- Author: Reem (captions)
- Date: 2026-11-17 (updated after QA round 1)
- Input: `02-script-short.md` (with "QA round 1 fixes"), `03-hooks.md`, `04-edit-plan.md` (safe zone), `08-seo.md`, `10-qa.md`
- Files: `captions/captions_en.srt`, `captions/captions_de.srt`, `captions/captions_fr.srt`, `captions/captions_es.srt`

## How the SRTs were made

- **No voiceover recorded yet.** Timings are estimated from the script: EN words / 2.9 per script beat, split inside the beat by characters, 0.1 s pause between beats (the caption stays on through the pause). 27 cues, 0:00.100-0:49.276.
- **Re-time after the VO is recorded.** Snap the EN cues to the real waveform (or a transcript of the real VO), then copy the times to DE/FR/ES. Cue numbers and line breaks stay valid. If the real VO runs past 52 s, Noura's rule applies: cut "Not every shop plays fair." (cue 10) first.
- **Checked by script on all 4 files** (validator: sequential numbers, `HH:MM:SS,mmm --> HH:MM:SS,mmm`, UTF-8, LF, no overlaps, 1-2 lines, **≤ 26 chars per line**, 1.0-2.7 s per cue, **≤ 17 chars/s in DE/FR/ES** (≤ 20 in EN, which must match the VO word for word), identical timings in all 4 files). Result: **all pass.** Cues that hold 2 lines run up to 2.6 s; that is on purpose, to keep the reading speed down.
- DE, FR and ES use the **same 27 timings** as EN. Translations are natural, not word for word, and shorter than EN where reading speed needs it; informal "du / tu / tú". "Was" price = DE *Streichpreis*, FR *prix barré*, ES *precio tachado*.

## Cue map (EN, for the editor)

| Cues | Time | Script beat |
|---|---|---|
| 1-2 | 0:00.1-0:04.3 | Hook "Is this Black Friday deal real, or fake? One prompt tells you." |
| 3-6 | 0:04.3-0:11.3 | The trick ("was" price raised) |
| 7-10 | 0:11.3-0:18.7 | EU rule (cue 10 = "Not every shop plays fair.", first cut if long) |
| 11-13 | 0:18.7-0:23.3 | Copy the prompt |
| 14-15 | 0:23.3-0:27.2 | Paste link + prices |
| 16-19 | 0:27.2-0:34.1 | It looks up prices ... verdict list |
| **20-22** | **0:34.1-0:39.1** | **VERDICT (NOT SURE in the files now; swap below)** |
| 23 | 0:39.1-0:41.6 | Always click the sources before you buy. |
| 24-26 | 0:41.6-0:46.9 | Screenshot the prompt, send it to a friend |
| 27 | 0:46.9-0:49.3 | Follow for one AI shortcut a day. |

## Verdict cues: what is in the files and how to swap

The hook is result-agnostic (Hala's winner), so no change is needed there. The verdict is not: the files carry the **NOT SURE** line (no placeholder number, no claim about a product). **Cues 20-22 must be swapped to the real demo verdict in all 4 SRTs.** Never ship a verdict the demo did not show. Fill [X] from the A5 answer, confirmed by the A7 source check.

The wording below is the VO wording in `02-script-short.md` (QA round 1), word for word in EN. All lines ≤ 26 chars, reading speed ≤ 17 chars/s at the timings shown.

**REAL (3 cues, 20-22; runs 1.4 s longer, so shift cues 23-27 by +1.38 s; new end 0:50.7)**

| Cue | Time | EN | DE | FR | ES |
|---|---|---|---|---|---|
| 20 | 0:34.148-0:35.264 | Here, it's real. | Hier ist er echt. | Ici, c'est vrai. | Aquí es real. |
| 21 | 0:35.264-0:37.845 | This is the lowest price / in [X] days. | Das ist der tiefste / Preis seit [X] Tagen. | C'est le prix le plus / bas depuis [X] jours. | Es el precio más bajo / en [X] días. |
| 22 | 0:37.845-0:40.455 | Good deal, if the / sources check out. | Guter Deal, wenn / die Quellen passen. | Bon plan, si les / sources le confirment. | Buena oferta, si las / fuentes lo confirman. |

**FAKE (2 cues, 20-21; delete cue 22 and renumber; runs 1.4 s shorter, so shift the rest by -1.38 s; new end 0:47.9)**

| Cue | Time | EN | DE | FR | ES |
|---|---|---|---|---|---|
| 20 | 0:34.148-0:35.189 | Here, it's fake. | Hier ist er fake. | Ici, c'est faux. | Aquí es falsa. |
| 21 | 0:35.189-0:37.697 | The "was" price only / lasted [X] days. | Der Streichpreis galt / nur [X] Tage. | Le prix barré n'a duré / que [X] jours. | El precio tachado solo / duró [X] días. |

**NOT SURE (in the files now, cues 20-22)**

| Cue | Time | EN | DE | FR | ES |
|---|---|---|---|---|---|
| 20 | 0:34.148-0:35.734 | Here, it says not sure: | Hier sagt er: unsicher – | Ici, il dit « pas sûr » : | Aquí dice: no está claro. |
| 21 | 0:35.734-0:37.321 | no price history found. | keine Preisdaten gefunden. | aucun historique de prix. | sin historial de precios. |
| 22 | 0:37.321-0:39.076 | That's a reason to wait. | Ein Grund zu warten. | Une raison d'attendre. | Un motivo para esperar. |

("/" = line break.) The real VO re-timing replaces these estimated times anyway; the shift values only matter if a preview is rendered before the VO exists.

Note: on-screen verdict cards (REAL DEAL / FAKE DISCOUNT / NOT SURE) are in English in the edit. The translated subtitles translate the spoken words; if translated captions are burned in, keep them in the caption band (y 1290-1460) so they don't cover the English cards.

## Post captions per platform

Hashtags and the YouTube description come from `08-seo.md` (Sara). If 08 changes, 08 wins; do not use any older set.

Common block (paste after the first line on every platform; prompt stays in English, it works in any chatbot and in any country):

```
Paste this into any free AI chatbot with web search:

Is this deal real? Search the web before you answer.
Product: [paste link or exact model name]
Sale price: [price]   "Was" price: [price]   Country: [country]
1. Lowest price for this exact product in the last 30-90 days, with dates.
2. Was the "was" price really charged, and for how long?
3. Price for the same product at 2 other big stores.
4. Verdict in one line: REAL DEAL / FAKE DISCOUNT / NOT SURE.
Only use prices you found, with a link for each. If you can't find data, say NOT SURE. Don't guess.

Always click the sources before you buy. AI can be wrong. Not financial advice.
```

EU reach line (one short line, add at the end before hashtags):
`🇩🇪 Untertitel auf Deutsch · 🇫🇷 Sous-titres en français · 🇪🇸 Subtítulos en español`
(Only if the translated subtitle tracks are actually uploaded; otherwise drop this line.)

### YouTube Shorts
- **Title (55 chars):** Is this Black Friday deal fake? One AI prompt checks it
- **Description:** paste the description from `08-seo.md` section 1 **as-is** (it already holds the prompt, the EU rule line and the 3 hashtags). Add the EU reach line (above) only if the DE/FR/ES tracks are uploaded.
- **Hashtags:** #blackfriday #aitools #shoppingtips (`08-seo.md`; at the end of the description, not in the title)
- **Tags field:** see `08-seo.md` section 1 (3 tags).
- **Subtitles:** upload all 4 SRTs as caption tracks (EN default; DE, FR, ES).
- **Pinned comment:** the prompt text only (easy to copy on mobile).

### TikTok
- **Caption first line (75 chars):** Real or fake? Check any Black Friday deal with this one AI prompt (save it)
- Then the common block (TikTok caption limit is large enough for the full prompt) + EU line.
- **Hashtags:** #blackfriday #blackfridaydeals #aitools #aiprompts #shoppingtips (`08-seo.md`)
- Burn in the EN captions (from `captions_en.srt`) in the edit, so they show on every device. Check in the upload screen whether TikTok offers caption translation for this account; not verified here.

### Instagram Reels
- **Caption first line (74 chars):** Before you buy on Black Friday: one AI prompt to check if the deal is real
- Then: "Save this and send it to the friend who's about to buy that TV. Full prompt 👇" + common block + EU line.
- **Hashtags (5 = cap):** #blackfriday #blackfridaydeals #aitools #aiprompts #shoppingtips (`08-seo.md`; never add a 6th)

### Facebook Reels
- **Caption first line (78 chars):** Is this Black Friday deal real or fake? One prompt checks it 👇 (screenshot it)
- Then the common block + EU line.
- **Hashtags:** #blackfriday #aitools #shoppingtips (`08-seo.md`)
- Upload the SRT files as captions (Facebook supports SRT with the language code in the filename, e.g. `captions_en.srt` may need renaming to `video.en_US.srt` format at upload).

## Disclosure

- Add "AI-assisted" (and the TikTok / Meta / YouTube AI label) **only if the voiceover is AI-generated**. A human voice + real screen recording does not need it (per Noura's caption draft and the house rule).
- Title rule from Hala stays: no "20 seconds" in titles until the real answer is timed.

## Open items for the owner / editor

1. After recording (Reem + Khaled, not the owner): swap cues 20-22 in all 4 SRTs to the real demo verdict (tables above) and fill [X].
2. Re-time all 4 SRTs to the recorded VO (one pass in EN, copy times to DE/FR/ES; cue count is identical), then re-check the rules above (same SRT check as in "How the SRTs were made").
3. Replace "-40%" on screen with the real discount (on-screen only; not in the SRTs).

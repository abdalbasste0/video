# 05 - Captions & post text - T-001

- Author: Reem (captions)
- Date: 2026-11-17
- Input: `02-script-short.md` (final, with Hala's winning hook), `03-hooks.md`, `brief.md`
- Files: `captions/captions_en.srt`, `captions/captions_de.srt`, `captions/captions_fr.srt`, `captions/captions_es.srt`

## How the SRTs were made

- **No voiceover recorded yet.** Timings are estimated from the script at **2.6 words/s**, with 0.3 s pauses between script beats. Total: 32 cues, 0:00.000-0:56.777 (under the 60 s YouTube Shorts limit).
- **Re-time after the VO is recorded.** The script's own table is tighter (about 49 s), so real timings will differ. Easiest fix: import the SRT into the editor and snap cues to the waveform, or re-run a transcript of the real VO and replace the times. Cue numbers and line breaks stay valid.
- Rules checked by script on all 4 files: sequential numbering, `HH:MM:SS,mmm --> HH:MM:SS,mmm`, 1-2 lines per cue, max 32 characters per line, 1.0-2.5 s per cue, no overlaps. All 4 pass.
- DE, FR and ES use the **same 32 timings** as EN. Translations are natural, not word for word; informal "du / tu / tú" (normal on Shorts/TikTok/Reels). "Was" price = DE *Streichpreis*, FR *prix barré*, ES *precio tachado*.

## Conditional lines: what I used (please read before editing)

The script has conditional versions in two places. Because the demo is not recorded, I used the neutral / default lines:

1. **Hook (0:00-0:03):** Hala's winner, already result-agnostic: "Is this Black Friday deal real, or fake? One prompt tells you." (cues 1-3). No change needed later.
2. **Payoff (0:31-0:37):** the script has FAKE / REAL / NOT SURE versions. I used the **NOT SURE** line ("Here, it says not sure: no price history found. That's a reason to wait.") because it is the only version without a placeholder number [X] and it makes no claim about a real product. **Cues 23-25 must be swapped to match the real demo verdict.** Never ship a verdict the demo did not show.

Replacement text for cues 23-25 (fill [X] from the real answer; keep 3 cues, keep ≤ 32 chars/line):

| Verdict | EN | DE | FR | ES |
|---|---|---|---|---|
| FAKE | Here, it's fake. / The "was" price / only lasted [X] days. | Hier ist er fake. / Der Streichpreis galt / nur [X] Tage. | Ici, c'est faux. / Le prix barré n'a duré / que [X] jours. | Aquí es falsa. / El precio tachado / solo duró [X] días. |
| REAL | Here, it's real. / Lowest price in [X] days. / Buy it. | Hier ist er echt. / Tiefster Preis seit [X] Tagen. / Zugreifen. | Ici, c'est une vraie promo. / Prix le plus bas en [X] jours. / Fonce. | Aquí es real. / El precio más bajo en [X] días. / Cómpralo. |
| NOT SURE (used) | as in files | as in files | as in files | as in files |

Note: on-screen verdict cards (REAL DEAL / FAKE DISCOUNT / NOT SURE) are in English in the edit. The translated subtitles translate the spoken words; if the editor burns in translated captions, keep them in the lower third so they don't cover the English cards.

## Post captions per platform

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
- **Description:** Is that Black Friday deal really a deal? One prompt checks it. + common block + EU line
- **Hashtags:** #blackfriday #aitools #shoppingtips #shorts
- **Subtitles:** upload all 4 SRTs as caption tracks (EN default; DE, FR, ES).
- **Pinned comment:** the prompt text only (easy to copy on mobile).

### TikTok
- **Caption first line (75 chars):** Real or fake? Check any Black Friday deal with this one AI prompt (save it)
- Then the common block (TikTok caption limit is large enough for the full prompt) + EU line.
- **Hashtags:** #blackfriday #ai #chatgpt #shoppingtips #aitools #dealcheck
- Burn in the EN captions (from `captions_en.srt`) in the edit, so they show on every device. Check in the upload screen whether TikTok offers caption translation for this account; not verified here.

### Instagram Reels
- **Caption first line (74 chars):** Before you buy on Black Friday: one AI prompt to check if the deal is real
- Then: "Save this and send it to the friend who's about to buy that TV. Full prompt 👇" + common block + EU line.
- **Hashtags (3-5):** #blackfriday #aitools #shoppingtips #moneytips #ai

### Facebook Reels
- **Caption first line (78 chars):** Is this Black Friday deal real or fake? One prompt checks it 👇 (screenshot it)
- Then the common block + EU line.
- **Hashtags:** #blackfriday #shoppingtips #ai
- Upload the SRT files as captions (Facebook supports SRT with the language code in the filename, e.g. `captions_en.srt` may need renaming to `video.en_US.srt` format at upload).

## Disclosure

- Add "AI-assisted" (and the TikTok / Meta / YouTube AI label) **only if the voiceover is AI-generated**. A human voice + real screen recording does not need it (per Noura's caption draft and the house rule).
- Title rule from Hala stays: no "20 seconds" in titles until the real answer is timed.

## Open items for the owner / editor

1. Swap cues 23-25 in all 4 SRTs to the real demo verdict (table above) and fill [X].
2. Re-time all 4 SRTs to the recorded VO (one pass in EN, copy times to DE/FR/ES; cue count is identical).
3. Replace "-40%" on screen with the real discount (on-screen only; not in the SRTs).

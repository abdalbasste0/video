# 06 - Cover - T-001

- Author: Tariq (thumbnail-designer)
- Date: 2026-11-17
- Input: `brief.md`, `02-script-short.md` (Noura), `03-hooks.md` (Hala, winner #1 "-40%: REAL or FAKE?")
- Output: `cover_vertical.jpg` (1080x1920, draft, ffmpeg only, no footage yet)
- Rules applied: no store logos, no product brands, no faces, no paid AI tools, text kept out of the bottom 20% (y > 1536 is empty).

## 3 concepts

| # | Name | Layout | Text (max 4 words) | Focal object | Colours (mobile contrast) | Emotion |
|---|---|---|---|---|---|---|
| A | **Price tag verdict** (drafted) | Top 55%: stacked headline. Middle: white price card with crossed-out "was" price, big sale price, red discount badge on the corner. Bottom 20% empty. | **REAL or FAKE?** (+ small "Black Friday deal") | Price card with a red strike-through on the "was" price | Dark navy-to-plum gradient; white "REAL", red #FF2D2D "FAKE?", yellow #FFD400 accents, green #0A8F3C sale price on white card. All with black outline. | Suspicion, "am I being fooled?" |
| B | **Stamp on the screenshot** | Real frame from the demo product page (blurred logo/brand), zoomed on price. A half-transparent "FAKE?" rubber stamp tilted across the price, question mark keeps it result-agnostic. | **FAKE DISCOUNT?** | The real "was" price + discount badge from the recording | Real screenshot darkened 40%, red stamp, white outline text top third | Curiosity, outrage |
| C | **Split verdict** | Screen split vertically: left half green "REAL" with tick, right half red "FAKE" with cross, the same price card in the middle on the seam. | **Real or fake deal?** | Price card sitting on the green/red split | Pure green #0A8F3C / red #FF2D2D halves, white card, black text | Decision tension, "which side?" |

## Drafted: Concept A

Why: it matches Hala's winning hook word for word ("REAL or FAKE?"), does not give away the verdict at 0:31, needs no footage, and reads at thumbnail size on the grid (two huge words + one price visual).

- File: `company/projects/2026-11-17-first-short/cover_vertical.jpg`
- Built with: `lavfi gradients` + `drawtext` (DejaVu Sans Bold) + `drawbox` (card, strike-through line, badge).
- Legibility check: viewed at full size. "REAL" / "FAKE?" are readable at grid size; the strike-through is clear. Layout updated in QA round 1 (see below): nothing below y=1250, nothing above y=300.
- Prices **$499 -> $299 (-40%)** are placeholders that match the hook's "-40%" example. They are not a real product.

## Before publishing (for Khaled / editor)

1. Replace the placeholder prices and discount with the **real** numbers from the recorded demo product (Hala's note: "-40%" must become the real discount). If the store is in the EU, use EUR (e.g. "WAS 499 €").
2. Optional upgrade to Concept B once the recording exists: grab a frame with `ffmpeg -ss <t> -i video.mp4 -frames:v 1 frame.png`, blur logos/brands, then lay the same headline on top.
3. Same cover for all 4 platforms; YouTube Shorts lets you pick a frame, so also place this card as the first 1-2 frames of the video if needed.

## Optional AI image (not used, needs owner approval)

Not generated (costs credits). Prompt, if the owner wants a richer background for Concept A:
> "Flat vector illustration of a generic shopping price tag with a red strike-through on the old price, magnifying glass over it, dark navy background, no brand names, no logos, no text, high contrast, vertical 9:16."
If used, label the post "AI-assisted" where the platform requires it.

## QA round 1 fixes (Badr, 10-qa.md fix 1)

Problem: the caption band (y ~1290-1460) covered "NOW $299", and the "-40%" badge (x 770-1010) sat under the TikTok/Reels right-hand buttons.

Re-rendered `cover_vertical.jpg` (1080x1920, ffmpeg `gradients` + `drawtext` + `drawbox`, DejaVu Sans Bold). Old version kept only in my scratchpad, not in the project.

| Element | Before | Now |
|---|---|---|
| "BLACK FRIDAY DEAL" | y ~200-265, 80 px | y 300-355, 66 px |
| "REAL" | 230 px | 190 px, y ~390-545 |
| "or" | y ~610-685 | y ~598-650 |
| "FAKE?" | 230 px, ends y ~945 | 190 px, ends y ~848 |
| Price card | x 120-960, y 1090-1490 | **x 90-900, y 960-1250** |
| "-40%" badge | x 770-1010, y 1030-1150 | **x 640-890, y 920-1030** (on the card corner) |
| "NOW $299" | y ~1320-1420 | y ~1112-1205 |

Checks (image viewed after render):
- Caption band y 1290-1460 and platform UI > y 1536: empty. Lowest pixel of content is y 1250.
- Right rail: nothing at x > 900 below y 900 (right 180 px clear).
- "FAKE?" (ends ~848) has a ~70 px gap above the badge and ~110 px above the card.
- Top safe zone: nothing above y 300 (TikTok/Reels top bar).
- IG 3:4 grid crop (1080x1440, y 240-1680): headline, card and badge all inside, nothing cut.

Still placeholders: $499 / $299 / -40% must be replaced with the real numbers after the recording (see "Before publishing").
Next step is for Khaled (fix 2): re-render the caption preview with this cover and no burned captions on the 1-2 cover frames.

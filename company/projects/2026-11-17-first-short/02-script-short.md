# 02 - Short script - T-001

## QA round 1 fixes (Noura, 2026-11-17, from `10-qa.md`)

- Fix 4 + 3 (REAL verdict VO): "Here, it's real. This is the lowest price in [X] days. Buy it." → "Here, it's real. This is the lowest price in [X] days. Good deal, if the sources check out." No direct buy instruction. Captions must use this exact wording (Reem).
- Fix 5 (on-screen source line, 0:10-0:17 row, was the 0:09 row): "EU Directive 2019/2161, Art. 6a" → "EU Directive 98/6/EC, Art. 6a".
- Fix 6 (header title): "...checks it in 20 seconds." → the 55-char title "Is this Black Friday deal fake? One AI prompt checks it". Alternative opening A ("in 20 seconds") is now conditional on the timed answer.
- Fix 7 (caption draft): old hashtag line replaced by a pointer to `08-seo.md`.
- Fix 8 (timing): one target: **≤ 52 s total, verdict starts ≤ 0:35, about 2.8 words/s.** Table re-timed (verdict now 0:32, end 0:50). Hard cap 58 s; if the real VO runs past 52 s, cut "Not every shop plays fair." first.
- No other VO line changed.

- Author: Noura (scriptwriter-short)
- Date: 2026-11-17
- Title: **"Is this Black Friday deal fake? One AI prompt checks it"** (55 chars, Hala's version; see `03-hooks.md` / `08-seo.md`). "20 sec" title only if the recorded answer is timed at 20 s or less.
- Format: 9:16, faceless (screen recording + voiceover), voiceover only, **no music** (per brief).
- Length target: **≤ 52 s total, verdict starts ≤ 0:35**, at about **2.8 words/s** plus short beats (VO = 136 words with the FAKE line, 140 NOT SURE, 144 REAL). Hard cap 58 s; if the recorded VO runs past 52 s, cut "Not every shop plays fair." first (5 words, about 2 s). Captions are timed to the real VO, not to this estimate. Fits YouTube Shorts (max 60 s), TikTok, Reels and FB Reels.
- Structure: result first (Layla's double hook), then the mechanism, then the prompt on screen, verdict before 0:35, CTA.

> **Hook update (Hala, 2026-11-17):** 0:00-0:03 now uses the winning hook from `03-hooks.md` (curiosity gap: "Is this Black Friday deal real, or fake? One prompt tells you."). It works for any demo verdict, so the old "It's fake" opening is no longer conditional. The verdict line (now 0:32) has 3 versions (FAKE / REAL / NOT SURE). Titles per platform are in `03-hooks.md`; "20 seconds" stays out of titles until the real answer is timed.

## Script

| Time | Voiceover | On-screen text | Visual |
|---|---|---|---|
| 0:00-0:03 | "Is this Black Friday deal real, or fake? One prompt tells you." | **-40%: REAL or FAKE?** (use the real discount from the demo product) | Product page, crossed-out "was" price and discount badge zoomed in (store logo and product brand blurred). REAL and FAKE stamps flicker over the price, no stamp lands. Do not show the chatbot verdict here; it is the payoff at 0:32. |
| 0:03-0:10 | "Here's the trick. Some stores raise the 'was' price a few weeks before the sale, so the discount looks huge." | "Was" price goes up -> then "-40%" | Simple animated price line (our own graphic): price jumps up, short plateau, then the "sale" drops back to the old normal price. |
| 0:10-0:17 | "In the EU, that old price must be the lowest price from the last 30 days. Not every shop plays fair." | **EU rule: "was" price = lowest price in the last 30 days** | Text card. Small source line: "EU Directive 98/6/EC, Art. 6a". |
| 0:17-0:21 | "So copy this prompt into any free chatbot that can search the web." | **SCREENSHOT THIS** | Prompt appears full-screen (see "Prompt on screen" below). Hold it on screen for at least 3 s total across this and the next line. |
| 0:21-0:25 | "Paste the product link, the sale price and the 'was' price." | [link] [sale price] [was price] highlighted | Screen recording: pasting the link and two prices into the brackets in a free chatbot with web search turned on. |
| 0:25-0:32 | "It looks up recent prices, checks two other stores, and gives a verdict: real deal, fake discount, or not sure." | **REAL DEAL / FAKE DISCOUNT / NOT SURE** | Real-time recording of the answer streaming in (no speed-up; if trimmed, label "sped up"). Small timer in the corner, 0 -> real seconds. |
| 0:32-0:38 | Pick by the real demo verdict (see `03-hooks.md`). FAKE: "Here, it's fake. The 'was' price only lasted [X] days." / REAL: "Here, it's real. This is the lowest price in [X] days. Good deal, if the sources check out." / NOT SURE: "Here, it says not sure: no price history found. That's a reason to wait." | Matching verdict card, e.g. **FAKE: "was" price lasted [X] days** | Zoom on the answer's price-history lines and its source links. **Use what the real demo shows. Never stage a result.** |
| 0:38-0:41 | "Always click the sources before you buy." | Click the links | Cursor clicks one source link in the answer. |
| 0:41-0:47 | "Screenshot the prompt, and send it to the friend who's about to buy that TV." | **Black Friday: Fri 27 Nov** | Prompt shown full-screen again (second chance to screenshot). |
| 0:47-0:50 | "Follow for one AI shortcut a day." | Follow for one AI shortcut a day | Channel end card (no logos of third parties). |

Word count (VO): 136 with the FAKE line, 140 with NOT SURE, 144 with REAL (all under 150). Payoff (verdict + reason) lands at 0:25-0:38, before the 0:45 limit. Timings assume about 2.8 words/s; the REAL version may run about 1-2 s longer.

## Prompt on screen (copy-paste, tool-agnostic)

Show it in a large monospace font, max ~12 lines on screen. Also put the full text in the caption / pinned comment.

```
Is this deal real? Search the web before you answer.
Product: [paste link or exact model name]
Sale price: [price]   "Was" price: [price]   Country: [country]

1. Lowest price for this exact product in the last 30-90 days, with dates.
2. Was the "was" price really charged, and for how long?
3. Price for the same product at 2 other big stores.
4. Verdict in one line: REAL DEAL / FAKE DISCOUNT / NOT SURE.

Only use prices you found, with a link for each. If you can't find data, say NOT SURE. Don't guess.
```

Why it is written this way: it works in any free chatbot that has web search (no plan-specific feature named), it forces source links so viewers can check the answer, and "NOT SURE" stops the bot from inventing a price history.

## 2 alternative openings (for Hala)

- **A (question hook):** VO: "Is this Black Friday deal fake? This prompt tells you in 20 seconds." / On-screen: **"Real deal or fake discount?"** over the crossed-out price. **Conditional:** use "in 20 seconds" only if the recorded chatbot answer is timed at 20 s or less; otherwise say "...This prompt tells you." (Hala picked the hook in `03-hooks.md`; this stays a backup.)
- **B (money hook):** VO: "Stop. Before you pay for that Black Friday deal, paste this into any free AI." / On-screen: **"Check before you pay"** with the cart button greyed out.

## Caption draft (same on all 4, tweak hashtags per platform)

Is that Black Friday deal really a deal? Paste this prompt into any free AI chatbot with web search (prompt below). Always click the sources it gives you. Not financial advice.
[full prompt]
Hashtags: use the per-platform sets in `08-seo.md` (section 2). Do not use an older set.

Add "AI-assisted" only if the voiceover is AI-generated (TikTok label toggle too). A plain screen recording + human voice does not need the label.

## Production notes and risks

1. **The demo must be real.** Record the demo first on a real product. The opening now works for any verdict (Hala's update); only the 0:32-0:38 line changes: use the FAKE / REAL / NOT SURE version that matches the real result. Never stage a result.
2. **"20 sec" in a title** only if it is true for the tool we record. Default title: "Is this Black Friday deal fake? One AI prompt checks it". Time the real answer; the "20 sec" title is allowed only at 20 s or less (`03-hooks.md`, `08-seo.md`).
3. **Use an EU store and a US store** when testing; price-history coverage varies by country. Pick the one that gives a clear answer for the video.
4. **Blur store logos and product brand names**; don't name or accuse a specific retailer. Say "some stores", as in the script.
5. **AI can be wrong.** The script tells viewers to click the sources; keep that line.
6. **US nuance (kept off screen on purpose):** the US has no fixed 30-day rule like the EU. The FTC's pricing guides say a "was" price must be a genuine former price, not a fictitious one. If a commenter asks, that is the answer (source below).
7. Post by 24 Nov 2026 per brief. The video stays usable for Cyber Monday (30 Nov) and January sales; only the 0:41 on-screen date is Black Friday-specific.

## Fact check and sources

| Claim in script | Status | Source |
|---|---|---|
| Black Friday 2026 is Friday 27 Nov (Thanksgiving 26 Nov, Cyber Monday 30 Nov) | Confirmed by several calendars | https://www.calendardate.com/black_friday_2026.htm , https://publicholidays.com/black-friday/ , https://www.universaltimedate.com/articles/black-friday-2026 |
| EU: an announced price reduction must show the "prior price" = lowest price applied in at least the 30 days before the reduction (Directive 98/6/EC Art. 6a, added by Omnibus Directive (EU) 2019/2161) | Confirmed via law-firm summaries; CJEU C-330/23 (26 Sep 2024) ruled the % discount must be calculated from that 30-day lowest price. Exceptions exist (perishables, goods on sale < 30 days, progressive reductions); member states may set longer periods. | https://www.hsfkramer.com/notes/ip/2024-posts/cjeu-confirms-that-price-reduction-claims-must-be-based-on-lowest-price-in-last-30-days , https://insightplus.bakermckenzie.com/bm/international-commercial-trade/european-union-the-cjeu-confirms-that-a-price-reduction-must-be-calculated-based-on-the-lowest-price-in-the-last-30-days , https://www.rpclegal.com/snapshots/consumer/spring-2022/european-commission-publishes-guidance-on-price-promotions-under-the-omnibus-directive/ , primary text: https://eur-lex.europa.eu/eli/dir/2019/2161/oj |
| How fake discounts work: stores raise the "was" price shortly before Black Friday; most "deals" are the same price or cheaper at other times of year | Confirmed: UK consumer group Which? finds this every year (e.g. a TV at £379 for only 3 days before a "£100 off" Black Friday price; "nine in 10 Black Friday deals cheaper or same price at other times of the year"). UK data, so the script says "some stores", no %. | https://www.which.co.uk/policy-and-insight/article/nine-in-10-black-friday-deals-cheaper-or-same-price-at-other-times-of-the-year-which-finds-a4Z2J3u5lTI2 , https://www.which.co.uk/policy-and-insight/article/only-one-in-seven-deals-worth-buying-on-black-friday-which-finds-aVYGM0J8z4Yf , https://www.retail-systems.com/rs/Only_14pc_Of_Black_Friday_Deals_Offer_A_Real_Discount_Warns_Which.php |
| US: "was" price must not be fictitious (FTC Guides Against Deceptive Pricing, 16 CFR 233.1); guidance, no fixed 30-day number | Confirmed (notes only, not in VO) | https://www.ecfr.gov/current/title-16/chapter-I/subchapter-B/part-233 , https://www.law.cornell.edu/cfr/text/16/part-233 |

**Verification limit:** page fetching was blocked in this session (eur-lex.europa.eu and which.co.uk did not resolve), so the facts above come from search results and summaries that agree with each other, not from reading the full pages. Nothing in the VO depends on a specific number from those pages.

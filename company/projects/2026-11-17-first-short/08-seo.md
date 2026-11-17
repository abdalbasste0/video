# 08 - SEO, hashtags and posting time - T-001

- Author: Sara (growth-analyst)
- Date: 2026-11-17
- Input: `brief.md`, `02-script-short.md` (Noura), `03-hooks.md` (Hala), `company/config.json`
- Method: free web search only (`paid_research_allowed: false`, no vidIQ, no paid keyword tools).

## Limits (read first)
- **No search-volume numbers.** Free search gives no keyword volumes, so I rank keywords by how often the same phrasing shows up in article titles and how well it matches the script. I did not make up any numbers.
- **Page fetching was blocked** (support.google.com did not resolve). Platform hashtag rules below come from search summaries, not the official help pages. Where sources disagree, I note it.
- Posting times use the **starting heuristics in `config.json`**. We have 0 posts of evidence, so I am not changing the windows (rule: at least 10 posts first).

## 1. YouTube search keywords

**Search phrasings people use** (each one appears as a headline on consumer/tech sites):
- "how to check if a Black Friday deal is real" ([Which?](https://www.which.co.uk/reviews/black-friday/article/black-friday-deals/black-friday-deals-how-to-check-if-a-black-friday-deal-is-real))
- "how to spot a fake Black Friday deal" ([Laptop Mag](https://www.laptopmag.com/how-to/how-to-spot-a-fake-black-friday-deal))
- "check price history" / "spot a bad Black Friday deal" ([Ground News](https://ground.news/article/how-to-check-price-history-and-spot-a-bad-black-friday-deal), [Android Authority](https://www.androidauthority.com/how-to-tell-if-a-black-friday-deal-is-worth-it-3734185/))
- "AI Black Friday prompts" ([Plann](https://www.plannthat.com/ai-black-friday-prompts/)); "asked ChatGPT which Black Friday deals aren't worth it" ([AOL/GOBankingRates](https://www.aol.com/articles/asked-chatgpt-black-friday-deals-145508557.html))
- "fake discounts" is also the term used in EU coverage, e.g. the EU sweep that found 30% of checked online traders showed discounts incorrectly ([European Commission, 26 Mar 2026](https://commission.europa.eu/news-and-media/news/eu-check-reveals-misleading-sales-practices-online-2026-03-26_en)). French and German outlets keep the English words "Black Friday" ([Que Choisir](https://www.quechoisir.org/actualite-black-friday-une-promotion-sur-trois-est-fausse-n175366/), [heise](https://heise.de/-11226422)), so one English keyword set serves US and EU.

**Primary keyword:** fake Black Friday deal. **Secondary:** check if a deal is real, price history, AI prompt.

### Title (≤ 60, Hala's version, unchanged)
`Is this Black Friday deal fake? One AI prompt checks it` (55 chars)

Only if the recorded answer is timed at 20 s or less: `Is this Black Friday deal fake? AI checks it in 20 sec` (54 chars).

### Description (paste as-is; first 2 lines carry the keywords)
```
Is this Black Friday deal real or fake? Copy this AI prompt to check any discount: price history, the real "was" price, and prices at 2 other stores.
Works in any free AI chatbot that can search the web. Always click the sources before you buy.

THE PROMPT (copy-paste):
Is this deal real? Search the web before you answer.
Product: [paste link or exact model name]
Sale price: [price]   "Was" price: [price]   Country: [country]
1. Lowest price for this exact product in the last 30-90 days, with dates.
2. Was the "was" price really charged, and for how long?
3. Price for the same product at 2 other big stores.
4. Verdict in one line: REAL DEAL / FAKE DISCOUNT / NOT SURE.
Only use prices you found, with a link for each. If you can't find data, say NOT SURE. Don't guess.

EU shoppers: a "was" price must be the lowest price of the last 30 days (Directive 98/6/EC, Art. 6a, added by Directive (EU) 2019/2161).
Black Friday 2026: Friday 27 November. Also works for Cyber Monday and January sales.

Not financial advice. AI can be wrong, so check the links it gives you.
Follow for one AI shortcut a day.

#blackfriday #aitools #shoppingtips
```
- Add "AI-assisted" to the description only if the voiceover is AI-generated (Noura's rule in `02-script-short.md`).
- The 3 hashtags go at the end of the description, not in the title, to keep the title's 55 characters for words.

### 3 tags (YouTube "Tags" field)
1. `fake black friday deals`
2. `how to check if a deal is real`
3. `ai prompt for shopping`

## 2. Hashtags per platform (one set works for US + EU)

Rules I worked to:
- **YouTube:** keep it small. Sources say the first 3 description hashtags show above the title and too many hashtags are ignored. They disagree on the cap (15 or 60), and I could not open the official page ([hashtagtools.io](https://hashtagtools.io/blog/youtube-shorts-character-limits-title-description-hashtags-2026), [wildandfreetools](https://wildandfreetools.com/blog/youtube-shorts-hashtags-title-or-description/)). We use 3, which is under both.
- **Instagram:** limited to **5 hashtags per post/Reel** since Mosseri's announcement on 19 Dec 2025 ([Business Today](https://www.businesstoday.in/technology/news/story/no-more-hashtag-stuffing-instagram-limits-hashtag-usage-to-just-5-per-reel-and-post-507444-2025-12-19), [Social Media Today](https://www.socialmediatoday.com/news/instagram-implements-new-limits-on-hashtag-use/808309/)).
- **Facebook:** no official number found. Third-party guides say about 3 and warn against loosely related tags ([Emplifi](https://emplifi.io/resources/blog/everything-you-need-to-know-about-hashtags-on-facebook), [Metricool](https://metricool.com/how-many-hashtags-to-use/)).
- **TikTok:** I found no usage counts for 2025/2026. #BlackFridayDeals is named as a high-interaction tag in Infegy's 2024 season data ([Infegy](https://www.infegy.com/insight-brief/exploring-tiktok-shops-growing-presence-with-black-friday)). I am **not** using #TikTokShopBlackFriday because we sell nothing, and an unrelated tag breaks platform rules.
- **US vs EU:** "Black Friday" is the term in both markets (see the FR/DE sources above), and we post one English video per platform. So the set is the same for both, with no separate EU set.

| Platform | Hashtags (in this order) | Count |
|---|---|---|
| YouTube Shorts | #blackfriday #aitools #shoppingtips | 3 |
| TikTok | #blackfriday #blackfridaydeals #aitools #aiprompts #shoppingtips | 5 |
| Instagram Reels | #blackfriday #blackfridaydeals #aitools #aiprompts #shoppingtips | 5 (cap) |
| Facebook Reels | #blackfriday #aitools #shoppingtips | 3 |

**Change from Noura's caption draft:** I dropped `#chatgpt` because the prompt is tool-agnostic by design (brief constraint). If the demo is recorded in ChatGPT, it may replace `#aiprompts` on TikTok and Instagram. Put the 5th tag on Instagram only if the owner wants it. The cap is 5, so never add a 6th.

**TikTok search tip:** TikTok search also reads the words in the caption and on screen. The first caption line from `03-hooks.md` already contains "Black Friday deal", "real or fake" and "AI prompt". Keep it.

## 3. Recommended posting date and time

Daylight saving time has ended on both sides (US since 1 Nov, EU since 25 Oct 2026), so New York (EST, UTC-5) is **6 hours** behind Paris (CET, UTC+1). Times below were checked with Python `zoneinfo`.

**Date: Friday 20 Nov 2026** (fallback: Monday 23 Nov; last possible day: Tuesday 24 Nov, per the brief).
Why: the video's value is checking a deal *before* Black Friday (Fri 27 Nov). Posting on the 20th gives a full week of runway before the deals go live and catches the "early Black Friday" weekend. This is reasoning, not data. We have no channel numbers yet.
Condition: post only once the real demo is recorded and the 0:31 verdict line matches it. Don't rush the date if that means staging a result.

| Platform | New York (EST) | Paris (CET) | Fit with config windows |
|---|---|---|---|
| Facebook Reels | 09:00 | 15:00 | Inside both: NY 09-12 starts, Paris 13-15 ends |
| YouTube Shorts | 12:00 | 18:00 | Golden slot; inside NY 12-15 and Paris 17-19 |
| Instagram Reels | 13:00 | 19:00 | Inside both: NY 11-13 ends, Paris 19-21 starts |
| TikTok | 14:00 | 20:00 | Inside Paris 18-21 only. The NY window 19-21 = 01-03 Paris, so no time covers both. I chose the EU window because the US gets it in the afternoon. Alternative: 19:00 NY / 01:00 Paris if the owner wants US first. |

If we can only post once at the same moment everywhere, use the **golden slot: 12:00 New York / 18:00 Paris**.

## Open points for Yasmin / owner
1. To confirm the YouTube hashtag rules from the source, the owner must allow `support.google.com` in the session network settings. Not blocking: 3 tags is safe under every cap I found.
2. The TikTok time is a trade-off between the two markets (see table). Owner's call if the US should come first.
3. After 10+ posts I will replace these windows with our own numbers.

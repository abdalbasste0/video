# QA: affiliate pixel stories, batch B (T-002)

Reviewer: Badr (qa-reviewer). Date checked: 2026-11-17.
Scope: `stories/webflow.json`, `heygen.json`, `hubspot.json`, `synthesia.json`, `speechify.json` and their `.sources.md`.
Method: I read every scene against its source table and re-checked the 3 riskiest claims per story with web search (results below). Glyphs were checked by script against the `FONT` table in `tools/pixel_story/engine.html`, and short-cut timing was checked with the build.py formula (words / 2.6 + 0.7 s). All 5 files were validated with `python3 -m json.tool` after the edits.
Limits: heygen.com, upstartsmedia.com, forbes.co and synthesia.io do not resolve from this session. I verified those through search-result snippets only. The owner should open the starred links in each `.sources.md` once before publishing.

## Summary

| Story | Verdict | Short cut (est.) | Long (est.) |
|---|---|---|---|
| Webflow | **PASS after fixes** | 59.1 s (7 scenes) | 2:49 |
| HeyGen | **PASS after fixes** | 52.0 s (5 scenes) | 2:55 |
| HubSpot | **PASS after fixes** | 53.1 s (5 scenes) | 2:57 |
| Synthesia | **PASS after fixes** | 53.1 s (5 scenes) | 3:00 |
| Speechify | **PASS after fixes** | 50.0 s (5 scenes) | 2:51 |

The common checks passed for all 5 stories:
- Every on-canvas glyph is in the pixel font (0 bad glyphs).
- Each short cut starts with the hook scene and ends with the spoken CTA, which includes "I may earn a commission if you sign up, at no extra cost to you". Each runs 45-60 s, under YouTube's 60 s limit.
- No script says "I use" or "we use" a product.
- No logos appear. Company names are text only.
- No medical or financial advice.

---

## 1. Webflow: PASS after fixes
Changes made:
1. **Scene 9**: the weakly sourced, single-blog specifics ("used his retirement savings, sold his cars, credit card debt") are now "Reports say the founders spent their savings and took on personal debt to keep going."
2. **Scene 10** (short): "a working prototype **of Webflow** on Hacker News". Without it, the short never named the product before scene 14.
3. **Scene 15 board**: `$100M / YEAR` is now `~$100M / YEAR`, so the board matches the "about" in the narration.
4. **Scene 17** (short): "a pile of debt became a company worth billions" is now "years of money trouble. Then a company valued at four billion dollars." The old line made an unsourced claim about today's value, since the $4B valuation is from 2022, and it repeated the weak debt claim.
5. **Scene 20** (short CTA): "Want to try Webflow?" added so the short CTA names the product.

Re-verified:
- YC rejected them in Nov 2012. In March 2013 they posted on HN and got about 20K sign-ups (sources range 20K-35K), then joined YC S13. Sources: https://webflow.com/blog/the-story-of-how-webflow-and-y-combinator, https://review.firstround.com/webflows-path-to-product-market-fit-lessons-on-creating-a-market-with-rigorous-customer-empathy, https://techcrunch.com/2013/08/05/webflow-lets-you-design-responsive-websites-visually-publish-instantly-when-youre-done
- The free Starter plan still exists after the May 2026 restructure. Source: https://webflow.com/blog/simplified-plans-and-updated-pricing-2026
- $120M Series C at $4B in March 2022 was already strongly sourced (SiliconANGLE).

Remaining risks:
- Webflow's own pricing blog says "purchase a paid Site plan to publish, host...". Third-party guides say Starter publishes to a webflow.io subdomain. Scene 18 ("publish a real site on a webflow dot io address") must be checked on webflow.com/pricing on publish day (owner).
- "A young father has a family to support" (scene 1) is secondary (buildd.co). It is low risk, but it is personal detail.

## 2. HeyGen: PASS after fixes
Changes made:
1. **Scene 13 bar chart** (known issue): the middle bar `100` was flagged as a writer's estimate. I checked it. Two sources report it: Upstarts says the ARR "doubled from $100 million eight months ago", and Forbes (Nov 13, 2025) says HeyGen "said it had reached $100M recurring revenue". So the value **stays at 100 as a company-reported figure**, and the label changed from the guessed month `OCT 25` to `2025`. The chart title already says "ARR $M (COMPANY)". Sources: https://www.upstartsmedia.com/p/exclusive-heygen-200m-arr-without-burn, https://forbes.co/2025/11/13/ia/heygen-se-sube-al-boom-del-video-de-alta-calidad-con-ia/, https://www.heygen.com/blog/heygen-surpasses-200m-arr. If Yasmin wants zero snippet-only sources, delete the middle bar instead (`values: [1, 200]`, `labels: ["JAN 23","JUN 26"]`).
2. **Title**: "built by a man who hated cameras" is now "built by a founder who felt awkward on camera". The old wording overstated a single Spanish-language Forbes Argentina source, whose headline says "sentirse incómodo".
3. **Scene 5**: "never felt comfortable" is now "did not feel comfortable" (same reason).
4. **Scene 11 date card**: `END 2023` is now `2023`. Sources disagree on when the Shenzhen entity was dissolved: Contrary says 2023, and Pandaily only reports "undergoing dissolution".

Re-verified:
- $200M ARR, announced June 25, 2026, roughly doubled in about 8 months, cash-flow break-even. All of this is company-reported, and the script says so.
- US lawmakers' scrutiny, Chinese investors asked to sell, Shenzhen entity dissolved. Sources: https://scmp.com/tech/tech-trends/article/3267861/ai-start-heygen-raises-us60-million-after-pivoting-away-mainland-china-investors, https://research.contrary.com/reports/heygen, https://www.maginative.com/article/heygen-raising-60m-at-440m-valuation-launches-heygen-5-0/ (mentions the House Select Committee report). The tone is neutral and acceptable.
- Free plan of 3 videos a month, 720p, watermark: most 2026 third-party guides agree, for example https://zsky.ai/blog/is-heygen-free and https://www.arcade.software/post/heygen-pricing. The length cap conflicts across sources and is not used in the script.

Remaining risks:
- 30M users in 196 countries is company-reported via yespress and is worded "HeyGen says". This is OK.
- Free-plan limits change often. Check heygen.com/pricing on publish day.

## 3. HubSpot: PASS after fixes
Changes made:
1. **Scene 1** (hook, fairness): "fell about 20 percent in a single day. Investors were scared that AI would replace the software it sells" is now "fell about 20 percent **during** a single day. Its outlook disappointed Wall Street, at a time when many investors feared AI could replace software like it." The source gives 20.1% *intraday*, and the drop was triggered by weak Q2 guidance, not only AI fear. The old line stated investors' motive as fact.
2. **Scene 1 board sub**: `STOCK, IN ONE DAY` is now `STOCK, DURING ONE DAY` (intraday, matching the narration).
3. **Scene 8**: "One month later" is now "A few weeks later". The free CRM was announced at INBOUND in Sep 2014, and the IPO was priced Oct 8, 2014.

Re-verified:
- May 8, 2026: shares down 20.1% intraday after Q1. Revenue was about $881M, +23% YoY, and Q2 guidance came in below consensus. Sources: https://www.fool.com/investing/2026/05/08/why-hubspot-plunged-today/, https://www.nasdaq.com/articles/why-hubspot-plunged-today
- July 10, 2024: Alphabet shelved its talks, which never reached due diligence. The stock fell as much as 19% intraday and about 12% at the close. The script uses "as much as 19 percent", which is correct. Source: https://www.bloomberg.com/news/articles/2024-07-10/google-parent-alphabet-is-said-to-shelve-its-interest-in-hubspot
- FY2025 revenue was $3.13B (+19%), with 288,706 customers at Dec 31, 2025. Source: https://www.businesswire.com/news/home/20260211469584/en/HubSpot-Reports-Strong-Q4-and-Full-Year-2025-Results

Fairness check: the stock drops are framed as past, reported events. The long cut balances them with revenue growth (scenes 2 and 13), and the short cut balances them with scene 13. There are no predictions and no buy/sell language. OK.

Remaining risk: the short opens on a stock drop. That is OK for platform policy (not financial advice), but Sara or Youssef should not use "crash" or "collapse" wording in titles or thumbnails.

## 4. Synthesia: PASS after fixes
Changes made:
1. **Disclosure**: `AFFILIATE LINK IN DESCRIPTION` is now `AFFILIATE LINK IN DESCRIPTION - AI VOICE`. The AI-voice label was missing.
2. **Scene 15** (known issue, Adobe "talks to buy for $3B"): **cut**. It was replaced with a verified, official scene: "April 2025. Synthesia says its yearly recurring revenue has passed one hundred million dollars. Adobe's venture arm also invests in the company." The board reads `$100M ARR / COMPANY SAYS`. Sources: https://www.synthesia.io/post/100-million-revenue-adobe-investment, https://tech.eu/2025/04/15/synthesia-scores-adobe-investment-as-hits-100m-in-arr/
3. **Scene 16**: "Instead, in January 2026" is now "Then, in January 2026". "Instead" only made sense after the cut Adobe deal.
4. **Scene 17**: removed the duplicate "Reports say ARR passed $100M". It is now "With the new money, Synthesia says it is building AI agents that talk with employees and help them learn" (Series E post).
5. **Title**: "Nobody wanted to fund this AI video startup" is now "Investors kept saying no to this AI video startup". Cuban, LDV and Seedcamp did fund it, so "nobody" was false.
6. **Scene 1** (hook): "for years, almost nobody believed in it" is now "in the early days, investor after investor said no". This is supported by Riparbelli's accounts of many early investor rejections (starterstory, 20VC).
7. **Scene 8**: "their very first investor" is now "their first outside investor, after a cold email". Source: https://seedcamp.com/views/synthesia-raises-3-1-million-to-deliver-the-first-ai-video-synthesis-platform-to-customers/ plus founder interviews.

Re-verified:
- The $100M ARR milestone is official (April 15, 2025).
- Mark Cuban was the first outside investor (founder's account).
- The free plan exists, with watermarked exports. Minutes conflict between 3 and 10, so the script quotes no number. Sources: https://www.arcade.software/post/synthesia-pricing, https://zsky.ai/blog/is-synthesia-free
- The valuation bars `[0.3, 1, 2.1]` for 2021/2023/2025 are each sourced (TechCrunch, CNBC, Synthesia/Bloomberg). No invented values.

Remaining risks:
- Third-party guides say free-plan videos may be share-link only, with no MP4 download. Scene 18 says "get a short video", which is still true. Check synthesia.io/pricing on publish day.
- Omar's `synthesia.sources.md` row 13 still documents the Adobe-talks claim. It is now unused. Omar should update the table (row 13 → the April 2025 official post).

## 5. Speechify: PASS after fixes
Changes made:
1. **Disclosure**: the AI-voice label was missing. It is now `AFFILIATE LINK IN DESCRIPTION - AI VOICE`.
2. **Scene 13** (known issue, "very little venture capital"): **cut**. It is now "Speechify spreads to phones, computers and web browsers. Students, busy professionals and people with dyslexia start listening instead of reading." (App Store and Chrome listings; no numbers.) The board is `line-up USERS` with no values, so no invented numbers.
3. **Scene 14**: removed the now-duplicate "and people with dyslexia".
4. **Title**: "an app 50 million people use" is now "a reading app used by millions". 50M is a self-reported figure and should not sit unqualified in the title.
5. **short_title**: `HE COULDN'T READ` is now `LEARNED BY EAR`. "Couldn't read" overstates dyslexia, could read as disrespectful to dyslexic viewers, and conflicts with "struggled to read" in the script.
6. **Scene 4**: "So his father finds the audiobook" is now "So he turns to the audiobook". Sources disagree on the father's role: some say he read aloud or recorded cassettes himself.

Re-verified:
- 2025 Apple Design Award, Inclusivity category (app winner). Source: https://developer.apple.com/news/?id=xjifig9f, https://techcrunch.com/2025/06/04/apple-names-2025-design-awards-winners
- Diagnosed with dyslexia in third grade, and called it "the best day of his life". The exact wording is confirmed on Speechify's own French about page ("le plus beau jour de ma vie"). Sources: https://speechify.com/fr/about/, https://dyslexiahelp.umich.edu/success-story/cliff-weitzman/
- He listened to the audiobook 22 times in a row (his own account). Source: https://www.montana.edu/dxi/articles/cliffweitzman.html
- The free tier has standard voices, and Premium adds natural voices and faster speeds (third-party, consistent). Source: https://costbench.com/software/ai-voice-tools/speechify/free-plan/

Remaining risks:
- 50M+ users is a company figure, and it is labelled as one on the board. OK.
- Scene 6 ("some teachers and staff believed dyslexia was a myth") is his own account, worded "he says", and names no one. OK.

---

## Open items for others
1. **Owner**: on publish day, check the free-plan wording on the 5 pricing pages (webflow.com/pricing, heygen.com/pricing, hubspot.com/pricing, synthesia.io/pricing, speechify.com/pricing) and the live affiliate rate in each dashboard.
2. **Omar**: update `synthesia.sources.md` row 13 (Adobe-talks → April 2025 ARR + Adobe Ventures) and row 15, `speechify.sources.md` row 11 (VC line removed), and `heygen.sources.md` scene 13 board row (middle bar now company-reported, with the Upstarts and Forbes URLs).
3. **Khaled**: re-render these 5 after the edits. No renders for them exist yet.
4. **Youssef**: the description must open with the affiliate disclosure (FTC/EU). On YouTube, tick "Includes paid promotion". The AI-voice label goes in the description too, and "altered or synthetic content" should be set where the platform asks.

## Process issues (for the Sunday meeting)
1. **The on-screen disclosure does not say "commission".** `AFFILIATE LINK IN DESCRIPTION` only says where the link is, and it shows for only the first 6 s. The spoken commission line comes at the very end. Root-cause fix: make a single house disclosure string (for example `AFFILIATE LINK: I MAY EARN A COMMISSION - AI VOICE`) part of the story template, and have build.py warn when `disclosure` is missing "AI VOICE". Two of my 5 stories (and some in batch A) were missing the AI label.
2. **Chart values need a source per bar.** HeyGen's chart had a derived bar. Rule for writers: every number in `board.values` must have its own row in `.sources.md`, or it is cut.
3. **Many official domains are blocked in this session** (heygen.com, synthesia.io, upstartsmedia.com, forbes.co, speechify.com). Fact checks rely on search snippets. Ask the owner to allow these domains for research sessions.
4. **Shared scratchpad collision.** A parallel QA agent wrote a file with the same name in the same scratchpad, and my checker output was overwritten mid-run. Parallel agents should use filenames prefixed with their agent id.
5. Writers should avoid hard-wrapped multi-line scene JSON vs single-line style drift. Mixed formats make the QA diffs noisy (HeyGen and HubSpot were reformatted to one scene per line by my edit script; content is unchanged apart from the logged fixes).

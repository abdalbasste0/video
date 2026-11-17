# 10 - QA, story scripts batch A (T-002)

Reviewer: Badr (qa-reviewer). Date checked: **2026-11-17**.
Scope: `stories/elevenlabs.json`, `fireflies.json`, `lovable.json`, `descript.json`, `kit.json` and their `.sources.md`.
The other 5 stories (webflow, heygen, hubspot, synthesia, speechify) are batch B. They are not covered here.

## Summary

| Story | Verdict | Edits | 9:16 cut (estimate*) | Glyphs |
|---|---|---|---|---|
| ElevenLabs | **PASS after fixes** | 1 | 58.0 s (6 scenes) | OK |
| Fireflies.ai | **PASS after fixes** | 3 | 55.8 s (6 scenes) | OK |
| Lovable | **PASS after fixes** | 3 | 52.7 s (5 scenes) | OK |
| Descript | **PASS after fixes** | 3 | 55.7 s (6 scenes) | OK |
| Kit | **PASS after fixes** | 3 | 56.9 s (6 scenes) | OK |

*The estimate uses the engine formula (words / 2.6 + 0.7 s). The real length follows the Sofia VO. If a 9:16 VO runs past 60 s, YouTube Shorts needs a trim. The limit in `config.platforms.youtube.max_short_seconds` is 60.

All 5 JSON files pass `python3 -m json.tool` after the edits.

**Render warning:** `renders/elevenlabs/` already holds `landscape_16x9.mp4`, `vertical_9x16.mp4` and `vo-script*.txt`. They were made **before** these fixes. Khaled must re-render ElevenLabs, and render the others only from the fixed JSON. The VO scripts the owner pastes into VoiceStudio must come from the new build.

## Checks run on all 5 stories
- **Glyphs:** a script read the `FONT` table from `tools/pixel_story/engine.html`. It applied the engine's own normalisation (accents stripped, dashes and quotes mapped, uppercased), then checked title, subtitle, label, date, caption, every board field, `disclosure` and `short_title`. **Nothing was unsupported.** `short_title` "SIDE GIG → $13B" is drawn by ffmpeg in DejaVu Sans Bold, which has →.
- **Disclosure:** every story has `disclosure: "AFFILIATE LINK IN DESCRIPTION - AI VOICE"` on screen for the first 6 s. Every story's CTA scene, which is also the last `short` scene, says "I may earn a commission if you sign up, at no extra cost to you." The AI-voice label is present.
- **No false use claims:** no story says or implies that we use the product. ElevenLabs does not imply that our voice is made with ElevenLabs.
- **No coupons, PPC or "discount" language** anywhere. This matters for Descript, whose terms ban coupon and PPC promotion.
- **No logos.** Names appear as text only.
- **Hook and CTA:** every short starts on a hook scene (a date plus a conflict) and ends on the commission CTA.
- **Chart values (`board.values`):** each bar chart was checked against a published figure. One invented chart (Kit) was removed. The rest are listed per story below.

---

## 1. ElevenLabs: PASS after fixes

**Re-verified (web search, 2026-11-17)**
1. Feb 2026 $500M Series D, Sequoia lead, $11B valuation: confirmed. Sources: https://elevenlabs.io/blog/series-d, https://tech.eu/2026/02/04/elevenlabs-raises-500m-says-building-towards-ipo/
2. Polish state stake, June 2026, about $11M: confirmed through Vinci / BGK on 17 Jun 2026. **BGK did not disclose the size**, and the $11M (PLN 40M+) figure comes from the press. The script already says "reportedly". Sources: https://notesfrompoland.com/2026/06/18/poland-invests-11m-in-elevenlabs-to-develop-polish-ai-hub/, https://thenextweb.com/news/poland-elevenlabs-stake-ai-lab-poland, https://www.bankier.pl/wiadomosc/Powstanie-AI-Lab-Poland-Spolka-BGK-inwestuje-ponad-40-mln-zl-w-ElevenLabs-9152692.html
3. The ARR bars [100, 200, 330] are confirmed as the CEO's own figures to Bloomberg: 20 months, then +10, then +5. The narration attributes them to "the CEO". **Note:** a later ElevenLabs blog post says 2025 ended at $350M, and that it passed $500M ARR by May 2026. "About 330" is still supported. Sources: https://finance.yahoo.com/news/elevenlabs-ceo-says-voice-ai-161522538.html, https://elevenlabs.io/blog/500m-arr-and-new-investors
4. (Extra) Free plan of 10,000 credits a month: consistent across third-party guides, but the official page could not be checked. Source: https://dupple.com/learn/is-elevenlabs-free

**Changes made**
- Scene 1 (in the short): changed "users on the forum 4chan are using it to fake celebrity voices" to "fake celebrity voice clips, some linked to its tool, appear on 4chan." The reports said not every clip was confirmed as ElevenLabs, so the short now matches scene 9's wording. The word count is unchanged.

**Remaining risks**
- The free-plan credits in scenes 16-17 come from third parties only. **Owner: check elevenlabs.io/pricing on publish day.**
- The valuation may have changed after the May 2026 third close of the Series D. No new figure was found, so "$11 billion" stands.

## 2. Fireflies.ai: PASS after fixes

**Re-verified**
1. The "Fred" story: Sam Udotong's own LinkedIn post (joined calls as "Fred from Fireflies.ai", typed by hand, $100/month, pizza). Confirmed. One outlet says Udotong later called it "taken out of context", and others say he said early clients knew a human was involved. Sources: https://www.pcgamer.com/software/ai/usd1-billion-ai-company-co-founder-admits-that-its-usd100-a-month-transcription-service-was-originally-two-guys-surviving-on-pizza-and-typing-out-notes-by-hand, https://futurism.com/artificial-intelligence/fireflies-founder-startup-ai
2. $14M Series A led by Khosla in May 2021, with Canaan participating: confirmed, including on the company blog. Source: https://fireflies.ai/blog/fireflies-ai-raises-14-million-series-a-to-automate-work-from-meetings
3. The June 2025 valuation of over $1B, via a first tender offer, profitable since 2023, no primary capital since 2021: confirmed as **company-reported** (the 12 Jun 2025 press release). The script attributes it. Sources: https://fireflies.ai/blog/fireflies-1-billion-valuation/, https://www.businesswire.com/news/home/20250612531860/en

**Changes made**
- Scene 7 (in the short): added "They say early clients knew a human was helping." This is a fairness fix. Without it the 9:16 cut shows only "Fred is really two broke founders" and none of the founders' side, which is in scene 9 and outside the short.
- Scene 2 (16:9 only): changed "how a fake robot became a real one" to "how a human "robot" became real AI". This takes the word "fake" out of our own voice. The board in scene 9 keeps the open question "FAKE IT TILL YOU MAKE IT?", which is fine as a question.
- Scene 16: changed "You invite Fred to your Zoom..." to "You invite its AI note-taker to your Zoom...". The current product name of the bot was not verified, so we no longer claim it is called Fred.

**Remaining risks**
- The usage claims (20M+ people, 500K+ orgs, 3 of 4 in the Fortune 500) are company claims. The script attributes them ("The company says").
- Free-plan details are third-party. **Owner: check fireflies.ai/pricing.**
- This is a tone-sensitive story. The title says "the 'AI' that was two founders typing", which is the founder's own account, so it is acceptable. Do not add "fraud" or "scam" in titles or descriptions (note for Sara and Youssef).

## 3. Lovable: PASS after fixes

**Re-verified**
1. Aug 2026: $400M Series C at a $13.3B valuation, Menlo lead with the EQT-managed Scaleup Europe Fund as co-lead. The Dec 2025 round was $330M at $6.6B. Confirmed on lovable.dev/blog/series-c and in the press. Sources: https://tech.eu/2026/08/12/lovables-valuation-doubles-to-13bn-as-raises-400m/, https://www.antler.co/press-releases/antler-portfolio-company-lovable-raises-400m-series-c-at-13-3b-valuation
2. CVE-2025-48757 (CVSS 9.3): the score is real, but **the NVD record is tagged "disputed"**. Lovable says each customer is responsible for protecting their app's data. The script presented it without the dispute, so it was fixed. Source: https://nvd.nist.gov/vuln/detail/CVE-2025-48757
3. ARR of $100M (Jul 2025) and $400M (Feb 2026) with 146 employees: confirmed as **company-reported and unaudited**, from TechCrunch (Mar 2026) and BI quoting the CRO. The bars [100, 400] match these published figures, and the narration attributes them. Source: https://techcrunch.com/2026/03/11/lovable-says-it-added-100m-in-revenue-last-month-alone-with-just-146-employees/

**Changes made**
- Scene 9: changed "a security researcher finds that many apps built with Lovable leave user data exposed" to "reports that many apps ... could leave user data exposed".
- Scene 10 narration: now reads "The issue gets an official security code. Lovable disputes it, saying each app owner must protect their own data, but it also ships a security scanner." I removed the paraphrased quote "not yet where it wants to be", which had only one source.
- Scene 10 board: changed "SCORE 9.3 / 10" to "DISPUTED BY LOVABLE".

**Remaining risks**
- The free plan's "few credits every day" is from third parties. **Owner: check lovable.dev/pricing.**
- The affiliate terms conflict ($100 flat vs 20% of 12 payments). No figure appears on screen, which is correct. The owner should confirm in the dashboard.
- Later reports put Lovable at $500-600M ARR. The script's "around 400 million by early 2026" is still correct for that date.

## 4. Descript: PASS after fixes

**Re-verified**
1. Groupon's Q4 2012 net loss was $81.1M, the stock fell about 26% after hours, and Mason was fired the next day: confirmed. Source: https://www.statista.com/chart/946/groupon-s-latest-financial-results, plus the cbsnews and qz links in the sources file.
2. Dec 2017 launch with a $5M seed from a16z (Alex Rampell): confirmed. Source: https://techcrunch.com/2017/12/12/descript-gets-5m-to-make-sound-editing-like-a-word-document/
3. Nov 2022: $50M Series C led by the OpenAI Startup Fund, with about $550M valuation **reported by The Information and not disclosed by the company**. The script says "reported ... about". Confirmed. Source: https://techcrunch.com/2022/11/15/ai-powered-media-editing-app-descript-lands-fresh-cash-from-openai
4. (Extra) Burkhauser became CEO in 2025 and Mason executive chairman: confirmed. The month differs between sources (Aug or Sep), and the script only says 2025. Source: https://www.producthunt.com/p/descript/descript-s-andrew-mason-transitions-from-ceo-to-executive-chairman

**Changes made**
- Scene 5 board: changed "EDITING TIME = 2× RECORDING" to "EDITING TOOK / LONGER THAN RECORDING". The 2x figure has a single secondary source (Contrary). The narration keeps "reportedly", but the board showed it as a fact.
- Scene 9 (in the short): changed "with 5 million dollars from the investors Andreessen Horowitz" to "with 5 million dollars in seed money from Andreessen Horowitz". The old wording was grammatically off.
- Scene 16 board: changed "2017: FOUNDER AGAIN" to "2017: DESCRIPT". This was a factual error. Mason was a founder again with Detour (about 2013-14), not first in 2017.

**Remaining risks**
- The free-plan limits (media allowance, watermark) are third-party. **Owner: check descript.com/pricing.**
- Descript affiliate terms: **no PPC bidding and no coupon sites**. Youssef must not add "coupon", "promo code" or "discount" to titles, descriptions or tags.

## 5. Kit (ConvertKit): PASS after fixes

**Re-verified**
1. $3K MRR in Jan 2015 and $97K in Dec 2015 (bars [3, 97]): confirmed on Nathan Barry's own timeline. The $50K went in Oct 2014 per his profit page, and one third-party source says Dec 2014. The date card "OCT 2014" matches his own page. Sources: https://nathanbarry.com/profit/, https://nathanbarry.com/2015-review/
2. Seva rename: announced 1 Jul 2018 at Craft + Commerce and reversed by 31 Jul 2018. "Within weeks" is correct. Sources: https://domainnamewire.com/2018/07/31/convertkit-decides-against-renaming-as-seva/, https://nathanbarry.com/rename/
3. "Still self-funded" and the "~$50M/yr" figure: estimates range from $43.8M (Latka, 2024) to $52M (Sacra, 2025). Bootstrapping is widely repeated, but some directories list $1.8-3.3M of funding and one claims an institutional round. **I could not prove "self-funded"**, so I removed it. Sources: https://getlatka.com/companies/convertkit, https://sacra.com/research/convertkit

**Changes made**
- Scene 5 board: **removed invented bar values** [2, 2.4, 2, 1.6, 1.3] (labels M1-M18). The sources file called them "illustrative shape, not exact data". The board is now a text board: "SLOW GROWTH / PART-TIME".
- Scene 15: changed "Today Kit is still self-funded." to "Today Kit serves creators around the world." The estimate sentence and its "APPROX. OUTSIDE ESTIMATE" board stay.
- Scene 16 (in the short): now reads "That tool is ConvertKit, now called Kit. From thirteen hundred dollars a month to **an estimated** tens of millions a year...". The short had no brand name before the CTA, and "tens of millions" was stated as fact even though it is an outside estimate. The hedge in scene 15 is not in the short.

**Remaining risks**
- **Owner: check the free Newsletter plan (10,000 subscribers) on kit.com/pricing** on publish day. The source is the official help center.
- The commission tiers after month 12 come from a third party. Nothing is said on screen.

---

## Fixes for others (not done by me)
1. **Khaled (video-editor):** re-render ElevenLabs. The existing `renders/elevenlabs/*` predates the fixes. Render Fireflies, Lovable, Descript and Kit only from the current JSON.
2. **Owner (via Yasmin):** before publishing, open the 5 pricing pages and confirm the free-plan claims (elevenlabs.io/pricing, fireflies.ai/pricing, lovable.dev/pricing, descript.com/pricing, kit.com/pricing). Also confirm the live commission in each affiliate dashboard.
3. **Youssef (publisher):** in every description, add "Affiliate link: we may earn a commission" above the fold. On YouTube, check the "altered or synthetic content" rule for an AI narrator voice at upload. If in doubt, tick it. On TikTok, set the AI-generated label. The on-screen "AI VOICE" stays either way. No coupon or PPC wording (Descript, ElevenLabs).
4. **Sara and Youssef:** in the Fireflies titles and thumbnails, don't call it "fraud", "scam" or "fake company".

## Process issues (for the Sunday meeting)
1. **Invented chart values got into a script.** The Kit sources file openly said the bars were "illustrative". Root cause: nothing tells writers that `bars` must use published numbers. Fix: add one line to Omar's agent file and to `tools/pixel_story/README.md`: "`bars` values must be published figures with a source row; otherwise use `line-up`/`line-down`".
2. **Board text gets no hedge.** The narration said "reportedly", but the board showed the bare figure (Descript 2x). Rule: if a claim is single-source, the board shows no number.
3. **The short cut loses context.** Fairness lines and hedges sit in scenes not marked `short` (Fireflies "clients knew", Kit "outside estimates"). Rule for writers: every `short` scene must stand alone, with attribution kept inside that scene.
4. **Rendering started before QA.** ElevenLabs renders exist from the pre-QA JSON. The pipeline order is scripts, then QA, then render. Khaled's task should wait for Badr's PASS, or renders should be marked "pre-QA".
5. **Official pricing and affiliate pages are DNS-blocked in this session.** Every free-plan claim is therefore third-party. This is a standing owner check until the network allows those hosts.
6. **The CTA wording is inconsistent with the house disclosure line.** Narration uses "I may earn" and Fahad's note uses "we may earn". Both are compliant, but we should pick one house line.

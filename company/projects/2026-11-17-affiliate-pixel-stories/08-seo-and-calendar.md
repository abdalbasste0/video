# 08 - SEO and publishing calendar: Pixel Stories (T-002)

Prepared by Sara (growth-analyst) for Yasmin and Youssef. Date: 2026-11-17.
Inputs: `brief.md`, `01-affiliate-products.md`, `products.json`, `stories/*.json` (read after Badr's QA edits of 16:47 UTC today; titles below follow the QA'd wording).

## Read first
- **No keyword volumes.** OpenSEO is not connected (it would need a pay-as-you-go DataForSEO key) and `paid_research_allowed` is false. Keywords below are picked from free web search: how people and publishers phrase these stories ("<company> story", "how <company> started", founder names, the product category). They are **judgement, not measured demand**. When OpenSEO is running, I will re-rank tags with real volumes.
- **No analytics yet.** `company/analytics/` has no data, so the times below are the starting heuristics from `config.json → posting_windows`. I will not change the windows until we have 10 or more posts of evidence.
- **Chapters are estimates.** Timestamps come from the silent-render timing (2.6 words per second, `tools/pixel_story/build.py`). When the Sofia voiceover is added, every scene is stretched by the same factor, so each timestamp must be multiplied by (VO length ÷ silent length), or read from the final `renders/<id>/timed_16x9.json`. Youssef: recompute before upload. YouTube rules: first chapter at 0:00, at least 3 chapters, each at least 10 seconds ([Storyblocks](https://www.storyblocks.com/resources/tutorials/how-to-add-chapters-to-youtube-video), [Adaptlypost](https://adaptlypost.com/blog/youtube-chapters-requirements)). All chapters below are at least 17 seconds long in the silent timing.
- **Title length.** All long titles are 46-51 characters (limit 60). Third-party guides say mobile can cut titles at about 50-55 characters, so the company name and the hook are at the start ([Fluxnote](https://fluxnote.io/guides/youtube-title-character-limit-2026), [AIR Media Tech](https://air.io/en/audience-growth/how-to-write-a-youtube-title-that-gets-clicked-research-across-11-niches)).
- **Disclosure.** Every description has the affiliate disclosure **before** the link, and every pinned comment labels the link. The FTC says to disclose a material connection (commissions count) clearly and conspicuously, and not to rely on platform tools alone ([FTC: Disclosures 101](https://www.ftc.gov/business-guidance/resources/disclosures-101-social-media-influencers)). Short captions say "Affiliate link in bio" where space allows, and the short itself already says "I may earn a commission" on screen and in the voiceover.
- **AI label.** Each description says the narration is an AI voice. On upload, also set YouTube's "altered or synthetic content" answer ([YouTube Help](https://support.google.com/youtube/answer/14328491)), plus the AI-generated content setting on TikTok and Meta. The owner decides on the toggles; my recommendation is "Yes" for the voice, to be safe.
- **"[AFFILIATE LINK]"** is a placeholder. The owner pastes the real link only after the program has approved him and he has read the live rate in the dashboard (Fahad's rule).

## Publishing order
Order = commission score × story score from Fahad's ranking (`products.json → scores`). Ties are broken by Fahad's total.

| Slot | Video | Commission | Story | Comm × Story | Fahad total | Program to be approved first |
|---|---|---|---|---|---|---|
| 1 | Webflow | 9 | 9 | 81 | 32 | Webflow (PartnerStack) |
| 2 | Kit (ConvertKit) | 9 | 8 | 72 | 33 | Kit (PartnerStack) |
| 3 | HubSpot | 9 | 8 | 72 | 31 | HubSpot (direct affiliate platform) |
| 4 | Fireflies.ai | 7 | 10 | 70 | 35 | Fireflies.ai (direct) |
| 5 | ElevenLabs | 8 | 8 | 64 | 35 | ElevenLabs (PartnerStack) |
| 6 | Lovable | 6 | 10 | 60 | 34 | Lovable (own affiliate platform, Impact reported) |
| 7 | HeyGen | 7 | 8 | 56 | 32 | HeyGen (Rewardful) |
| 8 | Synthesia | 8 | 7 | 56 | 31 | Synthesia (Rewardful) |
| 9 | Speechify | 6 | 8 | 48 | 30 | Speechify (Dub partners) |
| 10 | Descript | 4 | 10 | 40 | 33 | Descript (PartnerStack) |

**Swap rule:** if a program has not approved the owner 48 hours before its slot, swap it with the next approved video. Do not publish a video with a placeholder or a non-affiliate link "for now": the views from the first days would earn nothing.

## Calendar (24 Nov - 18 Dec 2026)

Ten long videos over 4 weeks (2, 3, 3, 2 per week) on Tue / Thu / Sat. Each 9:16 short goes out **the day after** its long video, on a day with no long upload, so the short can point to a long video that is already live (YouTube Shorts "related video" link, and "Full story on YouTube" on the other platforms). No uploads on Thu 26 Nov (US Thanksgiving). The run ends before the Christmas week.

Both markets are on winter time in this period (New York UTC-5, Paris UTC+1, a 6-hour gap). The owner's clock is Paris, so the **Paris column is the owner's time**.

**Fixed times per platform (from `posting_windows`):**

| Post | New York | Paris (owner) | Why |
|---|---|---|---|
| YouTube long (16:9) | 12:00 | 18:00 | The golden slot: inside both YouTube windows |
| Facebook long (16:9, same day) | 09:00 | 15:00 | Overlap of the Facebook US (09-12) and EU (13-15) windows |
| YouTube Short | 12:00 | 18:00 | Golden slot again |
| Instagram Reel | 13:00 | 19:00 | Edge of both Instagram windows (US 11-13, EU 19-21) |
| Facebook Reel | 09:00 | 15:00 | Same overlap as above |
| TikTok, slots 1, 3, 5, 7, 9 | 19:00 | 01:00 (next day) | US window. Schedule it in TikTok Studio the evening before |
| TikTok, slots 2, 4, 6, 8, 10 | 14:00 | 20:00 | EU window |

The TikTok windows do not overlap, so I alternate them. That gives 5 posts in each window: after the run I can compare them (a test, not a conclusion yet).

| Slot | Video | Long: YouTube + Facebook | Short: YT Shorts, Reels, Facebook, TikTok | TikTok time (NY / Paris) |
|---|---|---|---|---|
| 1 | Webflow | Tue 24 Nov | Wed 25 Nov | 19:00 / 01:00 Thu |
| 2 | Kit | Sat 28 Nov | Sun 29 Nov | 14:00 / 20:00 |
| 3 | HubSpot | Tue 1 Dec | Wed 2 Dec | 19:00 / 01:00 Thu |
| 4 | Fireflies.ai | Thu 3 Dec | Fri 4 Dec | 14:00 / 20:00 |
| 5 | ElevenLabs | Sat 5 Dec | Sun 6 Dec | 19:00 / 01:00 Mon |
| 6 | Lovable | Tue 8 Dec | Wed 9 Dec | 14:00 / 20:00 |
| 7 | HeyGen | Thu 10 Dec | Fri 11 Dec | 19:00 / 01:00 Sat |
| 8 | Synthesia | Sat 12 Dec | Sun 13 Dec | 14:00 / 20:00 |
| 9 | Speechify | Tue 15 Dec | Wed 16 Dec | 19:00 / 01:00 Thu |
| 10 | Descript | Thu 17 Dec | Fri 18 Dec | 14:00 / 20:00 |

**Ready-by dates (work back from slot 1):** the Webflow voiceover, final render, Badr's QA and the Webflow approval must be done by **Sun 22 Nov**, so Youssef can schedule on Mon 23 Nov. Then keep at least 2 videos finished ahead of the calendar.

**Weekly cadence change:** `config.cadence.long_videos_per_week` is 1, and this plan runs 2-3. That is Yasmin's brief for this project. I have not changed `config.json`.

## Per-video SEO packs

### 1. Webflow (Tue 24 Nov long, Wed 25 Nov short)

- **Story file**: `stories/webflow.json` · silent render length about 2:49
- **Affiliate program that must be approved before publishing**: Webflow via PartnerStack (https://webflow.com/solutions/affiliates). Commission as published: 50% of first subscription for up to 12 months (Base tier). Cookie is 30 or 90 days (conflicting): confirm in the PartnerStack dashboard. No self-purchase commissions.
- **Search angle (no volumes, see method)**: "webflow story", "how Webflow started", "vlad magdalin", "no-code website builder"

**YouTube title** (49 chars)
```
Webflow Failed 3 Times. The 4th Try Was Worth $4B
```
**YouTube description**
```
He failed to launch the same idea in 2005, 2007 and 2008. Then Y Combinator said no.
This is how Webflow went from broke and rejected to a $4 billion company, told in pixel art.

Affiliate disclosure: the link below is an affiliate link. If you sign up, I may earn a commission at no extra cost to you.
Try Webflow's free Starter plan: [AFFILIATE LINK]

Chapters:
0:00 Rejected, with a family to feed
0:17 Three failed launches
0:51 Try number four, no money
1:14 20,000 sign-ups overnight
1:38 Y Combinator, then $4 billion
2:20 How to use Webflow free

Sources: https://webflow.com/blog/the-story-of-how-webflow-and-y-combinator · https://en.wikipedia.org/wiki/Webflow · https://review.firstround.com/webflows-path-to-product-market-fit-lessons-on-creating-a-market-with-rigorous-customer-empathy (full claim-by-claim list available on request)

Narration is an AI voice. Pixel animation made for this channel. Company names are used for identification only; no logos. Facts checked on 2026-11-17; numbers marked "reportedly" or "the company says" are not independently confirmed.

#webflow #startupstory #nocode
```
**YouTube tags (3)**: `webflow story`, `vlad magdalin`, `no-code website builder`

**Shorts / TikTok / Reels / Facebook caption** (125 chars, hashtags not counted)
```
He failed 3 times. Y Combinator said no. The 4th try became Webflow, worth $4B. Full story on YouTube. Affiliate link in bio.
#webflow #startupstory #nocode #founderstory #pixelart
```
Hashtags per platform: TikTok and Instagram use all 5; YouTube Shorts and Facebook use the first 3 (`#webflow #startupstory #nocode`).

**Pinned comment (YouTube long + Short; first comment on Facebook)**
```
Want to try it? Webflow's free Starter plan: [AFFILIATE LINK] (affiliate link: I may earn a commission at no extra cost to you). Would you have tried a 4th time?
```

### 2. Kit (Sat 28 Nov long, Sun 29 Nov short)

- **Story file**: `stories/kit.json` · silent render length about 2:54
- **Affiliate program that must be approved before publishing**: Kit via PartnerStack (https://kit.com/affiliate). Commission as published: 50% for 12 months, then 10-20% recurring at Bronze/Silver/Gold. Cookie (90 days) is 3rd-party only: confirm. 50% for 12 months.
- **Search angle (no volumes, see method)**: "convertkit story", "how Kit started", "nathan barry", "email newsletter for creators"

**YouTube title** (46 chars)
```
Kit (ConvertKit): Shut It Down or Double Down?
```
**YouTube description**
```
October 2014: a small email tool makes about $1,300 a month, and a friend says shut it down or double down.
This is how ConvertKit, now Kit, went from there to an estimated tens of millions a year, told in pixel art.

Affiliate disclosure: the link below is an affiliate link. If you sign up, I may earn a commission at no extra cost to you.
Start Kit's free Newsletter plan: [AFFILIATE LINK]

Chapters:
0:00 $1,300 a month
0:20 A side project in public
0:57 The double-down decision
1:41 The name mistake
2:09 Kit today
2:28 How to use Kit free

Sources: https://medium.com/@nathanbarry/growing-convertkit-to-5-020-in-monthly-recurring-revenue-91f10094d8a1 · https://www.indiehackers.com/interview/2fcb58f1fa · https://www.indiehackers.com/post/the-story-of-convertkit-from-0-to-597-000-in-monthly-revenue-YuYm5Me8di4KbnVkESy8 (full claim-by-claim list available on request)

Narration is an AI voice. Pixel animation made for this channel. Company names are used for identification only; no logos. Facts checked on 2026-11-17; numbers marked "reportedly" or "the company says" are not independently confirmed.

#convertkit #newsletter #startupstory
```
**YouTube tags (3)**: `convertkit story`, `nathan barry`, `email newsletter for creators`

**Shorts / TikTok / Reels / Facebook caption** (129 chars, hashtags not counted)
```
$1,300 a month. Shut it down or double down? One choice turned ConvertKit into Kit. Full story on YouTube. Affiliate link in bio.
#convertkit #newsletter #startupstory #creatoreconomy #pixelart
```
Hashtags per platform: TikTok and Instagram use all 5; YouTube Shorts and Facebook use the first 3 (`#convertkit #newsletter #startupstory`).

**Pinned comment (YouTube long + Short; first comment on Facebook)**
```
Start a newsletter free (up to 10,000 subscribers on Kit's free plan): [AFFILIATE LINK] (affiliate link: I may earn a commission at no extra cost to you). Would you have shut it down?
```

### 3. HubSpot (Tue 1 Dec long, Wed 2 Dec short)

- **Story file**: `stories/hubspot.json` · silent render length about 2:57
- **Affiliate program that must be approved before publishing**: HubSpot via Direct (HubSpot affiliate platform) (https://www.hubspot.com/partners/affiliates). Commission as published: 30% recurring for up to 12 months. Check HubSpot's affiliate brand rules (trademark bidding, wording) before posting.
- **Search angle (no volumes, see method)**: "hubspot story", "how HubSpot started", "inbound marketing", "free crm"

**YouTube title** (49 chars)
```
HubSpot Gave Its Best Product Away for Free. Why?
```
**YouTube description**
```
In 2014 HubSpot made its riskiest bet: a CRM, with the core version free. A few weeks later it went public.
Here is the 20-year story of the company that taught the world inbound marketing, told in pixel art.

Affiliate disclosure: the link below is an affiliate link. If you sign up, I may earn a commission at no extra cost to you.
Get HubSpot's free CRM: [AFFILIATE LINK]

Chapters:
0:00 A 20% drop in one day
0:23 Two MIT students and inbound marketing
1:07 The free CRM bet and the IPO
1:36 When Alphabet came knocking
2:06 $3.13 billion and the AI question
2:27 How to use the free CRM

Sources: https://ir.hubspot.com · https://en.wikipedia.org/wiki/HubSpot · https://www.fool.com/investing/2026/05/08/why-hubspot-plunged-today/ (full claim-by-claim list available on request)

Narration is an AI voice. Pixel animation made for this channel. Company names are used for identification only; no logos. Facts checked on 2026-11-17; numbers marked "reportedly" or "the company says" are not independently confirmed.

#hubspot #crm #startupstory
```
**YouTube tags (3)**: `hubspot story`, `inbound marketing`, `free crm`

**Shorts / TikTok / Reels / Facebook caption** (126 chars, hashtags not counted)
```
HubSpot gave its best product away for free. Then Google's parent came knocking. Full story on YouTube. Affiliate link in bio.
#hubspot #crm #startupstory #smallbusiness #pixelart
```
Hashtags per platform: TikTok and Instagram use all 5; YouTube Shorts and Facebook use the first 3 (`#hubspot #crm #startupstory`).

**Pinned comment (YouTube long + Short; first comment on Facebook)**
```
Try HubSpot's free CRM (no expiry date): [AFFILIATE LINK] (affiliate link: I may earn a commission at no extra cost to you). Will AI replace software like this, or power it?
```

### 4. Fireflies.ai (Thu 3 Dec long, Fri 4 Dec short)

- **Story file**: `stories/fireflies.json` · silent render length about 2:59
- **Affiliate program that must be approved before publishing**: Fireflies.ai via Direct (https://fireflies.ai/affiliate). Commission as published: Up to 30% recurring for 12 months (tiered). Use the direct program, not the Awin listing (5%). Payout minimum not published: ask partners@fireflies.ai.
- **Search angle (no volumes, see method)**: "fireflies ai story", "how Fireflies started", "ai meeting notes", "ai notetaker"

**YouTube title** (50 chars)
```
Fireflies.ai's 'AI' Started as Two Founders Typing
```
**YouTube description**
```
A silent guest named Fred joins a client call. Fred is supposed to be an AI note-taker. Fred is really two broke founders, typing by hand.
This is how Fireflies.ai went from a human 'bot' to a company valued at over $1 billion, told in pixel art.

Affiliate disclosure: the link below is an affiliate link. If you sign up, I may earn a commission at no extra cost to you.
Try Fireflies.ai free: [AFFILIATE LINK]

Chapters:
0:00 Fred joins the call
0:21 Pivot after pivot
0:49 Fred was human
1:33 Fred becomes real software
1:59 Profitable, then $1 billion
2:28 How to use Fireflies free

Sources: https://www.pcgamer.com/software/ai/usd1-billion-ai-company-co-founder-admits-that-its-usd100-a-month-transcription-service-was-originally-two-guys-surviving-on-pizza-and-typing-out-notes-by-hand · https://fireflies.ai/blog/fireflies-1-billion-valuation/ · https://www.aol.com/articles/ai-startups-viral-linkedin-story-112801605.html (full claim-by-claim list available on request)

Narration is an AI voice. Pixel animation made for this channel. Company names are used for identification only; no logos. Facts checked on 2026-11-17; numbers marked "reportedly" or "the company says" are not independently confirmed.

#firefliesai #AItools #startupstory
```
**YouTube tags (3)**: `fireflies ai story`, `ai meeting notes`, `ai notetaker`

**Shorts / TikTok / Reels / Facebook caption** (137 chars, hashtags not counted)
```
'Fred' the AI note-taker was two founders typing by hand (clients knew, they say). Now Fireflies.ai is worth $1B+. Full story on YouTube.
#firefliesai #AItools #startupstory #productivity #pixelart
```
Hashtags per platform: TikTok and Instagram use all 5; YouTube Shorts and Facebook use the first 3 (`#firefliesai #AItools #startupstory`).

**Pinned comment (YouTube long + Short; first comment on Facebook)**
```
Want an AI note-taker in your next call? Fireflies.ai free plan: [AFFILIATE LINK] (affiliate link: I may earn a commission at no extra cost to you). Always tell people you are recording.
```

### 5. ElevenLabs (Sat 5 Dec long, Sun 6 Dec short)

- **Story file**: `stories/elevenlabs.json` · silent render length about 2:56
- **Affiliate program that must be approved before publishing**: ElevenLabs via PartnerStack (https://elevenlabs.io/affiliates). Commission as published: 22% of payments for first 12 months (11% Business, 0% Enterprise). Terms ban cookie stuffing, self-referral and fake coupon or cash-back promises. Our narration is VoiceStudio, never imply it is ElevenLabs.
- **Search angle (no volumes, see method)**: "elevenlabs story", "how ElevenLabs started", "ai voice generator", "mati staniszewski"

**YouTube title** (47 chars)
```
ElevenLabs: From Deepfake Crisis to $11 Billion
```
**YouTube description**
```
January 2023: a tiny voice startup opens its beta, and within days fake celebrity voice clips, some linked to its tool, appear online.
This is how ElevenLabs survived its worst week and became an $11 billion company, told in pixel art.

Affiliate disclosure: the link below is an affiliate link. If you sign up, I may earn a commission at no extra cost to you.
Try ElevenLabs free: [AFFILIATE LINK]

Chapters:
0:00 The worst week
0:19 Two friends and flat movie dubbing
0:48 Building a voice that feels human
1:17 The deepfake crisis
1:45 The road to $11 billion
2:25 How to use ElevenLabs free

Sources: https://www.engadget.com/ai-voice-tool-deepfake-celebrity-audio-clips-094648743.html · https://oecd.ai/en/incidents/2023-01-30-b00c · https://fintool.com/news/elevenlabs-11b-valuation-series-d (full claim-by-claim list available on request)

Narration is an AI voice. Pixel animation made for this channel. Company names are used for identification only; no logos. Facts checked on 2026-11-17; numbers marked "reportedly" or "the company says" are not independently confirmed.

#elevenlabs #AIvoice #AItools
```
**YouTube tags (3)**: `elevenlabs story`, `ai voice generator`, `mati staniszewski`

**Shorts / TikTok / Reels / Facebook caption** (119 chars, hashtags not counted)
```
Its first public week went badly: fake celebrity voices. 3 years later ElevenLabs is worth $11B. Full story on YouTube.
#elevenlabs #AIvoice #AItools #startupstory #pixelart
```
Hashtags per platform: TikTok and Instagram use all 5; YouTube Shorts and Facebook use the first 3 (`#elevenlabs #AIvoice #AItools`).

**Pinned comment (YouTube long + Short; first comment on Facebook)**
```
Try ElevenLabs free: [AFFILIATE LINK] (affiliate link: I may earn a commission at no extra cost to you). Only clone voices you have permission to use. (This video's narration is not made with ElevenLabs.)
```

### 6. Lovable (Tue 8 Dec long, Wed 9 Dec short)

- **Story file**: `stories/lovable.json` · silent render length about 3:01
- **Affiliate program that must be approved before publishing**: Lovable via Lovable affiliate platform (Impact reported) (https://lovable.dev/partners/affiliates). Commission as published: Up to $100 per first-time subscriber (docs say 20% of first 12 payments - conflicting). Terms conflict (up to $100 per subscriber vs 20% of first 12 payments): confirm in the dashboard. Pricing changes often.
- **Search angle (no volumes, see method)**: "lovable story", "how Lovable started", "vibe coding", "ai app builder"

**YouTube title** (50 chars)
```
Lovable: A GitHub Side Project Worth $13.3 Billion
```
**YouTube description**
```
June 2023: a Swedish engineer puts a free side project on GitHub. In August 2026 it is valued at $13.3 billion.
This is the story of Lovable, the app builder you talk to, told in pixel art.

Affiliate disclosure: the link below is an affiliate link. If you sign up, I may earn a commission at no extra cost to you.
Try Lovable free: [AFFILIATE LINK]

Chapters:
0:00 $13.3 billion from Stockholm
0:17 GPT Engineer goes viral
0:45 Rebuilt for people who can't code
1:12 The security wake-up call
1:33 $100 million in eight months
2:28 How to use Lovable free

Sources: https://techcrunch.com/2026/03/11/lovable-says-it-added-100m-in-revenue-last-month-alone-with-just-146-employees/ · https://siliconangle.com/2026/08/12/vibe-coding-startup-lovable-doubles-valuation-13-3b-400m-raise/ · https://www.indiehackers.com/post/tech/hitting-100m-arr-in-eight-months-with-an-ai-software-builder-ONMaxjB3rix2PnBCnrDr (full claim-by-claim list available on request)

Narration is an AI voice. Pixel animation made for this channel. Company names are used for identification only; no logos. Facts checked on 2026-11-17; numbers marked "reportedly" or "the company says" are not independently confirmed.

#lovable #vibecoding #AItools
```
**YouTube tags (3)**: `lovable story`, `vibe coding`, `ai app builder`

**Shorts / TikTok / Reels / Facebook caption** (122 chars, hashtags not counted)
```
A side project on GitHub in 2023. Valued at $13.3B in 2026. How Lovable did it, built in Stockholm. Full story on YouTube.
#lovable #vibecoding #AItools #startupstory #pixelart
```
Hashtags per platform: TikTok and Instagram use all 5; YouTube Shorts and Facebook use the first 3 (`#lovable #vibecoding #AItools`).

**Pinned comment (YouTube long + Short; first comment on Facebook)**
```
Build your first app by chatting: Lovable free plan: [AFFILIATE LINK] (affiliate link: I may earn a commission at no extra cost to you). What would you build first?
```

### 7. HeyGen (Thu 10 Dec long, Fri 11 Dec short)

- **Story file**: `stories/heygen.json` · silent render length about 2:54
- **Affiliate program that must be approved before publishing**: HeyGen via Rewardful (https://www.heygen.com/affiliate-program). Commission as published: 30-35% recurring for 3-6 months (official pages conflict). Official pages conflict (35% for 3 months vs up to 30% for 6 months): confirm the live rate in Rewardful.
- **Search angle (no volumes, see method)**: "heygen story", "how HeyGen started", "ai avatar video", "joshua xu"

**YouTube title** (50 chars)
```
HeyGen: The Camera-Shy Founder Behind $200M a Year
```
**YouTube description**
```
Its founder did not feel comfortable on camera, so he built AI that makes the video for you.
This is how HeyGen reached over $200 million a year in recurring revenue, the company says, told in pixel art.

Affiliate disclosure: the link below is an affiliate link. If you sign up, I may earn a commission at no extra cost to you.
Try HeyGen free: [AFFILIATE LINK]

Chapters:
0:00 $200 million, no camera
0:21 From Snapchat to a new start
0:53 178 days to $1 million
1:22 A new name and a hard choice
1:53 The curve goes up
2:22 How to use HeyGen free

Sources: https://www.heygen.com/blog/heygen-surpasses-200m-arr · https://www.heygen.com/blog/0-1m-arr-in-7-months · https://www.upstartsmedia.com/p/exclusive-heygen-200m-arr-without-burn (full claim-by-claim list available on request)

Narration is an AI voice. Pixel animation made for this channel. Company names are used for identification only; no logos. Facts checked on 2026-11-17; numbers marked "reportedly" or "the company says" are not independently confirmed.

#heygen #AIvideo #AItools
```
**YouTube tags (3)**: `heygen story`, `ai avatar video`, `joshua xu`

**Shorts / TikTok / Reels / Facebook caption** (131 chars, hashtags not counted)
```
He didn't like being on camera, so he built AI that makes the video. HeyGen says it now earns $200M+ a year. Full story on YouTube.
#heygen #AIvideo #AItools #startupstory #pixelart
```
Hashtags per platform: TikTok and Instagram use all 5; YouTube Shorts and Facebook use the first 3 (`#heygen #AIvideo #AItools`).

**Pinned comment (YouTube long + Short; first comment on Facebook)**
```
Make your first AI avatar video: HeyGen free plan: [AFFILIATE LINK] (affiliate link: I may earn a commission at no extra cost to you). Would you use an avatar of yourself?
```

### 8. Synthesia (Sat 12 Dec long, Sun 13 Dec short)

- **Story file**: `stories/synthesia.json` · silent render length about 2:59
- **Affiliate program that must be approved before publishing**: Synthesia via Rewardful (https://synthesia.io/partners/affiliates). Commission as published: 25% of net payments, 12 months, up to $267 per referral. 25% of net, Starter/Creator only (Enterprise excluded). Cookie 60 days is 3rd-party only.
- **Search angle (no volumes, see method)**: "synthesia story", "how Synthesia started", "ai video generator", "ai avatar training videos"

**YouTube title** (51 chars)
```
Investors Kept Saying No to Synthesia. Now It's $4B
```
**YouTube description**
```
In the early days, investor after investor said no to a London startup that made videos talk with AI.
This is how Synthesia went from a research paper to a $4 billion company, told in pixel art.

Affiliate disclosure: the link below is an affiliate link. If you sign up, I may earn a commission at no extra cost to you.
Try Synthesia free: [AFFILIATE LINK]

Chapters:
0:00 $4 billion, after years of no
0:19 A research paper and four founders
0:49 The hard years
1:18 David Beckham speaks nine languages
1:52 Unicorn, $100M revenue, then $4 billion
2:36 How to use Synthesia free

Sources: https://synthesia.io/post/series-e-200-million-4-billion-valuation-future-work · https://siliconangle.com/2026/01/26/synthesia-raises-200m-4b-valuation-build-worker-skills-using-ai-avatars/ · https://sifted.eu/articles/synthesia-ai-interview (full claim-by-claim list available on request)

Narration is an AI voice. Pixel animation made for this channel. Company names are used for identification only; no logos. Facts checked on 2026-11-17; numbers marked "reportedly" or "the company says" are not independently confirmed.

#synthesia #AIvideo #AItools
```
**YouTube tags (3)**: `synthesia story`, `ai video generator`, `ai avatar training videos`

**Shorts / TikTok / Reels / Facebook caption** (114 chars, hashtags not counted)
```
Investors kept saying no. Then David Beckham spoke 9 languages. Now Synthesia is worth $4B. Full story on YouTube.
#synthesia #AIvideo #AItools #startupstory #pixelart
```
Hashtags per platform: TikTok and Instagram use all 5; YouTube Shorts and Facebook use the first 3 (`#synthesia #AIvideo #AItools`).

**Pinned comment (YouTube long + Short; first comment on Facebook)**
```
Make a training video from a script: Synthesia free plan: [AFFILIATE LINK] (affiliate link: I may earn a commission at no extra cost to you). What would you use it for?
```

### 9. Speechify (Tue 15 Dec long, Wed 16 Dec short)

- **Story file**: `stories/speechify.json` · silent render length about 2:51
- **Affiliate program that must be approved before publishing**: Speechify via Direct (Dub partners) (https://speechify.com/affiliates/). Commission as published: 30% of every sale. Use 30% (official), ignore blog claims of 40-50%. Commissions reversed on refunds.
- **Search angle (no volumes, see method)**: "speechify story", "how Speechify started", "cliff weitzman", "text to speech app"

**YouTube title** (51 chars)
```
Speechify: He Struggled to Read, So He Built an App
```
**YouTube description**
```
As a boy with dyslexia he listened to the same audiobook 22 times. At Brown University he coded his way around reading.
This is the story of Speechify and Cliff Weitzman, told in pixel art.

Affiliate disclosure: the link below is an affiliate link. If you sign up, I may earn a commission at no extra cost to you.
Try Speechify free: [AFFILIATE LINK]

Chapters:
0:00 An Apple Design Award
0:18 Dyslexia and Harry Potter
0:59 Code in a dorm room
1:36 Beating free text-to-speech
2:05 50 million users
2:28 How to use Speechify free

Sources: https://dyslexiahelp.umich.edu/success-story/cliff-weitzman/ · https://developer.apple.com/news/?id=xjifig9f · https://techcrunch.com/2025/06/04/apple-names-2025-design-awards-winners (full claim-by-claim list available on request)

Narration is an AI voice. Pixel animation made for this channel. Company names are used for identification only; no logos. Facts checked on 2026-11-17; numbers marked "reportedly" or "the company says" are not independently confirmed.

#speechify #dyslexia #texttospeech
```
**YouTube tags (3)**: `speechify story`, `cliff weitzman`, `text to speech app`

**Shorts / TikTok / Reels / Facebook caption** (133 chars, hashtags not counted)
```
Diagnosed with dyslexia in 3rd grade, he learned by listening. Then he built Speechify. Full story on YouTube. Affiliate link in bio.
#speechify #dyslexia #texttospeech #startupstory #pixelart
```
Hashtags per platform: TikTok and Instagram use all 5; YouTube Shorts and Facebook use the first 3 (`#speechify #dyslexia #texttospeech`).

**Pinned comment (YouTube long + Short; first comment on Facebook)**
```
Listen to any PDF or web page: Speechify free version: [AFFILIATE LINK] (affiliate link: I may earn a commission at no extra cost to you). Do you learn better by reading or listening?
```

### 10. Descript (Thu 17 Dec long, Fri 18 Dec short)

- **Story file**: `stories/descript.json` · silent render length about 2:58
- **Affiliate program that must be approved before publishing**: Descript via PartnerStack (https://www.descript.com/affiliate). Commission as published: $25 flat one-time per new paid subscriber (no renewals, $100k annual cap). $25 one-time only. Terms ban paid search bidding and coupon-site promotion. Do not mix with Descript's user-referral link.
- **Search angle (no volumes, see method)**: "descript story", "how Descript started", "andrew mason", "edit video by editing text"

**YouTube title** (47 chars)
```
Descript: How a Fired CEO Rebuilt Video Editing
```
**YouTube description**
```
February 2013: the CEO of Groupon writes a memo with one line that goes viral: I was fired today.
This is how Andrew Mason's next idea became Descript, the editor where you cut video by editing text, told in pixel art.

Affiliate disclosure: the link below is an affiliate link. If you sign up, I may earn a commission at no extra cost to you.
Try Descript free: [AFFILIATE LINK]

Chapters:
0:00 I was fired today
0:27 Detour and a painful edit
1:16 Descript goes solo
1:51 OpenAI money and a new CEO
2:27 How to use Descript free

Sources: https://money.cnn.com/2013/02/28/technology/groupon-ceo-andrew-mason/ · https://techcrunch.com/2018/04/24/bose-acquires-andrew-masons-walking-tour-startup-detour · https://techcrunch.com/2022/11/15/ai-powered-media-editing-app-descript-lands-fresh-cash-from-openai (full claim-by-claim list available on request)

Narration is an AI voice. Pixel animation made for this channel. Company names are used for identification only; no logos. Facts checked on 2026-11-17; numbers marked "reportedly" or "the company says" are not independently confirmed.

#descript #videoediting #podcasting
```
**YouTube tags (3)**: `descript story`, `andrew mason`, `edit video by editing text`

**Shorts / TikTok / Reels / Facebook caption** (132 chars, hashtags not counted)
```
'I was fired today.' Groupon's ex-CEO built a tool to edit video like a doc: Descript. Full story on YouTube. Affiliate link in bio.
#descript #videoediting #podcasting #startupstory #pixelart
```
Hashtags per platform: TikTok and Instagram use all 5; YouTube Shorts and Facebook use the first 3 (`#descript #videoediting #podcasting`).

**Pinned comment (YouTube long + Short; first comment on Facebook)**
```
Edit video by deleting words: Descript free plan: [AFFILIATE LINK] (affiliate link: I may earn a commission at no extra cost to you). What's the worst part of editing for you?
```

## Pre-publish checklist (per slot, Youssef)
1. The program in the pack is **approved**, and the owner has read the live rate in the dashboard. Paste the real link in place of `[AFFILIATE LINK]` in the description and the pinned comment, and in the link-in-bio for TikTok / Instagram (and Facebook if used).
2. Sofia's VO is in, the final render is done, and Badr's QA has passed.
3. Recompute the chapters from the final timing (see "Read first").
4. Set the AI / synthetic-content answers on each platform. Set the Short's "related video" to the long video.
5. Owner `/approve`. Nothing is scheduled without it.

## Sources used for this file
- YouTube chapter rules: https://www.storyblocks.com/resources/tutorials/how-to-add-chapters-to-youtube-video · https://adaptlypost.com/blog/youtube-chapters-requirements
- Title truncation (3rd-party estimates): https://fluxnote.io/guides/youtube-title-character-limit-2026 · https://air.io/en/audience-growth/how-to-write-a-youtube-title-that-gets-clicked-research-across-11-niches
- FTC disclosure guidance: https://www.ftc.gov/business-guidance/resources/disclosures-101-social-media-influencers
- YouTube synthetic-content disclosure: https://support.google.com/youtube/answer/14328491 · https://blog.youtube/news-and-events/disclosing-ai-generated-content
- Programs, commissions and story facts: `01-affiliate-products.md`, `products.json` and `stories/<id>.sources.md` (Fahad, Omar and Badr, checked 2026-11-17). The URLs in each description are taken from those files.

# Shot list - T-001 - "Is this Black Friday deal fake?"

- Producer: Mariam (recording-producer), 2026-11-17
- Source: `02-script-short.md` (final), `03-hooks.md`, `brief.md`
- Total time for you: about 25 min (setup 5, demo 10-15, voiceover 5). Order: **part 0 -> part A (demo) -> part C (voiceover)**. Part B is made by Khaled, not you.
- Part A is the same job as needs_you **N-002** (Noura): doing it closes N-002. Send Noura the verdict, [X] days and the timed seconds when done.
- Save every file in `company/projects/2026-11-17-first-short/raw/` with the file names below.

## Part 0 - Setup (once, 5 min)

| # | Step | Exact action |
|---|---|---|
| 0.1 | Clean browser | Open a **guest / private window** (Chrome: profile icon -> Guest; Firefox/Safari: new private window). No bookmarks bar, no extensions, no account avatar or name on screen. Close all other tabs. |
| 0.2 | Dark mode | OS dark mode on (Windows: Settings -> Personalization -> Colors -> Dark; macOS: System Settings -> Appearance -> Dark). The chatbot follows it. Store pages may stay light; that is fine. |
| 0.3 | Zoom 125% | In each tab: `Ctrl` + `+` (Windows) or `Cmd` + `+` (Mac) until the zoom badge shows **125%**. Check it again in every new tab. |
| 0.4 | 9:16 crop area | Make the browser window **tall and narrow**: about **608 x 1080 px** (or 720 x 1280 on a larger screen) and place it on the left of the screen. Everything important must stay inside it. The top 15% and bottom 20% of the frame are covered by platform buttons and captions: keep prices and verdicts in the **middle 65%**. |
| 0.5 | Recorder | Windows: OBS Studio (free), add "Window Capture" of the browser, 1080x1920 canvas, 30 fps. macOS: `Cmd` + `Shift` + `5` -> "Record Selected Portion" -> draw the box on the browser window. Mouse cursor visible. No microphone in this recording. |
| 0.6 | Quiet screen | Do Not Disturb on (no notification pop-ups). Close mail and chat apps. |
| 0.7 | Cookie banners | Open each page once before recording and accept/close the cookie and location pop-ups, so they don't appear on camera. |

## Part A - The real demo (you record; = N-002)

Rule: **never stage a result.** Whatever the chatbot says is what the video shows. Do A1-A6 for one **EU store** and one **US store**, then pick the clearer one for the video (Noura's note: price history coverage differs by country).

| Shot | Used at | What to record | Exact clicks | Length | File name |
|---|---|---|---|---|---|
| **A1** Product page | 0:00-0:03 (hook) and 0:19 | A real Black Friday product page with a crossed-out "was" price and a % badge. | 1. Go to a big store's Black Friday page (EU examples: amazon.de / amazon.fr / mediamarkt.de / fnac.com; US examples: bestbuy.com / walmart.com / amazon.com). 2. Pick a product with: crossed-out "was" price, % badge, **exact model number** on the page (TV, headphones, robot vacuum, smartwatch work best). 3. Start recording. 4. Hold still 3 s on the price block. 5. Slowly scroll so the model name and price are both visible, hold 3 s. 6. Click the address bar and copy the link (`Ctrl/Cmd` + `L`, then `C`). | 15 s | `A1-product-eu.mov` / `A1-product-us.mov` |
| **A2** Chatbot, search on | 0:15-0:19 | A new, empty chat in any **free chatbot that can search the web** and shows source links. | 1. Open the chatbot in a new tab (zoom 125% again). 2. Log out or use guest mode if possible; otherwise hide/crop the account name. 3. New chat. 4. Turn **web search on** if it is a toggle/button. If you can't see a web-search option on the free plan, use another chatbot. Don't record anything that names a paid plan. | 5 s | `A2-chat-empty.mov` |
| **A3** Paste prompt + fill brackets | 0:19-0:23 | The prompt being pasted, then link + 2 prices + country typed into the brackets. | 1. Copy the prompt from `02-script-short.md` ("Prompt on screen") into a text file first, with your product's values already filled in: link, sale price, "was" price, country. 2. Start recording. 3. Paste it in one go (`Ctrl/Cmd` + `V`). 4. Click on each filled value (link, sale price, "was" price) for 1 s so Khaled can highlight them. Do **not** press Enter yet. | 10 s | `A3-prompt-paste.mov` |
| **A4** Answer streaming + timing | 0:23-0:31 | The full answer streaming in, **real time**, no scrolling until it stops. | 1. Keep recording from A3 (or start a new one). 2. Look at the clock / start a phone stopwatch, then press **Enter**. 3. Don't touch anything while it writes. 4. Stop the stopwatch when the **verdict line** (REAL DEAL / FAKE DISCOUNT / NOT SURE) appears. 5. Write the seconds down (teleprompter checklist + tell Noura). Khaled can re-check it from the file. | 20-90 s | `A4-answer-eu.mov` / `A4-answer-us.mov` |
| **A5** Verdict + price-history zoom | 0:31-0:37 | The lines of the answer that prove the verdict: lowest price with dates, how long the "was" price was charged, the verdict line, the source links. | 1. Scroll slowly up to the price-history lines (item 1 and 2 of the answer). Hold 3 s. 2. Scroll slowly to the verdict line. Hold 4 s. 3. Move the cursor over the source links without clicking. Khaled zooms in later; don't zoom the browser now. | 15 s | `A5-verdict.mov` |
| **A6** Click a source | 0:37-0:40 | Clicking one source link in the answer and the page opening. | 1. Click one source link that shows a price. 2. Let the page load and stay on it 3 s. 3. Close the tab. | 6 s | `A6-source-click.mov` |

### A7 - Check the answer off camera (2 min, not recorded)

Open every source link in the answer and confirm the prices it quotes really appear there. If a link is broken or a price is not on the page, treat the result as **NOT SURE** (or run it on the other store). Never put a price on screen that you could not see on the source page.

### A8 - Pick the version (fill in, then send to Noura)

| | EU store | US store |
|---|---|---|
| Product (model) | | |
| Discount shown (for hook text, e.g. -40%) | | |
| Verdict (REAL DEAL / FAKE DISCOUNT / NOT SURE) | | |
| [X] days from the answer | | |
| Seconds to verdict (A4) | | |
| Sources checked OK (A7)? | | |

Then use the matching version everywhere:

| Verdict used in video | Teleprompter block 7 | On-screen card at 0:31 (Khaled) | Title note |
|---|---|---|---|
| FAKE DISCOUNT | "(FAKE)" lines | **FAKE: "was" price lasted [X] days** | Hook #2 may be A/B tested as a second cut (Hala) |
| REAL DEAL | "(REAL)" lines | **REAL: lowest price in [X] days** | Use hook #1 only |
| NOT SURE | "(NOT SURE)" lines | **NOT SURE = no proof. Wait.** | Use hook #1 only |

If A4 took **20 s or less**, the YouTube title may say "20 sec" (see `03-hooks.md`). If longer, keep titles without a number or say "under a minute".

## Part B - Graphics (Khaled builds, nothing for you to record)

| Used at | Item | Note |
|---|---|---|
| 0:00-0:03 | REAL / FAKE stamps flickering over A1 price, no stamp lands; **-[real %]: REAL or FAKE?** text | Blur store logo and product brand in A1. |
| 0:03-0:09 | Animated price line (price jumps up, plateau, "sale" drops back) | Our own graphic. |
| 0:10-0:17 | EU rule text card + source line "EU Directive 98/6/EC, Art. 6a" | |
| 0:15-0:19 and 0:40-0:46 | Prompt full-screen, large monospace, "SCREENSHOT THIS" | From the text in `02-script-short.md`, not from a recording. On screen at least 3 s in total. |
| 0:23-0:31 | Small timer in the corner, 0 -> real seconds | From A4. If A4 is trimmed, add a "sped up" label. |
| 0:46-0:49 | End card "Follow for one AI shortcut a day" | No third-party logos. |
| all | Blur: store logos, product brand names, chatbot logo, any account name/avatar, cookie text | We don't name or accuse a retailer. |

## Part C - Voiceover (you record, after part A)

Use `teleprompter.md`. 3 takes of the hook, 1-2 takes of the rest, phone mic at least 15 cm away, quiet room. File names: `C-vo-hook-take1.m4a` (2, 3), `C-vo-full-take1.m4a`.

## Hand-off checklist

- [ ] `raw/` holds A1-A6 (both stores if you did both) + C files.
- [ ] A8 table filled in and sent to Noura (closes N-002).
- [ ] Seconds to verdict written down (title decision).
- [ ] Tell Yasmin "recorded" so Khaled can start the edit.

# AI voiceover (owner chose AI voice on 2026-11-17)

- Tool: ElevenLabs, model eleven_v4, flow "Shortcut HQ - first short voiceover" (xMLMToHs6FELR3qmdm5P)
- Voice: **Laura - Enthusiast, Quirky Attitude** (voice_id FGY2WhTYpPnrIDTdsKH5, premade, young American female, social media). Chosen by the owner from his sample (`audio/owner_voice_sample_laura.mp3`). (Mira was the first pick; replaced.)
- Status:
  - Take 1, full track NOT SURE version: **GENERATED** 2026-11-17, 48.72 s, 761 credits (generation gXEu5DKYoAHbwo0yPHKu). The download host elevenlabsusercontent.com is blocked from this cloud session, so the owner downloads it from the ElevenLabs flow and uploads it to `audio/vo_full_notsure_laura.mp3`.
  - Takes 2 and 3 (FAKE / REAL lines): not generated yet (ElevenLabs free tier was busy). Only needed if the demo verdict isn't "not sure".
- Because the voice is AI: the "AI-generated / altered content" label is REQUIRED on YouTube, TikTok, Instagram and Facebook (see 07-publish-plan.md).

## Takes to generate (3)
1. **Full track, NOT SURE version** (blocks 1-10, the default):
   > [curious] Is this Black Friday deal real... or fake? One prompt tells you. Here's the trick. Some stores raise the "was" price a few weeks before the sale, so the discount looks huge. In the EU, that old price must be the lowest price from the last thirty days. Not every shop plays fair. So copy this prompt into any free chatbot that can search the web. Paste the product link, the sale price, and the "was" price. It looks up recent prices, checks two other stores, and gives a verdict: real deal, fake discount, or not sure. Here, it says not sure: no price history found. That's a reason to wait. Always click the sources before you buy. Screenshot the prompt, and send it to the friend who's about to buy that TV. Follow for one AI shortcut a day.
2. **FAKE verdict line** (replaces block 7): "Here, it's fake. The "was" price barely lasted."
3. **REAL verdict line** (replaces block 7): "Here, it's real. This is the lowest recent price. Good deal, if the sources check out."

No numbers are spoken, so the voiceover never claims a figure the demo didn't show. If the demo gives a day count, regenerate line 2 or 3 with "[X] days".

## After generating
Khaled downloads the takes to `company/inbox/footage/`, splices the matching verdict into the full track with ffmpeg, then renders with `tools/render_short.py --voiceover`. Reem re-times the SRTs to the real audio.

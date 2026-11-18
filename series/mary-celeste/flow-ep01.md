# Google Flow: The Mary Celeste, part 1

## Settings (the same for every scene)
- **Image:** model Nano Banana, 16:9 ratio, one result.
- **Video:** add the scene image, model Omni Flash (or Veo Fast), 720p, 8 seconds, 16:9.
- **Character consistency:** add the matching reference image from the `refs` folder as an *ingredient* with every scene that has a character.
- **Saving:** name each clip after the scene number, e.g. `shot03.mp4`, and put it in the `clips/mary-celeste-ep01/` folder (or upload to Google Drive and send me the link).
- You don't have to do every scene: any scene without a clip is animated automatically in code.

## Style (already included in every prompt)

> Hand-painted storybook cartoon illustration, cinematic 16:9 frame, warm natural light with soft god rays, rich painted backgrounds with brush texture, clean dark ink outlines. All people are simple stickman characters with large plain white round heads, simple black dot eyes and thick expressive eyebrows, thin limbs, black outline, wearing 1870s clothing.

---
### Scene 01  →  save as `shot01.mp4`

*Narration:* November, eighteen seventy-two. In New York harbor, a small two-masted ship called the Mary Celeste was getting ready to cross the Atlantic.

**Image prompt:**
```
Hand-painted storybook cartoon illustration, cinematic 16:9 frame, warm natural light with soft god rays, rich painted backgrounds with brush texture, clean dark ink outlines. All people are simple stickman characters with large plain white round heads, simple black dot eyes and thick expressive eyebrows, thin limbs, black outline, wearing 1870s clothing. A wide view of New York harbor in November 1872, grey morning, wooden piers, a small two-masted brigantine named Mary Celeste being loaded with barrels, seagulls.
```
**Animation prompt:**
```
Slow push-in toward the ship, seagulls flying, water gently moving, sailors carrying barrels. Keep the same art style and character design, no text, no subtitles.
```

---
### Scene 02  →  save as `shot02.mp4`

*Narration:* Her captain was Benjamin Briggs, an experienced and careful sailor. This time, he brought his wife, Sarah, and their two-year-old daughter, Sophia.

**Image prompt:**
```
Hand-painted storybook cartoon illustration, cinematic 16:9 frame, warm natural light with soft god rays, rich painted backgrounds with brush texture, clean dark ink outlines. All people are simple stickman characters with large plain white round heads, simple black dot eyes and thick expressive eyebrows, thin limbs, black outline, wearing 1870s clothing. On the wooden deck of a small sailing ship in harbor, the captain stands with his wife and their little daughter, smiling, masts and ropes behind them. Captain Benjamin Briggs: white round head with a short dark-brown beard along the jaw, navy peaked captain's cap with a gold badge, long navy blue coat, dark trousers, brown boots. Sarah Briggs: white round head, dark brown hair in a bun, long burgundy 1870s dress with a white collar. Sophia, a 2-year-old girl: small, white round head, short light-brown hair, cream dress.
```
**Animation prompt:**
```
The family looks around the ship, the little girl points at a seagull, flags and ropes sway in the breeze, slow camera dolly. Keep the same art style and character design, no text, no subtitles.
```
Reference images: `refs/captain.png`, `refs/wife.png`, `refs/child.png`

---
### Scene 03  →  save as `shot03.mp4`

*Narration:* With them were seven crewmen. Ten people in all.

**Image prompt:**
```
Hand-painted storybook cartoon illustration, cinematic 16:9 frame, warm natural light with soft god rays, rich painted backgrounds with brush texture, clean dark ink outlines. All people are simple stickman characters with large plain white round heads, simple black dot eyes and thick expressive eyebrows, thin limbs, black outline, wearing 1870s clothing. Sailors working on the deck of a small brigantine, pulling ropes and rolling a barrel, sails being raised. a sailor: white round head, red knit cap, off-white jacket, navy trousers. a sailor: white round head, green knit cap, short black beard, brown jacket, grey trousers.
```
**Animation prompt:**
```
One sailor pulls a rope hand over hand, the other rolls a barrel, sails flutter, light camera pan. Keep the same art style and character design, no text, no subtitles.
```
Reference images: `refs/sailor.png`, `refs/sailor2.png`

---
### Scene 04  →  save as `shot04.mp4`

*Narration:* In the hold were one thousand seven hundred and one barrels of industrial alcohol, bound for Genoa, Italy.

**Image prompt:**
```
Hand-painted storybook cartoon illustration, cinematic 16:9 frame, warm natural light with soft god rays, rich painted backgrounds with brush texture, clean dark ink outlines. All people are simple stickman characters with large plain white round heads, simple black dot eyes and thick expressive eyebrows, thin limbs, black outline, wearing 1870s clothing. Inside a dark wooden ship's cargo hold lit by a lantern, rows of stacked wooden barrels of alcohol.
```
**Animation prompt:**
```
Lantern light flickers and sways, slow push along the rows of barrels, dust floating in the light. Keep the same art style and character design, no text, no subtitles.
```

---
### Scene 05  →  save as `shot05.mp4`

*Narration:* On November seventh, the Mary Celeste set sail.

**Image prompt:**
```
Hand-painted storybook cartoon illustration, cinematic 16:9 frame, warm natural light with soft god rays, rich painted backgrounds with brush texture, clean dark ink outlines. All people are simple stickman characters with large plain white round heads, simple black dot eyes and thick expressive eyebrows, thin limbs, black outline, wearing 1870s clothing. A small two-masted brigantine with full white sails leaving harbor at sunset, orange and purple sky, calm sea.
```
**Animation prompt:**
```
The ship sails slowly across the frame, waves roll, sails fill with wind, sunset light shimmers on the water. Keep the same art style and character design, no text, no subtitles.
```

---
### Scene 07  →  save as `shot07.mp4`

*Narration:* Something was wrong. The ship was moving strangely, as if no one was steering. Some sails were set. Others were torn, or missing.

**Image prompt:**
```
Hand-painted storybook cartoon illustration, cinematic 16:9 frame, warm natural light with soft god rays, rich painted backgrounds with brush texture, clean dark ink outlines. All people are simple stickman characters with large plain white round heads, simple black dot eyes and thick expressive eyebrows, thin limbs, black outline, wearing 1870s clothing. Open Atlantic ocean on a bright day, a lone two-masted brigantine in the distance with some sails torn and loose, drifting strangely; a second sailing ship in the foreground.
```
**Animation prompt:**
```
The distant ship drifts and turns oddly, torn sails flapping, waves rolling, the camera slowly zooms toward it. Keep the same art style and character design, no text, no subtitles.
```

---
### Scene 08  →  save as `shot08.mp4`

*Narration:* The Dei Gratia's captain recognized her. It was the Mary Celeste. They signaled. There was no answer.

**Image prompt:**
```
Hand-painted storybook cartoon illustration, cinematic 16:9 frame, warm natural light with soft god rays, rich painted backgrounds with brush texture, clean dark ink outlines. All people are simple stickman characters with large plain white round heads, simple black dot eyes and thick expressive eyebrows, thin limbs, black outline, wearing 1870s clothing. A lonely two-masted sailing ship with torn sails drifting in thick sea fog, no one visible on deck, eerie grey light.
```
**Animation prompt:**
```
Fog drifts past, the ship rocks slowly on the waves, a torn sail flaps, very slow push-in, eerie mood. Keep the same art style and character design, no text, no subtitles.
```

---
### Scene 09  →  save as `shot09.mp4`

*Narration:* Three men rowed across and climbed aboard.

**Image prompt:**
```
Hand-painted storybook cartoon illustration, cinematic 16:9 frame, warm natural light with soft god rays, rich painted backgrounds with brush texture, clean dark ink outlines. All people are simple stickman characters with large plain white round heads, simple black dot eyes and thick expressive eyebrows, thin limbs, black outline, wearing 1870s clothing. Two sailors climbing over the rail onto the wet deck of a foggy abandoned ship, an open cargo hatch, coiled ropes. a sailor: white round head, red knit cap, off-white jacket, navy trousers. a sailor: white round head, green knit cap, short black beard, brown jacket, grey trousers.
```
**Animation prompt:**
```
The two sailors step onto the deck and look around nervously, fog drifts, the ship creaks and rocks. Keep the same art style and character design, no text, no subtitles.
```
Reference images: `refs/sailor.png`, `refs/sailor2.png`

---
### Scene 10  →  save as `shot10.mp4`

*Narration:* There was no one on board. Not one single person.

**Image prompt:**
```
Hand-painted storybook cartoon illustration, cinematic 16:9 frame, warm natural light with soft god rays, rich painted backgrounds with brush texture, clean dark ink outlines. All people are simple stickman characters with large plain white round heads, simple black dot eyes and thick expressive eyebrows, thin limbs, black outline, wearing 1870s clothing. The empty wet deck of an abandoned sailing ship in fog, ship's wheel turning by itself, an open hatch, no people at all.
```
**Animation prompt:**
```
The wheel slowly turns on its own, ropes sway, fog rolls across the empty deck, slow camera pan. Keep the same art style and character design, no text, no subtitles.
```

---
### Scene 11  →  save as `shot11.mp4`

*Narration:* Below deck, everything was damp, but in order. Clothes. Personal belongings. Even the sailors' pipes had been left behind.

**Image prompt:**
```
Hand-painted storybook cartoon illustration, cinematic 16:9 frame, warm natural light with soft god rays, rich painted backgrounds with brush texture, clean dark ink outlines. All people are simple stickman characters with large plain white round heads, simple black dot eyes and thick expressive eyebrows, thin limbs, black outline, wearing 1870s clothing. A damp wooden captain's cabin below deck: a bunk, a table with a logbook, clothes hanging, a child's toy on the floor, a round porthole, a sailor looking around in shock. a sailor: white round head, green knit cap, short black beard, brown jacket, grey trousers.
```
**Animation prompt:**
```
The hanging lamp swings, the sailor slowly looks around the cabin, dust in the light, slow push-in. Keep the same art style and character design, no text, no subtitles.
```
Reference images: `refs/sailor2.png`

---
### Scene 12  →  save as `shot12.mp4`

*Narration:* The cargo was almost untouched. And there was enough food and fresh water on board for six months.

**Image prompt:**
```
Hand-painted storybook cartoon illustration, cinematic 16:9 frame, warm natural light with soft god rays, rich painted backgrounds with brush texture, clean dark ink outlines. All people are simple stickman characters with large plain white round heads, simple black dot eyes and thick expressive eyebrows, thin limbs, black outline, wearing 1870s clothing. Ship's storeroom with sacks of food, water casks and barrels, all untouched, lit by soft light through the planks.
```
**Animation prompt:**
```
Slow camera glide past the supplies, light flickers through the planks, dust floats. Keep the same art style and character design, no text, no subtitles.
```

---
### Scene 13  →  save as `shot13.mp4`

*Narration:* There was water below, about three and a half feet of it in the hold. But the ship was not sinking. She was seaworthy.

**Image prompt:**
```
Hand-painted storybook cartoon illustration, cinematic 16:9 frame, warm natural light with soft god rays, rich painted backgrounds with brush texture, clean dark ink outlines. All people are simple stickman characters with large plain white round heads, simple black dot eyes and thick expressive eyebrows, thin limbs, black outline, wearing 1870s clothing. A sailor kneeling by an open cargo hatch on a wet deck, looking down at water sloshing in the dark hold below. a sailor: white round head, red knit cap, off-white jacket, navy trousers.
```
**Animation prompt:**
```
Water sloshes in the hold, the sailor leans in to look, the ship rocks gently. Keep the same art style and character design, no text, no subtitles.
```
Reference images: `refs/sailor.png`

---
### Scene 14  →  save as `shot14.mp4`

*Narration:* The last entry on the ship's log slate was dated November twenty-fifth, at eight a.m. The ship was passing the island of Santa Maria, in the Azores.

**Image prompt:**
```
Hand-painted storybook cartoon illustration, cinematic 16:9 frame, warm natural light with soft god rays, rich painted backgrounds with brush texture, clean dark ink outlines. All people are simple stickman characters with large plain white round heads, simple black dot eyes and thick expressive eyebrows, thin limbs, black outline, wearing 1870s clothing. Close-up of an old ship's logbook page by lamplight, handwritten entry, a quill pen beside it.
```
**Animation prompt:**
```
Lamplight flickers, the page edge lifts slightly in a draft, slow push-in onto the handwriting. Keep the same art style and character design, no text, no subtitles.
```

---
### Scene 16  →  save as `shot16.mp4`

*Narration:* And then they noticed what was missing. The ship's only lifeboat was gone. So were the captain's navigation instruments, and most of the ship's papers.

**Image prompt:**
```
Hand-painted storybook cartoon illustration, cinematic 16:9 frame, warm natural light with soft god rays, rich painted backgrounds with brush texture, clean dark ink outlines. All people are simple stickman characters with large plain white round heads, simple black dot eyes and thick expressive eyebrows, thin limbs, black outline, wearing 1870s clothing. The stern of a lonely sailing ship in fog, with empty lifeboat davits and cut ropes hanging where the lifeboat used to be.
```
**Animation prompt:**
```
Cut ropes swing from the empty davits, fog drifts, the ship rocks, slow push-in toward the empty space. Keep the same art style and character design, no text, no subtitles.
```

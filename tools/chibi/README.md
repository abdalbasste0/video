# Chibi map style

History-explainer look: cute big-headed characters (peg-doll bodies) standing on a vintage map, props popping in, word-by-word captions.

```
# 1) voice (once per story; same scene order as the story JSON)
CHATTERBOX_DIR=... python voice_chatterbox.py STORY.json VOICE_DIR
# 2) video (16:9 + 9:16 short)
WHISPER_DIR=... python3 tools/chibi/build.py STORY.chibi.json VOICE_DIR OUT_DIR [--preview 40]
# still image of one character/scene
node tools/chibi/still.js scene.json out.png
```

## Characters: `tools/chibi/characters/<id>.json`
One file per real person, built to resemble them (public photos/descriptions). Fields:
`name, role, note, skin (hex), hair {style: short-side|buzz|receding|curly|long|bob|bald, color}, facialHair (none|stubble|trimmed|short|moustache), facialHairColor, face {mouth: smile|grin|neutral|sad|smirk|open, brows: normal|raised|angry|worried, glasses: rect|round}, outfit {type: hoodie|tshirt|blazer|turtleneck|vest, color, accent, tie}, hat {type: cap, color}`.
Generic extras without a file: `investor`, `engineer`, `user`, `person`.
Be respectful: skin tone and hair from real appearance, no exaggerated ethnic features, no mockery.

## Story visuals: `STORY.chibi.json`
`{"story": id, "cast": {"vlad": "vlad_magdalin", ...}, "scenes": [ ... one entry per story scene, same order and count ... ]}`
Scene fields:
| field | meaning |
|---|---|
| `map` | `{"center":[lon,lat], "scale": n, "highlight":[{"country":"France"} or {"state":"California"}], "states": true, "pins":[{"lonlat":[lon,lat],"label":"Paris"}]}`. Scale guide: world 160, Atlantic/US+Europe 300, USA 900, Europe 700, one country 1500-3000, one state 2600, a metro area 9000 |
| `date` | ribbon at the top, e.g. `"MAR 2013"` |
| `characters` | `[{"id":"vlad","pos":[x,y],"to":[x,y],"mouth":"sad","brows":"worried","flip":true,"enterAt":2.0,"scale":1}]`. `pos` are fractions of the frame (feet position). Without `pos`, characters line up at the bottom. `at:[lon,lat]` pins a character to a map place. `to` makes them walk/hop there during the scene |
| `props` | `{"type": ...}` with `pos` (fractions), `at` (lon/lat), or `near: <character index>` + `side`. Types: `board` (easel; `title`, `chart`: up/down/bars, `lines`), `money` (`text`), `card` (big number; `text`, `sub`, `count`: true animates the number, `color`, `size`), `stamp` (`text`, slams in), `bubble` (`text`, speech bubble), `laptop`, `building` (`label`), `sign` (`text`, `color`, `textColor`), `title` (`lines`), `crowd` (`count` small people popping in), `arrow` (`from`/`to` lon-lat, drawn across the map). `enterAt` = seconds into the scene |
| `camera` | `{"zoom":1.1, "focus":[lon,lat]}` slow push-in |
| `dim` | 0-0.4 darkens the map (dramatic beats) |

Layout rules (16:9, works for 9:16 too): characters' feet at y 0.78-0.86; cards/titles/stamps at y ≤ 0.4 so they never cover a face; captions are added automatically at the very bottom, so keep y > 0.9 empty. Use 1-3 characters per scene, change the map region when the story moves, and time props (`enterAt`) to the narration words.

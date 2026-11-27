# Vanished at Sea: stick figure story video

A ~2-minute (2:06) 16:9 1080p stick figure story video: 25 scenes × 5 s, English narration, ambient sound design, burned-in subtitles and a thumbnail.

## Deliverables (`out/`)
| File | What |
|---|---|
| `out/vanished_at_sea_1080p.mp4` | Final video: 1920×1080, 25 fps, H.264 + AAC, subtitles burned in |
| `out/vanished_at_sea_1080p_nosubs.mp4` | Same video without burned-in subtitles (use with the .srt) |
| `out/subtitles_en.srt` | English subtitles (sidecar) |
| `out/thumbnail_en.png` | Thumbnail, "VANISHED AT SEA" |
| `out/thumbnail_ar.png` | Thumbnail, "اختفت في البحر" |
| `assets/narration.mp3` | Raw ElevenLabs voiceover (voice "Tobias – Deep, Calm, Serious", eleven_multilingual_v2) |

## How it was made
* **Voiceover**: ElevenLabs text-to-speech, one take of the full script with 1.2 s breaks between the 25 beats. `src/audio.py` splits it on those pauses and drops each beat 0.25 s after its scene cut, so every line is synced to its own 5-second clip.
* **Visuals**: the ElevenLabs account is on the free plan, which can't generate video, and its image credits wouldn't cover 25 frames. So every scene is drawn and animated in code (`src/gfx.py`, `src/scenes.py`, pycairo). Karim is one shared rig, so he looks the same in every shot. The camera is locked. Motion includes body physics (breathing, shivering, walking, recoils), water, fog, smoke, steam, rain, flickering lamps, sweeping beams and a ticking clock. No lip sync, no dialogue.
* **Sound** (`src/audio.py`): synthesized ocean surf and swell, wind, a low tension drone with pulse hits and a heartbeat, plus per-scene effects (engine, gulls, creaks, clock ticks, wave crash, sparks, radar pings, paper). Ambience is ducked under the voice.
* **Edit** (`src/render.py`): 0.3 s crossfades between scenes, fade in and out, subtitles from `build/subs.ass` (bold white, black outline, bottom center).

## Rebuild
```
pip install pycairo numpy scipy pillow
python3 src/audio.py && python3 src/subs.py && python3 src/render.py && ./src/finalize.sh
python3 src/thumbnail.py
```

## Karim (character sheet)
A young man in his twenties: big round white head, messy black spiky hair, wide worried eyes with dark under-eye lines (old fear), a faded orange life vest with reflective strips over a slightly torn gray t-shirt, dark work trousers, and a coiled tan nautical rope on his shoulder.

## Storyboard
| # | Time | Narration | Visual |
|---|---|---|---|
| 1 |   0–  5s | A ship leaves the harbor at dawn. Calm water. Engines humming. | Dawn harbor: trawler sails out past cranes; Karim on the pier raises a tense wave. Gulls, sun rays, drifting fog. |
| 2 |   5– 10s | By sunset, it's gone. No distress call. No wreckage. | Sunset: the ship's silhouette fades from the horizon; Karim steps back in shock, hands to chest. |
| 3 |  10– 15s | Not even a single drop of fuel floating on the surface. | Karim kneels on a raft and dips his fingers into a perfectly clean surface; ripples, no oil. |
| 4 |  15– 20s | The entire crew, their gear, their belongings... vanished. | Empty deck: crew ghosts and their duffel bags dissolve one by one; Karim watches, trembling. |
| 5 |  20– 25s | As if they never boarded at all. | Gangway to a moored ship; footprints fade step by step; fog rolls over the pier. |
| 6 |  25– 30s | And this isn't one story. It's a pattern, across every ocean. | Ocean map board: red disappearance markers pulse on, one by one, across every ocean; Karim points. |
| 7 |  30– 35s | Repeating, again and again, for hundreds of years. | Moonlit fog: ghostly old sailing ships fade in and out; Karim on a raft, lantern flickering. |
| 8 |  35– 40s | Here's the strange part. Most of these ships aren't small, or old. | Daylight: a giant cargo ship looms; Karim raises a finger ("here's the strange part"). |
| 9 |  40– 45s | Some are massive vessels, with modern equipment and trained crews. | A massive modern vessel with spinning radar and crew on deck; tiny Karim looks up from the dock. |
| 10 |  45– 50s | And they disappeared in calm seas, under clear skies. | Clear sky, glassy sea: a cargo ship shimmers and dissolves into nothing; Karim's hands fly to his face. |
| 11 |  50– 55s | That's exactly what makes this story so hard to shake. | Night close-up: Karim clutches his head, shivering; heartbeat. |
| 12 |  55– 60s | The mind wants a big explanation for a strange situation. | Purple dusk on the pier: Karim, hand on chin, under a growing "?" thought bubble. |
| 13 |  60– 65s | But the truth is often simpler... and harsher, at the same time. | Storm and rain: Karim sits slumped on the pier edge, legs dangling. |
| 14 |  65– 70s | Some ships were found completely empty. No violence. No struggle. | Dark cabin: Karim walks in through an open door; the lamp swings; the table is bare. |
| 15 |  70– 75s | As if the crew just stood up, and left everything behind. | Cabin: food on plates, steaming mug, chair pushed back and still rocking. |
| 16 |  75– 80s | Food still on the table. Clothes still hanging. Clocks still ticking. | Cabin: wall clock ticking with pendulum, coats swaying; Karim's eyes scan the room. |
| 17 |  80– 85s | There's no clean ending to close the case with. | Night desk: "CASE: UNSOLVED" folder, flickering lamp; Karim rubs his head. |
| 18 |  85– 90s | Investigators fall back on logic. A rogue wave... | Storm deck: a towering rogue wave rises, foam spraying, lightning; Karim recoils. |
| 19 |  90– 95s | a sudden mechanical failure... a human error at the wrong moment. | Engine room: alarm light, smoking pipe, sparks, jittering gauges; Karim coughs, bent over. |
| 20 |  95–100s | But in some cases, those explanations simply run out. | Evidence board: red strings snap, papers fly off the desk; Karim throws up his hands. |
| 21 | 100–105s | No black box. No witness. Not a single body ever turns up. | Night raft in fog: Karim sweeps a flashlight over empty water. |
| 22 | 105–110s | That's why these stories stay alive. They raise a deeper question. | Lighthouse beam sweeps the night; Karim sits alone at the end of the pier. |
| 23 | 110–115s | How does something this size vanish, in a world of satellites and radar? | Satellites cross a starry sky; a radar shows NO CONTACT; Karim looks up. |
| 24 | 115–120s | The ocean is still bigger than every tool we've invented to understand it. | Extreme wide sunset: tiny Karim on a tiny raft in a vast ocean under god rays. |
| 25 | 120–125s | The sea doesn't always leave a trace... even when it takes something this large. | Sunset beach: waves wash away Karim's footprints; he turns to face the sea; fade to black. |

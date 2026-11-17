# Pixel story engine

Turns a story JSON into a pixel-art animated video (genre: narrated company stories in a side-view pixel office).

```
python3 tools/pixel_story/build.py story.json OUT_DIR                 # silent video + captions
python3 tools/pixel_story/build.py story.json OUT_DIR --voiceover vo.mp3 --voiceover-vertical vo_short.mp3
python3 tools/pixel_story/build.py story.json OUT_DIR --preview 20     # first 20 s only
```
Outputs: `landscape_16x9.mp4` (YouTube, Facebook), `vertical_9x16.mp4` (scenes with `"short": true`, for Shorts, TikTok, Reels), SRT captions, `vo-script.txt` and `vo-script-short.txt` (paste into VoiceStudio), `cover_16x9.jpg`.
Scene length = narration words / 2.6 + 0.7 s (min 3 s) unless `dur` is set. With `--voiceover`, every scene is stretched to match the audio length.
Example covering every feature: `tools/pixel_story/examples/demo.json`.

## Story
```json
{
  "title": "How Fireflies went from fake AI to a $1B company",
  "short_title": "THE FAKE AI BOT",          // big title on the 9:16 version (keep it under 18 characters)
  "disclosure": "AFFILIATE LINK IN DESCRIPTION", // shown for the first 6 s
  "scenes": [ ... ]
}
```

## Scene fields
| field | values |
|---|---|
| `narration` | the voiceover line for this scene (English). It becomes the captions. Aim for 8-30 words per scene |
| `type` | `"title"` for a title card, with `title: ["LINE 1", "LINE 2"]`, `subtitle` and `color` |
| `room` | `office` `boardroom` `garage` `lab` `factory` `store` `deal` `stage` `server` `dorm` `night` |
| `label` | room tag top-left, e.g. `"CEO SUITE"` |
| `floors` | stack 2-3 rooms: `[{"room":"boardroom","label":"CEO SUITE","people":3,"suits":true}, {"room":"office","label":"ENGINEERING","people":6}]` (each floor takes the room fields below, plus `weight`). `"columns": true` puts them side by side |
| `people` | number of people (desks in office/lab/dorm/garage, seats at a boardroom/deal table, standing figures on stage/night/store) |
| `mode` | force `desks`, `table` or `stand` |
| `grow` | `[from, to]` people appear during the scene (hiring) |
| `leave` | `N` people leave during the scene, down to N (layoffs) |
| `working` | `false` = screens off |
| `mood` | `happy` (jumping, arms up) or `sad` |
| `suits` | `true` = executives/investors |
| `walker` | `[0.1, 0.8]` one person walks across (fractions of width) |
| `date` | big date card top-right: `"2012"`, `"SEP 2016"` |
| `board` | wall board, one of: `{"type":"number","text":"$1 BILLION","count":true,"sub":"-30% IN A YEAR","color":"#3a8a4a"}`, `{"type":"bars","title":"USERS","values":[1,4,9],"labels":["2019","2020","2021"]}`, `{"type":"line-up","title":"REVENUE"}`, `{"type":"line-down"}`, `{"type":"versus","left":"ZOOM","right":"FIREFLIES"}`, `{"type":"text","lines":["HEADLINE","second line"]}` |
| `event` | `fire`, `confetti`, `rain`, `money-up`, `money-down`, `dark` |
| `caption` | big on-screen line at the top, e.g. `"TRY IT FREE"` (max ~24 characters) |
| `zoom` | `true` = slow push-in |
| `short` | `true` = include in the 60-second 9:16 cut (pick scenes totalling 45-60 s, starting with a hook) |
| `dur` | force seconds |

Text drawn on the canvas uses a 5x7 pixel font: A-Z, 0-9, `. , ! ? - + $ % : ' / & € # ( ) " = × → ↑ ↓`. Lowercase is shown as uppercase.

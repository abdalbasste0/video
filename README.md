# Streamer Films: automated animated short-film channel

A fully automated pipeline for motivational animated short films (discipline, dopamine, consistency)
starring an original character, **the Streamer** (headphones + dark hoodie with neon touches).

```
story JSON (script + scenes)  ->  Kokoro TTS voice  ->  procedural animation (Skia)
        ->  music + SFX + subtitles  ->  video.mp4 (16:9) + short.mp4 (9:16) + thumbnail.png
        ->  YouTube upload (private + scheduled)
```

Everything is free and runs locally: no ElevenLabs, no paid image or video generators.

## Usage

```bash
./setup.sh                                                   # once
python -m studio.render stories/001-zero-viewers.json --preview   # quick stills to check the scenes
python -m studio.render stories/001-zero-viewers.json --vertical  # full video + Shorts
python -m studio.youtube auth                                # once (see the file for setup)
python -m studio.youtube upload output/001-zero-viewers --publish-at 2026-11-20T17:00:00Z
```

## Files
- `studio/character.py`: the character, 10 facial expressions and moves (walk, run, sit, sleep, kneel, push-ups, triumph...).
- `studio/scenes.py`: places (streaming room, bedroom, rainy street, gym, mountain at dawn, dark space, alarm clock).
- `studio/audio.py`: Kokoro voice, generated background music (no copyright issues), sound effects.
- `studio/render.py`: assembles everything into the final video.
- `stories/*.json`: each video's script and scenes.
- `schedule/calendar.md`: the publishing schedule.

## Writing a new video
Each shot in `shots` holds: `bg` (place), `actor` (`action`, `expr`, `x`, `move_to`, `prop`),
`say` (narration; its length sets the shot's duration), `caption` (big text), `cam` (zoom/focus), `sfx`, `fx`.

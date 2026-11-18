#!/usr/bin/env python3
"""Sofia voiceover for a pixel story, scene by scene, with Kokoro (the engine Voicebox uses).

  KOKORO_DIR=/path/to/kokoro_model  python voice.py STORY.json OUT_DIR [--voice af_bella] [--speed 1.1]

Needs: pip install kokoro-onnx soundfile, and in KOKORO_DIR: model.onnx (onnx-community/Kokoro-82M-v1.0-ONNX)
and voices.npz (that repo's voices/*.bin packed as arrays of shape (510,1,256)).

Writes to OUT_DIR:
  voiced_story.json   the story with every scene's "dur" set to its real audio length
  vo_full.wav         narration for the 16:9 video (each scene padded to its dur)
  vo_short.wav        narration for the 9:16 cut (scenes with "short": true)
Then: python3 tools/pixel_story/build.py OUT_DIR/voiced_story.json OUT_DIR --voiceover OUT_DIR/vo_full.wav --voiceover-vertical OUT_DIR/vo_short.wav
"""
import argparse, json, os
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

LEAD, TAIL = 0.25, 0.45  # silence before/after each scene's line (seconds)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("story"); ap.add_argument("out_dir")
    ap.add_argument("--voice", default="af_bella"); ap.add_argument("--speed", type=float, default=1.1)
    a = ap.parse_args()
    kdir = os.environ.get("KOKORO_DIR", "kokoro_model")
    k = Kokoro(os.path.join(kdir, "model.onnx"), os.path.join(kdir, "voices.npz"))
    story = json.load(open(a.story))
    os.makedirs(a.out_dir, exist_ok=True)
    sr, full, short = 24000, [], []
    for s in story["scenes"]:
        text = s.get("narration", "").strip()
        if text:
            audio, sr = k.create(text, voice=a.voice, speed=a.speed, lang="en-us")
        else:
            audio = np.zeros(0, dtype=np.float32)
        min_dur = s.get("dur") or (3.0 if not text else 0)
        dur = max(min_dur, LEAD + len(audio) / sr + TAIL)
        clip = np.zeros(int(round(dur * sr)), dtype=np.float32)
        start = int(LEAD * sr)
        clip[start:start + len(audio)] = audio[: len(clip) - start]
        s["dur"] = round(len(clip) / sr, 3)
        full.append(clip)
        if s.get("short"):
            short.append(clip)
    story["voice"] = {"engine": "kokoro (Voicebox engine)", "voice": a.voice, "speed": a.speed, "persona": "Sofia"}
    json.dump(story, open(os.path.join(a.out_dir, "voiced_story.json"), "w"), indent=1)
    sf.write(os.path.join(a.out_dir, "vo_full.wav"), np.concatenate(full), sr)
    if short:
        sf.write(os.path.join(a.out_dir, "vo_short.wav"), np.concatenate(short), sr)
    tot = sum(len(c) for c in full) / sr
    print(f"voice {a.voice}: full {tot:.1f}s, short {sum(len(c) for c in short) / sr:.1f}s")


if __name__ == "__main__":
    main()

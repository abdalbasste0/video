#!/usr/bin/env python3
"""Khaled's editing tool: turn raw footage into platform-ready cuts with ffmpeg.

  python3 tools/render_short.py INPUT OUT_DIR [--srt captions.srt] [--start 0] [--end 45]
                                [--voiceover vo.mp3] [--formats vertical,landscape]

Outputs:
  OUT_DIR/vertical_9x16.mp4    1080x1920, for YouTube Shorts, TikTok, Instagram Reels, Facebook Reels
  OUT_DIR/landscape_16x9.mp4   1920x1080, for long-form YouTube
  OUT_DIR/cover.jpg            frame at 1s, starting point for Tariq's cover

Audio is normalised to -14 LUFS (what YouTube, TikTok, Instagram and Facebook all target).
Captions are burned in with large, high-contrast text placed in the platform-safe zone.
"""
import argparse
import os
import subprocess
import sys

STYLE = ("FontName=DejaVu Sans,FontSize=13,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
         "BorderStyle=1,Outline=3,Shadow=0,Alignment=2,MarginV={mv}")


def esc(path):
    # ffmpeg filter-graph escaping for paths inside subtitles=
    return path.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def run(cmd):
    print("$", " ".join(cmd))
    subprocess.run(cmd, check=True)


def render(a, fmt):
    if fmt == "vertical":
        w, h, mv, name = 1080, 1920, 70, "vertical_9x16.mp4"
    else:
        w, h, mv, name = 1920, 1080, 40, "landscape_16x9.mp4"
    # fill the frame: scale up to cover, then centre-crop
    vf = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1,fps=30"
    if a.srt:
        vf += f",subtitles='{esc(os.path.abspath(a.srt))}':force_style='{STYLE.format(mv=mv)}'"
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    if a.start:
        cmd += ["-ss", str(a.start)]
    if a.end:
        cmd += ["-to", str(a.end)]
    cmd += ["-i", a.input]
    if a.voiceover:
        cmd += ["-i", a.voiceover, "-map", "0:v:0", "-map", "1:a:0", "-shortest"]
    cmd += ["-vf", vf, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", os.path.join(a.out_dir, name)]
    run(cmd)
    return os.path.join(a.out_dir, name)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("input")
    p.add_argument("out_dir")
    p.add_argument("--srt")
    p.add_argument("--start", type=float)
    p.add_argument("--end", type=float)
    p.add_argument("--voiceover")
    p.add_argument("--formats", default="vertical")
    a = p.parse_args()
    if not os.path.exists(a.input):
        sys.exit(f"Input not found: {a.input}")
    os.makedirs(a.out_dir, exist_ok=True)
    outs = [render(a, f.strip()) for f in a.formats.split(",") if f.strip()]
    first = outs[0]
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", "1", "-i", first,
         "-frames:v", "1", "-q:v", "2", os.path.join(a.out_dir, "cover.jpg")])
    for o in outs + [os.path.join(a.out_dir, "cover.jpg")]:
        print("OUT", o)


if __name__ == "__main__":
    main()

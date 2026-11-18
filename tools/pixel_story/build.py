#!/usr/bin/env python3
"""Build a pixel-art story video from a story JSON (see README.md in this folder).

  python3 tools/pixel_story/build.py STORY.json OUT_DIR [--voiceover vo.mp3] [--no-vertical] [--preview SECONDS]

Outputs in OUT_DIR:
  landscape_16x9.mp4   1920x1080, burned captions (YouTube, Facebook)
  vertical_9x16.mp4    1080x1920 cut of the scenes marked "short": true (Shorts, TikTok, Reels)
  captions_16x9.srt, captions_9x16.srt, vo-script.txt, timed_story.json, cover_16x9.jpg

Scene durations come from the narration (WPS words/second) unless "dur" is set.
With --voiceover, all scene durations are scaled so the video matches the audio length.
"""
import argparse, json, os, re, subprocess, sys, textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
WPS = 2.6
FONT_STYLE = ("FontName=Inter Display Black,FontSize={fs},Bold=0,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
              "BackColour=&H80000000,BorderStyle=1,Outline=2.4,Shadow=1.2,Spacing=0.3,Alignment=2,MarginV={mv}")


def run(cmd):
    subprocess.run(cmd, check=True)


def dur_of(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]).decode().strip())


def ts(t):
    h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)) % 1000:03d}"


def time_scenes(scenes, scale=1.0):
    out = []
    for s in scenes:
        s = dict(s)
        words = len(s.get("narration", "").split())
        s["dur"] = round(s.get("dur") or max(3.0, words / WPS + 0.7), 2)
        out.append(s)
    if scale != 1.0:
        for s in out:
            s["dur"] = round(s["dur"] * scale, 3)
    return out


def srt(scenes, width):
    """One subtitle block per chunk of narration, spread evenly over the scene."""
    blocks, t0 = [], 0.0
    for s in scenes:
        words = s.get("narration", "").split()
        if words:
            lines = textwrap.wrap(" ".join(words), width)
            chunks = [lines[i:i + 2] for i in range(0, len(lines), 2)]
            lead = 0.25
            span = (s["dur"] - lead - 0.3) / len(chunks)
            for i, c in enumerate(chunks):
                a = t0 + lead + i * span
                blocks.append((a, a + span - 0.05, "\n".join(c)))
        t0 += s["dur"]
    return "".join(f"{i}\n{ts(a)} --> {ts(b)}\n{t}\n\n" for i, (a, b, t) in enumerate(blocks, 1)), t0


def esc(p):
    return p.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def render(story, scenes, out_dir, name):
    timed = dict(story, scenes=scenes)
    tp = os.path.join(out_dir, f"timed_{name}.json")
    json.dump(timed, open(tp, "w"), indent=1)
    raw = os.path.join(out_dir, f".raw_{name}.mp4")
    run(["node", os.path.join(HERE, "render.js"), tp, raw, "24"])
    return raw


def mux(raw, out, srt_path, audio, total, vertical, title):
    if vertical:
        vf = ("scale=1440:810:flags=neighbor,crop=1080:810,pad=1080:1920:0:520:color=0x0b0c10,"
              f"subtitles='{esc(srt_path)}':force_style='{FONT_STYLE.format(fs=13, mv=70)}'")
        if title:
            vf += (",drawtext=fontfile=/usr/share/fonts/opentype/inter/InterDisplay-Black.otf:"
                   f"text='{title.replace(chr(39), '').replace(':', ' ')}':fontcolor=0xffc861:fontsize=64:x=(w-tw)/2:y=330:"
                   "borderw=4:bordercolor=black")
    else:
        vf = f"scale=1920:1080:flags=neighbor,subtitles='{esc(srt_path)}':force_style='{FONT_STYLE.format(fs=17, mv=24)}'"
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", raw]
    if audio:
        cmd += ["-i", audio, "-map", "0:v", "-map", "1:a", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11"]
    else:
        cmd += ["-f", "lavfi", "-t", str(total), "-i", "anullsrc=r=48000:cl=stereo", "-map", "0:v", "-map", "1:a"]
    cmd += ["-vf", vf, "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out]
    run(cmd)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("story"); ap.add_argument("out_dir")
    ap.add_argument("--voiceover"); ap.add_argument("--voiceover-vertical")
    ap.add_argument("--no-vertical", action="store_true")
    ap.add_argument("--preview", type=float, help="render only the first N seconds (quick check)")
    a = ap.parse_args()
    story = json.load(open(a.story))
    os.makedirs(a.out_dir, exist_ok=True)

    scenes = time_scenes(story["scenes"])
    natural = sum(s["dur"] for s in scenes)
    if a.voiceover:
        scenes = time_scenes(story["scenes"], dur_of(a.voiceover) / natural)
    if a.preview:
        keep, t = [], 0
        for s in scenes:
            if t >= a.preview: break
            keep.append(s); t += s["dur"]
        scenes = keep

    open(os.path.join(a.out_dir, "vo-script.txt"), "w").write(
        "\n\n".join(s["narration"] for s in story["scenes"] if s.get("narration")) + "\n")

    text, total = srt(scenes, 42)
    sp = os.path.join(a.out_dir, "captions_16x9.srt"); open(sp, "w").write(text)
    raw = render(story, scenes, a.out_dir, "16x9")
    out = os.path.join(a.out_dir, "landscape_16x9.mp4")
    mux(raw, out, sp, a.voiceover, total, False, None)
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", str(min(2.0, total / 2)), "-i", out, "-frames:v", "1", "-q:v", "2",
         os.path.join(a.out_dir, "cover_16x9.jpg")])
    os.remove(raw)
    print("OUT", out, f"{total:.1f}s")

    if not a.no_vertical and not a.preview:
        vs = [s for s in story["scenes"] if s.get("short")]
        if vs:
            vscenes = time_scenes(vs)
            if a.voiceover_vertical:
                vscenes = time_scenes(vs, dur_of(a.voiceover_vertical) / sum(s["dur"] for s in vscenes))
            vtext, vtotal = srt(vscenes, 30)
            vsp = os.path.join(a.out_dir, "captions_9x16.srt"); open(vsp, "w").write(vtext)
            open(os.path.join(a.out_dir, "vo-script-short.txt"), "w").write(
                "\n\n".join(s["narration"] for s in vs if s.get("narration")) + "\n")
            vraw = render(dict(story, vertical=True), vscenes, a.out_dir, "9x16")
            vout = os.path.join(a.out_dir, "vertical_9x16.mp4")
            mux(vraw, vout, vsp, a.voiceover_vertical, vtotal, True, story.get("short_title") or story.get("title"))
            os.remove(vraw)
            print("OUT", vout, f"{vtotal:.1f}s")


if __name__ == "__main__":
    main()

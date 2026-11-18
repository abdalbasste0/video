#!/usr/bin/env python3
"""Build a chibi-map video (16:9 + 9:16) from a story's chibi visuals + its Sofia voiceover.

  python3 tools/chibi/build.py CHIBI.json VOICE_DIR OUT_DIR [--preview SECONDS] [--no-vertical]

VOICE_DIR is where tools/pixel_story/voice_chatterbox.py wrote voiced_story.json, vo_full.wav, vo_short.wav.
Captions: word-by-word, timed with Whisper word timestamps on the real audio (WHISPER_DIR = faster-whisper model folder),
burned in with Inter Display Black. Outputs landscape_16x9.mp4, vertical_9x16.mp4, captions_*.ass, cover.jpg.
"""
import argparse, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def words(audio, whisper_dir):
    import numpy as np, soundfile as sf
    from faster_whisper import WhisperModel
    a, sr = sf.read(audio, dtype="float32")
    if a.ndim > 1:
        a = a.mean(axis=1)
    a = np.interp(np.arange(0, len(a), sr / 16000), np.arange(len(a)), a).astype(np.float32)
    m = WhisperModel(whisper_dir, device="cpu", compute_type="int8")
    segs, _ = m.transcribe(a, word_timestamps=True, vad_filter=False)
    out = []
    for s in segs:
        for w in s.words or []:
            out.append((w.start, w.end, w.word.strip()))
    return out


def align(ws, script):
    """Keep Whisper's timing but the script's spelling: map script words onto recognised words."""
    import difflib, re
    norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())
    sw = script.split()
    a, b = [norm(w) for w in sw], [norm(w[2]) for w in ws]
    times = [None] * len(sw)
    for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            times[blk.a + k] = ws[blk.b + k][:2]
    # fill gaps by interpolating between known neighbours
    known = [i for i, t in enumerate(times) if t]
    if not known:
        return ws
    for i in range(len(sw)):
        if times[i]:
            continue
        lo = max([k for k in known if k < i], default=None); hi = min([k for k in known if k > i], default=None)
        t0 = times[lo][1] if lo is not None else 0.0
        t1 = times[hi][0] if hi is not None else t0 + 0.4 * (i - (lo or 0) + 1)
        span = (hi if hi is not None else i + 1) - (lo if lo is not None else -1)
        pos = i - (lo if lo is not None else -1)
        st = t0 + (t1 - t0) * (pos - 1) / span; en = t0 + (t1 - t0) * pos / span
        times[i] = (st, max(en, st + 0.12))
    return [(t[0], t[1], w) for t, w in zip(times, sw)]


def ass(ws, W, H, path, vertical):
    size = 92 if vertical else 84
    y = int(H * (0.8 if vertical else 0.935))
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: W,Inter Display Black,{size},&H00FFFFFF,&H00FFFFFF,&H001A1612,&H64000000,0,0,0,0,100,100,1,0,1,9,3,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    def ts(t):
        h, r = divmod(max(0, t), 3600); m, s = divmod(r, 60)
        return f"{int(h)}:{int(m):02d}:{s:05.2f}"
    lines = []
    # group into chunks of up to 2 short words (one word if long), like history-explainer captions
    i = 0
    while i < len(ws):
        chunk = [ws[i]]
        if i + 1 < len(ws) and len(ws[i][2]) + len(ws[i + 1][2]) <= 11 and ws[i + 1][0] - ws[i][1] < 0.25:
            chunk.append(ws[i + 1])
        i += len(chunk)
        st, en = chunk[0][0], chunk[-1][1]
        nxt = ws[i][0] if i < len(ws) else en + 0.6
        en = min(max(en, st + 0.25), nxt)
        text = " ".join(c[2] for c in chunk).replace("{", "").replace("}", "")
        lines.append(f"Dialogue: 0,{ts(st)},{ts(en)},W,,0,0,0,,{{\\pos({W // 2},{y})\\fscx70\\fscy70\\t(0,90,\\fscx100\\fscy100)}}{text}")
    open(path, "w").write(head + "\n".join(lines) + "\n")


def render(chibi, voiced, audio, out, aspect, short, preview, whisper_dir):
    W, H = (1080, 1920) if aspect == "9x16" else (1920, 1080)
    raw = out + ".raw.mp4"
    cmd = ["node", os.path.join(HERE, "animate.js"), "--chibi", chibi, "--voiced", voiced, "--out", raw, "--aspect", aspect]
    if short: cmd.append("--short")
    if preview: cmd += ["--preview", str(preview)]
    subprocess.run(cmd, check=True)
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", raw]).decode())
    clip = out + ".audio.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", audio, "-t", str(dur), clip], check=True)
    ap = out + ".ass"
    v = json.load(open(voiced))
    scenes = [s for s in v["scenes"] if (s.get("short") or not short)]
    if preview:
        keep, t = [], 0
        for s in scenes:
            if t >= preview: break
            keep.append(s); t += s["dur"]
        scenes = keep
    script = " ".join(s.get("narration", "") for s in scenes)
    ass(align(words(clip, whisper_dir), script), W, H, ap, aspect == "9x16")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", raw, "-i", clip,
                    "-vf", f"ass={ap}", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)
    os.remove(raw); os.remove(clip)
    print("OUT", out, f"{dur:.1f}s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("chibi"); ap.add_argument("voice_dir"); ap.add_argument("out_dir")
    ap.add_argument("--preview", type=float); ap.add_argument("--no-vertical", action="store_true")
    a = ap.parse_args()
    wd = os.environ.get("WHISPER_DIR")
    if not wd:
        sys.exit("Set WHISPER_DIR to a faster-whisper model folder (e.g. Systran/faster-whisper-base.en)")
    os.makedirs(a.out_dir, exist_ok=True)
    v = os.path.join(a.voice_dir, "voiced_story.json")
    render(a.chibi, v, os.path.join(a.voice_dir, "vo_full.wav"), os.path.join(a.out_dir, "landscape_16x9.mp4"), "16x9", False, a.preview, wd)
    if not a.no_vertical and not a.preview:
        render(a.chibi, v, os.path.join(a.voice_dir, "vo_short.wav"), os.path.join(a.out_dir, "vertical_9x16.mp4"), "9x16", True, None, wd)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "3", "-i", os.path.join(a.out_dir, "landscape_16x9.mp4"),
                    "-frames:v", "1", "-q:v", "2", os.path.join(a.out_dir, "cover.jpg")], check=True)


if __name__ == "__main__":
    main()

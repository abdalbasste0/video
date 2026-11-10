"""
Captions (.srt, NOT burned into the video - YouTube shows them as CC).

Best:     faster-whisper word timestamps from the final audio.
Fallback: we know each line's text and where its audio starts/ends, so words are
          spread over the line's duration (good enough when whisper isn't installed).
Text is stored in normal (logical) order - players handle right-to-left themselves.
"""
from __future__ import annotations

from pathlib import Path

from .config import language


def _fmt(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _group(words, max_chars, max_lines, max_gap=0.6, max_dur=6.0):
    """words: [(start, end, word)] -> cues [(start, end, text)]"""
    cues, cur = [], []
    limit = max_chars * max_lines
    for w in words:
        text = " ".join(x[2] for x in cur + [w])
        too_long = len(text) > limit
        gap = cur and (w[0] - cur[-1][1] > max_gap)
        too_slow = cur and (w[1] - cur[0][0] > max_dur)
        if cur and (too_long or gap or too_slow):
            cues.append(cur)
            cur = []
        cur.append(w)
        if w[2].rstrip().endswith((".", "!", "?", "؟", "…")) and len(" ".join(x[2] for x in cur)) > max_chars * 0.6:
            cues.append(cur)
            cur = []
    if cur:
        cues.append(cur)
    out = []
    for c in cues:
        text = " ".join(x[2] for x in c)
        if len(text) > max_chars and max_lines > 1:  # break into 2 balanced lines
            words_ = text.split()
            best = min(range(1, len(words_)), key=lambda i: abs(len(" ".join(words_[:i])) - len(" ".join(words_[i:]))))
            text = " ".join(words_[:best]) + "\n" + " ".join(words_[best:])
        out.append((c[0][0], c[-1][1], text))
    return out


def words_from_lines(lines: list) -> list:
    """lines: [{'text','start','end'}] -> evenly spread word timings (by character length)."""
    words = []
    for ln in lines:
        ws = ln["text"].split()
        total = sum(len(w) + 1 for w in ws) or 1
        t = ln["start"]
        span = ln["end"] - ln["start"]
        for w in ws:
            d = span * (len(w) + 1) / total
            words.append((t, t + d, w))
            t += d
    return words


def words_from_whisper(audio_path: Path, lang_code: str) -> list | None:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return None
    model = WhisperModel("small", device="auto", compute_type="int8")
    segs, _ = model.transcribe(str(audio_path), language=lang_code, word_timestamps=True, vad_filter=True)
    return [(w.start, w.end, w.word.strip()) for s in segs for w in (s.words or []) if w.word.strip()]


def write_srt(lang_code: str, out: Path, lines: list = None, audio_path: Path = None, log=print) -> Path:
    style = language(lang_code).get("caption_style", {})
    words = words_from_whisper(audio_path, lang_code) if audio_path else None
    if words:
        log("  captions: faster-whisper word timestamps")
    else:
        log("  captions: timed from script lines (install faster-whisper for word-accurate timing)")
        words = words_from_lines(lines or [])
    cues = _group(words, style.get("max_chars_per_line", 42), style.get("max_lines", 2))
    body = "".join(f"{i}\n{_fmt(s)} --> {_fmt(e)}\n{t}\n\n" for i, (s, e, t) in enumerate(cues, 1))
    Path(out).write_text(body, encoding="utf-8")
    return Path(out)

"""Voice (Kokoro TTS), procedural royalty-free music and sound effects."""
import os
import numpy as np

SR = 24000  # Kokoro native rate; everything is mixed at this rate
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_kokoro = None


def kokoro():
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        _kokoro = Kokoro(os.path.join(ROOT, "models/kokoro-v1.0.onnx"),
                         os.path.join(ROOT, "models/voices-v1.0.bin"))
    return _kokoro


def voice_style(spec):
    """'am_michael' or a blend 'am_michael:0.6,am_fenrir:0.4'."""
    k = kokoro()
    if ":" not in spec:
        return spec
    parts = [p.split(":") for p in spec.split(",")]
    return sum(k.get_voice_style(n) * float(w) for n, w in parts)


def tts(text, voice="am_michael", speed=0.92, lang="en-us"):
    samples, sr = kokoro().create(text, voice=voice_style(voice), speed=speed, lang=lang)
    assert sr == SR
    # trim leading/trailing near-silence so timing is tight
    a = np.abs(samples)
    idx = np.where(a > 0.01)[0]
    if len(idx):
        samples = samples[max(0, idx[0] - 600): idx[-1] + 2400]
    return samples.astype(np.float32)


# ---------------------------------------------------------------- music
def _note(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def _reverb(x, sr=SR, mix=0.35):
    out = np.copy(x)
    for d, g in ((0.0297, 0.77), (0.0371, 0.74), (0.0411, 0.72), (0.0437, 0.70)):
        n = int(d * sr * 3)
        y = np.copy(x)
        for k in range(1, 7):
            if n * k >= len(x):
                break
            y[n * k:] += x[:-n * k] * (g ** k)
        out += y * mix / 4
    return out


def music(duration, mood="emotional", seed=1, bpm=72):
    """Ambient pad + soft piano arpeggio. mood: emotional | dark | hopeful."""
    rng = np.random.default_rng(seed)
    n = int(duration * SR) + SR
    t = np.arange(n) / SR
    progs = {
        "emotional": [(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)],  # Am F C G
        "dark":      [(57, 60, 64), (53, 57, 60), (52, 55, 59), (52, 56, 59)],  # Am F Em E
        "hopeful":   [(48, 52, 55), (55, 59, 62), (57, 60, 64), (53, 57, 60)],  # C G Am F
    }
    prog = progs.get(mood, progs["emotional"])
    bar = 4 * 60 / bpm
    pad = np.zeros(n, np.float32)
    keys = np.zeros(n, np.float32)
    nb = int(duration / bar) + 2
    for b in range(nb):
        chord = prog[b % len(prog)]
        s0 = int(b * bar * SR)
        s1 = min(n, int((b + 1) * bar * SR) + SR)
        tt = t[s0:s1] - b * bar
        env = np.minimum(1, tt / 1.2) * np.exp(-np.maximum(0, tt - bar) * 3)
        for m in chord + (chord[0] - 12,):
            f = _note(m)
            v = sum(np.sin(2 * np.pi * f * d * tt) for d in (0.997, 1.0, 1.004)) / 3
            pad[s0:s1] += (v * env * 0.08).astype(np.float32)
        # arpeggio, 8th notes, gentle piano-ish tone
        step = 60 / bpm / 2
        for i in range(8):
            if rng.random() < 0.25:
                continue
            m = chord[[0, 1, 2, 1, 2, 0, 1, 2][i]] + 12
            a0 = s0 + int(i * step * SR)
            L = int(2.5 * SR)
            a1 = min(n, a0 + L)
            ta = np.arange(a1 - a0) / SR
            f = _note(m)
            tone = (np.sin(2 * np.pi * f * ta) + 0.35 * np.sin(4 * np.pi * f * ta)
                    + 0.12 * np.sin(6 * np.pi * f * ta))
            keys[a0:a1] += (tone * np.exp(-ta * 2.2) * np.minimum(1, ta * 200) * 0.07).astype(np.float32)
    # sub swell
    x = pad + _reverb(keys, mix=0.6)
    x = x[: int(duration * SR)]
    fade = int(2 * SR)
    x[:fade] *= np.linspace(0, 1, fade)
    x[-fade:] *= np.linspace(1, 0, fade)
    return x / (np.max(np.abs(x)) + 1e-6) * 0.9


# ---------------------------------------------------------------- sfx
def sfx(name, dur=None):
    rng = np.random.default_rng(abs(hash(name)) % 2**32)
    if name == "alarm":
        d = dur or 2.0
        t = np.arange(int(d * SR)) / SR
        gate = ((t * 8) % 1 < 0.5) & ((t * 1.25) % 1 < 0.6)
        return (np.sign(np.sin(2 * np.pi * 1800 * t)) * gate * 0.18).astype(np.float32)
    if name == "rain":
        d = dur or 4.0
        x = rng.standard_normal(int(d * SR)).astype(np.float32)
        y = np.convolve(x, np.ones(6) / 6, mode="same")
        return y * 0.08
    if name == "typing":
        d = dur or 3.0
        out = np.zeros(int(d * SR), np.float32)
        tpos = 0.0
        while tpos < d - 0.05:
            i = int(tpos * SR)
            L = int(0.025 * SR)
            out[i:i + L] += rng.standard_normal(L).astype(np.float32) * np.exp(-np.arange(L) / 120) * 0.12
            tpos += rng.uniform(0.06, 0.18)
        return out
    if name == "heartbeat":
        d = dur or 3.0
        out = np.zeros(int(d * SR), np.float32)
        for beat in np.arange(0.1, d - 0.4, 0.9):
            for off, a in ((0, 1.0), (0.22, 0.7)):
                i = int((beat + off) * SR)
                ta = np.arange(int(0.18 * SR)) / SR
                out[i:i + len(ta)] += (np.sin(2 * np.pi * 55 * ta) * np.exp(-ta * 25) * 0.5 * a)[: len(out) - i]
        return out
    if name == "whoosh":
        d = dur or 0.8
        x = rng.standard_normal(int(d * SR)).astype(np.float32)
        x = np.convolve(x, np.ones(20) / 20, mode="same")
        env = np.sin(np.linspace(0, np.pi, len(x))) ** 2
        return x * env * 0.5
    if name == "boom":
        d = dur or 2.0
        ta = np.arange(int(d * SR)) / SR
        return (np.sin(2 * np.pi * 45 * ta * (1 - ta * 0.1)) * np.exp(-ta * 2.5) * 0.6).astype(np.float32)
    if name == "ding":
        d = dur or 1.5
        ta = np.arange(int(d * SR)) / SR
        return ((np.sin(2 * np.pi * 1320 * ta) + 0.5 * np.sin(2 * np.pi * 1980 * ta)) * np.exp(-ta * 4) * 0.15).astype(np.float32)
    raise KeyError(name)


def envelope(x, win=2400):
    a = np.abs(x)
    k = np.ones(win) / win
    return np.convolve(a, k, mode="same")

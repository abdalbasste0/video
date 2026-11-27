"""Build the final soundtrack: narration beats synced to 5s scenes + procedural
ocean ambience, low tension drone, and per-scene sound effects."""
import json, subprocess, re, sys
import numpy as np
from scipy.signal import butter, sosfilt
from scipy.io import wavfile

SR = 48000
ROOT = "/home/user/video"
SCENE = 5.0
N = 25
TOTAL = N * SCENE + 1.0
LEAD = 0.25  # narration starts this long after each scene cut
rng = np.random.default_rng(7)

def load_narration():
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f"{ROOT}/assets/narration.mp3",
                          "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()

def detect_beats():
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", f"{ROOT}/assets/narration.mp3",
                          "-af", "silencedetect=noise=-42dB:d=0.75", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", out)]
    ends = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", out)]
    assert len(starts) == N - 1 == len(ends), (len(starts), len(ends))
    segs, prev = [], 0.0
    for s, e in zip(starts, ends):
        segs.append((max(0.0, prev - 0.06), s + 0.12))
        prev = e
    segs.append((prev - 0.06, None))
    return segs

def lp(x, f, order=2):
    return sosfilt(butter(order, f, "low", fs=SR, output="sos"), x)

def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "band", fs=SR, output="sos"), x)

def hp(x, f, order=2):
    return sosfilt(butter(order, f, "high", fs=SR, output="sos"), x)

def env_ar(n, a, r):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    e[:na] = np.linspace(0, 1, na) if na else 1
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e

def add(buf, sig, t0, gain=1.0):
    i = int(t0 * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i] * gain

T = int(TOTAL * SR)
tt = np.arange(T) / SR

# ---------- ocean ambience (continuous) ----------
def ocean():
    noise = rng.standard_normal(T)
    brown = np.cumsum(noise); brown -= lp(brown, 0.5, 1); brown /= np.abs(brown).max()
    surf = lp(noise, 900) * 0.6 + lp(brown, 400) * 0.8
    swell = 0.55 + 0.45 * np.sin(2 * np.pi * tt / 7.3) * np.sin(2 * np.pi * tt / 11.1 + 1)
    swell = np.clip(swell, 0.15, 1.0) ** 1.6
    wash = hp(bp(noise, 1500, 6000) * (np.clip(np.sin(2 * np.pi * tt / 7.3 - 0.6), 0, 1) ** 4), 1200)
    return surf * swell * 0.18 + wash * 0.05

def wind():
    noise = rng.standard_normal(T)
    mod = 0.5 + 0.5 * np.sin(2 * np.pi * tt / 9.0 + np.sin(2 * np.pi * tt / 3.7))
    return bp(noise, 300, 1100) * mod * 0.05

# ---------- low tension music bed ----------
def drone():
    out = np.zeros(T)
    for f, a in [(55.0, 0.11), (82.4, 0.06), (65.4, 0.05), (110.0, 0.035), (164.8, 0.015)]:
        detune = 1 + 0.0025 * np.sin(2 * np.pi * tt / 13 + f)
        ph = np.cumsum(2 * np.pi * f * detune / SR)
        out += a * (np.sin(ph) + 0.25 * np.sin(2 * ph))
    shimmer = lp(rng.standard_normal(T), 200) * 0.0
    swell = 0.6 + 0.4 * np.sin(2 * np.pi * tt / 20 - np.pi / 2)
    fade = np.clip(tt / 4, 0, 1) * np.clip((TOTAL - tt) / 4, 0, 1)
    return (out + shimmer) * swell * fade

def pulse_hit(dur=2.5):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 48 * np.exp(-t * 0.6)
    s = np.sin(np.cumsum(2 * np.pi * f / SR)) * np.exp(-t * 1.6)
    s += lp(rng.standard_normal(n), 120) * np.exp(-t * 3) * 0.6
    return s * 0.45

def heartbeat(beats=4, bpm=62):
    period = 60 / bpm; n = int(beats * period * SR); out = np.zeros(n)
    for k in range(beats):
        for off, g in [(0, 1.0), (0.22, 0.7)]:
            m = int(0.18 * SR); t = np.arange(m) / SR
            thump = np.sin(2 * np.pi * 52 * t) * np.exp(-t * 26) * g
            add(out, thump, k * period + off)
    return out * 0.5

# ---------- sound effects ----------
def creak(dur=1.2):
    n = int(dur * SR); t = np.arange(n) / SR
    f0 = 180 + 90 * np.sin(np.pi * t / dur) + 30 * rng.standard_normal() 
    ph = np.cumsum(2 * np.pi * f0 / SR)
    saw = 2 * ((ph / (2 * np.pi)) % 1) - 1
    grit = (rng.random(n) < 0.02 + 0.03 * np.sin(np.pi * t / dur)).astype(float)
    s = bp(saw * 0.5 + grit, 250, 2400) * np.sin(np.pi * t / dur) ** 0.7
    return s * 0.12

def engine(dur=5.0):
    n = int(dur * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * 38 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 9.5 * t)) 
    s += 0.4 * lp(rng.standard_normal(n), 160)
    return s * env_ar(n, 1.0, 1.5) * 0.12

def gull():
    n = int(0.55 * SR); t = np.arange(n) / SR
    f = 1500 + 900 * np.sin(np.pi * t / 0.55) - 600 * t
    s = np.sin(np.cumsum(2 * np.pi * f / SR)) * np.sin(np.pi * t / 0.55) ** 2
    return bp(s + 0.2 * rng.standard_normal(n) * np.sin(np.pi * t / .55), 700, 4000) * 0.035

def tick():
    n = int(0.03 * SR); t = np.arange(n) / SR
    return hp(rng.standard_normal(n), 2500) * np.exp(-t * 300) * 0.25

def wave_crash(dur=4.0):
    n = int(dur * SR); t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    e = np.clip(t / 1.4, 0, 1) ** 2 * np.exp(-np.clip(t - 1.4, 0, None) * 1.4)
    rumble = lp(noise, 250) * e * 1.6
    hiss = bp(noise, 800, 7000) * e
    return (rumble + hiss) * 0.35

def hiss_sparks(dur=4.5):
    n = int(dur * SR); out = hp(rng.standard_normal(n), 3000) * 0.025
    for _ in range(14):
        m = int(0.04 * SR); t = np.arange(m) / SR
        add(out, hp(rng.standard_normal(m), 2000) * np.exp(-t * 120) * 0.25, rng.uniform(0.2, dur - 0.2))
    steam = bp(rng.standard_normal(n), 2000, 8000) * env_ar(n, 0.3, 1.0) * 0.06
    return out + steam

def ping():
    n = int(2.0 * SR); t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * 1180 * t) + 0.3 * np.sin(2 * np.pi * 2360 * t)) * np.exp(-t * 3.2)
    return s * 0.06

def buzz(dur=5.0):
    n = int(dur * SR); t = np.arange(n) / SR
    s = np.sign(np.sin(2 * np.pi * 100 * t)) * 0.3 + np.sin(2 * np.pi * 50 * t)
    flick = (np.sin(2 * np.pi * 0.9 * t) > 0.85).astype(float) * 0.7 + 0.3
    return bp(s, 80, 900) * flick * 0.012

def whoosh(dur=1.6):
    n = int(dur * SR); t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    e = np.sin(np.pi * t / dur) ** 2
    return bp(noise, 400, 2500) * e * 0.10

def paper(dur=2.0):
    n = int(dur * SR); out = np.zeros(n)
    for _ in range(18):
        m = int(rng.uniform(0.03, 0.09) * SR); t = np.arange(m) / SR
        add(out, bp(rng.standard_normal(m), 1500, 7000) * np.sin(np.pi * t / t[-1]) * 0.08, rng.uniform(0, dur - 0.1))
    return out

def drip():
    n = int(0.25 * SR); t = np.arange(n) / SR
    f = 900 + 1400 * np.exp(-t * 30)
    return np.sin(np.cumsum(2 * np.pi * f / SR)) * np.exp(-t * 22) * 0.06

def build():
    narr = load_narration()
    segs = detect_beats()
    voice = np.zeros(T)
    timings = []
    for i, (a, b) in enumerate(segs):
        ia = int(a * SR); ib = len(narr) if b is None else int(b * SR)
        seg = narr[ia:ib].astype(np.float64)
        fade = int(0.04 * SR)
        seg[:fade] *= np.linspace(0, 1, fade); seg[-fade:] *= np.linspace(1, 0, fade)
        t0 = i * SCENE + LEAD
        add(voice, seg, t0)
        # trim silence for subtitle timing
        absx = np.abs(seg); thr = 10 ** (-38 / 20)
        idx = np.where(absx > thr)[0]
        s0 = t0 + idx[0] / SR; s1 = t0 + idx[-1] / SR
        timings.append((round(s0, 3), round(s1, 3)))

    amb = ocean() + wind()
    music = drone()
    sfx = np.zeros(T)
    S = lambda k, off=0.0: k * SCENE + off
    # scene-specific effects
    add(sfx, engine(5.3), S(0)); add(sfx, gull(), S(0, 0.8)); add(sfx, gull(), S(0, 2.6), 0.7)
    add(sfx, creak(), S(0, 3.4))
    add(sfx, pulse_hit(), S(1, 0.1))
    add(sfx, drip(), S(2, 1.5)); add(sfx, drip(), S(2, 3.3), 0.6)
    add(sfx, whoosh(2.0), S(3, 1.0)); add(sfx, creak(1.5), S(3, 3.0))
    add(sfx, whoosh(1.4), S(4, 1.6))
    add(sfx, ping(), S(5, 0.6)); add(sfx, ping(), S(5, 1.9), 0.7); add(sfx, ping(), S(5, 3.1), 0.5)
    add(sfx, creak(1.6), S(6, 0.5)); add(sfx, creak(1.2), S(6, 2.8))
    add(sfx, pulse_hit(), S(7, 1.0), 0.6)
    add(sfx, engine(5.3), S(8), 0.8); add(sfx, ping(), S(8, 2.0), 0.5)
    add(sfx, whoosh(2.5), S(9, 1.5))
    add(sfx, heartbeat(5), S(10, 0.3))
    add(sfx, creak(), S(13, 1.0)); add(sfx, creak(1.4), S(14, 2.5))
    for k in range(10):
        add(sfx, tick(), S(15, 0.2 + k * 0.5))
    add(sfx, paper(2.0), S(16, 2.4)); add(sfx, buzz(5.0), S(16))
    add(sfx, wave_crash(4.6), S(17, 0.3)); add(sfx, pulse_hit(), S(17, 1.8))
    add(sfx, hiss_sparks(4.8), S(18))
    add(sfx, paper(2.5), S(19, 1.0)); add(sfx, buzz(5.0), S(19), 0.8)
    add(sfx, heartbeat(5), S(20, 0.2), 0.8)
    add(sfx, pulse_hit(), S(21, 0.3), 0.5)
    for k in range(4):
        add(sfx, ping(), S(22, 0.3 + k * 1.15), 0.8)
    add(sfx, whoosh(2.5), S(23, 1.0), 0.8)
    add(sfx, pulse_hit(3.0), S(24, 3.0), 0.8)

    # duck ambience + music under voice
    venv = lp(np.abs(voice), 4)
    venv = np.clip(venv / (venv.max() + 1e-9) * 4, 0, 1)
    duck = 1 - 0.45 * venv
    mix = voice * 1.0 + (amb * 0.9 + music * 0.75) * duck + sfx * 0.9
    fade = np.clip(tt / 1.0, 0, 1) * np.clip((TOTAL - tt) / 1.5, 0, 1)
    mix *= fade
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    mix /= np.abs(mix).max() / 0.92
    stereo = np.stack([mix, mix], 1)
    # slight stereo width on ambience
    wide = (amb * 0.9 * duck * fade)
    d = int(0.012 * SR)
    stereo[d:, 1] += wide[:-d] * 0.15; stereo[:, 0] -= wide * 0.05
    wavfile.write(f"{ROOT}/build/soundtrack.wav", SR, (np.clip(stereo, -1, 1) * 32767).astype(np.int16))
    json.dump(timings, open(f"{ROOT}/build/timings.json", "w"))
    print("ok", timings)

if __name__ == "__main__":
    build()

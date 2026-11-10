"""
Audio: reading/writing wavs, cleaning voice lines, lip-flap envelopes,
license checks, mixing with music ducking, and loudness normalization.

All internal audio is 48 kHz float32 numpy arrays.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import wave
from pathlib import Path

import numpy as np

from .config import ASSETS, StudioError, settings

SR = 48000


def _ffmpeg():
    exe = shutil.which("ffmpeg")
    if not exe:
        raise StudioError("FFmpeg is not installed or not on PATH (see README).")
    return exe


# ── wav io ────────────────────────────────────────────────────
def write_wav(path, data: np.ndarray, sr: int = SR):
    """data: float32 mono (N,) or stereo (N, 2), range -1..1."""
    data = np.clip(np.asarray(data, np.float32), -1, 1)
    ch = 1 if data.ndim == 1 else data.shape[1]
    with wave.open(str(path), "wb") as w:
        w.setnchannels(ch)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((data * 32767).astype("<i2").tobytes())


def read_wav(path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as w:
        sr, ch, n, sw = w.getframerate(), w.getnchannels(), w.getnframes(), w.getsampwidth()
        raw = w.readframes(n)
    if sw != 2:
        raise StudioError(f"{path}: only 16-bit wav supported (convert with ffmpeg).")
    a = np.frombuffer(raw, "<i2").astype(np.float32) / 32768
    if ch > 1:
        a = a.reshape(-1, ch)
    return a, sr


def load_any(path, stereo=False) -> np.ndarray:
    """Load any audio file (mp3/ogg/wav...) as 48 kHz float32 via ffmpeg."""
    ch = 2 if stereo else 1
    r = subprocess.run([_ffmpeg(), "-v", "error", "-i", str(path), "-f", "s16le", "-ac", str(ch), "-ar", str(SR), "-"],
                       capture_output=True)
    if r.returncode != 0:
        raise StudioError(f"Could not read audio file {path}: {r.stderr.decode()[-200:]}")
    a = np.frombuffer(r.stdout, "<i2").astype(np.float32) / 32768
    return a.reshape(-1, 2) if stereo else a


def standardize(src: Path, dst: Path):
    """Any TTS output -> 48 kHz mono 16-bit wav, silence trimmed at both ends, small pad."""
    af = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,"
          "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.08,areverse,"
          "adelay=60|60,apad=pad_dur=0.08")
    r = subprocess.run([_ffmpeg(), "-y", "-v", "error", "-i", str(src), "-af", af, "-ac", "1", "-ar", str(SR),
                        "-sample_fmt", "s16", str(dst)], capture_output=True, text=True)
    if r.returncode != 0:
        raise StudioError(f"Could not convert voice audio: {r.stderr[-200:]}")


def duration(path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / w.getframerate()


# ── lip flap ──────────────────────────────────────────────────
def envelope(path, fps: int) -> list[float]:
    """Mouth openness per video frame (0..1) from the voice loudness."""
    a, sr = read_wav(path)
    if a.ndim > 1:
        a = a.mean(axis=1)
    hop = sr // fps
    n = len(a) // hop
    if n == 0:
        return []
    rms = np.sqrt((a[: n * hop].reshape(n, hop) ** 2).mean(axis=1))
    ref = np.percentile(rms, 95) or 1e-6
    v = np.clip(rms / ref, 0, 1)
    v[v < 0.12] = 0            # gate: mouth closed in pauses
    # light smoothing so the mouth doesn't jitter
    v = np.convolve(v, [0.25, 0.5, 0.25], mode="same")
    return [round(float(x), 2) for x in v]


# ── licenses ──────────────────────────────────────────────────
def license_file(path: Path) -> Path:
    return Path(str(path) + ".license.txt")


def require_license(path: Path):
    path = Path(path)
    lic = license_file(path)
    if not lic.exists() or not lic.read_text(encoding="utf-8").strip():
        raise StudioError(
            f"Refusing to use {path.relative_to(ASSETS.parent) if path.is_absolute() else path}: "
            f"no license file found.\nCreate '{lic.name}' next to it saying where it came from and its license "
            f"(e.g. 'CC0 - freesound.org/s/12345 - author X')."
        )


def unlicensed_assets() -> list[Path]:
    bad = []
    for folder in ("music", "sfx"):
        for f in (ASSETS / folder).glob("*"):
            if f.suffix.lower() in (".wav", ".mp3", ".ogg", ".flac", ".m4a") and not license_file(f).exists():
                bad.append(f)
    return bad


# ── mixing ────────────────────────────────────────────────────
def db(x):
    return 10 ** (x / 20)


def _place(buf, clip, start_s, gain=1.0):
    i = int(start_s * SR)
    if i >= len(buf):
        return
    clip = clip[: len(buf) - i]
    if buf.ndim == 2 and clip.ndim == 1:
        clip = np.repeat(clip[:, None], 2, axis=1)
    buf[i: i + len(clip)] += clip * gain


def voice_activity(voice: np.ndarray, ramp_s=0.15) -> np.ndarray:
    """0..1 curve, 1 while someone talks, smooth ramps (for ducking)."""
    mono = np.abs(voice if voice.ndim == 1 else voice.mean(axis=1))
    hop = SR // 100
    n = len(mono) // hop + 1
    pad = np.zeros(n * hop, np.float32)
    pad[: len(mono)] = mono
    act = (pad.reshape(n, hop).max(axis=1) > 0.02).astype(np.float32)
    k = max(1, int(ramp_s * 100))
    hold = np.convolve(act, np.ones(k * 2), mode="same") > 0      # hold through tiny gaps
    smooth = np.convolve(hold.astype(np.float32), np.ones(k) / k, mode="same")
    return np.repeat(smooth, hop)[: len(mono)]


def mix(total_s: float, voices: list, music: list, sfx: list) -> np.ndarray:
    """
    voices: [(wav_path, start_s)]
    music:  [(file, start_s, end_s)]      looped / cut to fit, ducked under voice
    sfx:    [(file, start_s, gain_db)]
    Returns stereo float32 array.
    """
    a = settings()["audio"]
    N = int(total_s * SR) + 1
    vbus = np.zeros(N, np.float32)
    for path, start in voices:
        clip, sr = read_wav(path)
        if sr != SR:
            clip = load_any(path)
        _place(vbus, clip if clip.ndim == 1 else clip.mean(axis=1), start)
    mbus = np.zeros((N, 2), np.float32)
    for f, start, end in music:
        require_license(Path(f))
        m = load_any(f, stereo=True)
        need = int((end - start) * SR)
        if len(m) < need:
            m = np.tile(m, (need // len(m) + 1, 1))
        m = m[:need].copy()
        fade = min(int(1.0 * SR), need // 4)
        if fade:
            m[:fade] *= np.linspace(0, 1, fade)[:, None]
            m[-fade:] *= np.linspace(1, 0, fade)[:, None]
        _place(mbus, m, start)
    duck = db(a["music_volume_db"]) * db(a["duck_db"] * voice_activity(vbus))
    mbus *= duck[:, None]
    sbus = np.zeros((N, 2), np.float32)
    for f, start, gain in sfx:
        require_license(Path(f))
        _place(sbus, load_any(f, stereo=True), start, db(a["sfx_volume_db"] + gain))
    out = mbus + sbus + np.repeat(vbus[:, None], 2, axis=1)
    peak = np.abs(out).max() or 1
    if peak > 0.98:
        out *= 0.98 / peak
    return out


def loudnorm(src: Path, dst: Path, target=None) -> dict:
    """Two-pass EBU R128 normalization to target LUFS (default -14), true peak -1 dB."""
    target = target if target is not None else settings()["audio"]["target_lufs"]
    flt = f"loudnorm=I={target}:TP=-1.0:LRA=11"
    r = subprocess.run([_ffmpeg(), "-hide_banner", "-i", str(src), "-af", flt + ":print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S)
    if not m:
        raise StudioError("Loudness measurement failed (ffmpeg loudnorm).")
    meas = json.loads(m.group(0))
    flt2 = (f"{flt}:measured_I={meas['input_i']}:measured_TP={meas['input_tp']}:measured_LRA={meas['input_lra']}:"
            f"measured_thresh={meas['input_thresh']}:offset={meas['target_offset']}:linear=true")
    r = subprocess.run([_ffmpeg(), "-y", "-v", "error", "-i", str(src), "-af", flt2, "-ar", str(SR), str(dst)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise StudioError("Loudness normalization failed: " + r.stderr[-200:])
    return meas


def measure_lufs(path) -> float:
    r = subprocess.run([_ffmpeg(), "-hide_banner", "-i", str(path), "-af", "loudnorm=print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S)
    return float(json.loads(m.group(0))["input_i"]) if m else float("nan")


# ── code-generated sounds (CC0, used by the demo) ────────────
def ensure_demo_sounds() -> dict:
    """Create a few sounds by code (no downloads) WITH license files, so the license gate passes."""
    rng = np.random.default_rng(7)
    out = {}
    lic = "CC0 1.0 - generated procedurally by Stickman Mystery Studio (studio/audio.py ensure_demo_sounds). No third-party material."

    def save(rel, data):
        p = ASSETS / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            write_wav(p, data)
            license_file(p).write_text(lic + "\n", encoding="utf-8")
        out[p.stem] = p

    t = np.arange(int(SR * 12)) / SR
    drone = sum(np.sin(2 * np.pi * f * t + p) * g for f, p, g in [(55, 0, 0.5), (82.4, 1, 0.3), (110.3, 2, 0.15), (164.8, 0.5, 0.06)])
    drone *= 0.6 + 0.4 * np.sin(2 * np.pi * t / 6)  # slow swell
    noise = np.convolve(rng.standard_normal(len(t)), np.ones(400) / 400, mode="same") * 0.6
    loop = (drone * 0.35 + noise * 0.2).astype(np.float32)
    x = int(SR * 0.5)  # crossfade end into start for a seamless loop
    loop[:x] = loop[:x] * np.linspace(0, 1, x) + loop[-x:] * np.linspace(1, 0, x)
    save("music/demo_tension_drone.wav", np.stack([loop[:-x], np.roll(loop[:-x], 300)], axis=1) * 0.8)

    ts = np.arange(int(SR * 0.12)) / SR
    step = rng.standard_normal(len(ts)) * np.exp(-ts * 60)
    step = np.convolve(step, np.ones(30) / 30, mode="same") * 4
    save("sfx/demo_footstep.wav", step.astype(np.float32) * 0.6)

    ta = np.arange(int(SR * 2.0)) / SR
    siren = np.sign(np.sin(2 * np.pi * (700 + 250 * np.sign(np.sin(2 * np.pi * 2 * ta))) * ta)) * 0.25
    siren *= np.minimum(1, ta * 20) * np.minimum(1, (2.0 - ta) * 4)
    save("sfx/demo_alarm.wav", siren.astype(np.float32))

    th = np.arange(int(SR * 1.2)) / SR
    hit = (np.sin(2 * np.pi * 48 * th * (1 - th * 0.3)) * np.exp(-th * 4) +
           np.convolve(rng.standard_normal(len(th)), np.ones(60) / 60, mode="same") * np.exp(-th * 9) * 2)
    save("sfx/demo_impact.wav", (hit * 0.8).astype(np.float32))
    return out

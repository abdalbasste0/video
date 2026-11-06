// مهندس الصوت: موسيقى تصويرية ومؤثرات تُولَّد برمجيًا + خفض تلقائي للموسيقى تحت صوت الراوي
import { rng } from './procedural-art.js';
import { stripTags } from './ai.js';

const SR = 44100;
let sharedCtx;
const ctx = () => (sharedCtx ||= new (window.AudioContext || window.webkitAudioContext)());

export async function decodeBlob(blob) {
  const buf = await blob.arrayBuffer();
  return ctx().decodeAudioData(buf);
}

export function estimateDuration(text) {
  const words = stripTags(text).split(/\s+/).filter(Boolean).length;
  return Math.max(2.8, words / 2.4 + 0.8);
}

export const SFX = ['none', 'wind', 'crickets', 'whisper', 'heartbeat', 'footsteps', 'stinger', 'rain', 'clock', 'thunder'];

function noiseBuffer(ac, seconds, seed = 7) {
  const r = rng(seed);
  const b = ac.createBuffer(1, Math.max(1, Math.floor(SR * seconds)), SR);
  const d = b.getChannelData(0);
  for (let i = 0; i < d.length; i++) d[i] = r() * 2 - 1;
  return b;
}

function noise(ac, dest, t0, dur, { type = 'lowpass', freq = 800, q = 1, gain = 0.3, attack = 0.3, release = 0.5, seed = 3 } = {}) {
  const src = ac.createBufferSource();
  src.buffer = noiseBuffer(ac, dur + 0.1, seed);
  const f = ac.createBiquadFilter(); f.type = type; f.frequency.value = freq; f.Q.value = q;
  const g = ac.createGain();
  g.gain.setValueAtTime(0, t0);
  g.gain.linearRampToValueAtTime(gain, t0 + Math.min(attack, dur / 2));
  g.gain.setValueAtTime(gain, Math.max(t0 + attack, t0 + dur - release));
  g.gain.linearRampToValueAtTime(0, t0 + dur);
  src.connect(f).connect(g).connect(dest);
  src.start(t0); src.stop(t0 + dur + 0.05);
  return { filter: f, gain: g };
}

function tone(ac, dest, t0, dur, freq, { type = 'sine', gain = 0.2, attack = 0.01, decay = dur } = {}) {
  const o = ac.createOscillator(); o.type = type; o.frequency.value = freq;
  const g = ac.createGain();
  g.gain.setValueAtTime(0, t0);
  g.gain.linearRampToValueAtTime(gain, t0 + attack);
  g.gain.exponentialRampToValueAtTime(0.0001, t0 + Math.max(attack + 0.01, decay));
  o.connect(g).connect(dest);
  o.start(t0); o.stop(t0 + dur + 0.05);
  return o;
}

function thump(ac, dest, t, gain = 0.6) {
  const o = ac.createOscillator(); o.type = 'sine';
  o.frequency.setValueAtTime(90, t); o.frequency.exponentialRampToValueAtTime(40, t + 0.15);
  const g = ac.createGain(); g.gain.setValueAtTime(gain, t); g.gain.exponentialRampToValueAtTime(0.001, t + 0.25);
  o.connect(g).connect(dest); o.start(t); o.stop(t + 0.3);
}

function playSfx(ac, dest, kind, t0, dur, seed) {
  const r = rng(seed);
  switch (kind) {
    case 'wind': {
      const n = noise(ac, dest, t0, dur, { type: 'bandpass', freq: 400, q: 0.7, gain: 0.25, attack: 1, release: 1, seed });
      n.filter.frequency.setValueAtTime(300, t0);
      n.filter.frequency.linearRampToValueAtTime(900, t0 + dur / 2);
      n.filter.frequency.linearRampToValueAtTime(350, t0 + dur);
      break;
    }
    case 'crickets':
      for (let t = t0; t < t0 + dur; t += 0.35 + r() * 0.4)
        for (let k = 0; k < 3; k++) tone(ac, dest, t + k * 0.05, 0.04, 4200 + r() * 300, { gain: 0.03, decay: 0.04 });
      break;
    case 'whisper':
      for (let t = t0 + 0.2; t < t0 + dur - 0.5; t += 0.9 + r() * 0.8)
        noise(ac, dest, t, 0.5 + r() * 0.4, { type: 'bandpass', freq: 2500 + r() * 1500, q: 2, gain: 0.12, attack: 0.15, release: 0.25, seed: seed + Math.floor(t * 10) });
      break;
    case 'heartbeat':
      for (let t = t0 + 0.1; t < t0 + dur; t += 0.85) { thump(ac, dest, t, 0.7); thump(ac, dest, t + 0.22, 0.5); }
      break;
    case 'footsteps':
      for (let t = t0 + 0.1; t < t0 + dur; t += 0.42)
        noise(ac, dest, t, 0.09, { type: 'lowpass', freq: 600, gain: 0.35, attack: 0.005, release: 0.07, seed: seed + Math.floor(t * 100) });
      break;
    case 'stinger': {
      [0, 1, 6, 11].forEach((st) => tone(ac, dest, t0, 2.5, 110 * 2 ** (st / 12), { type: 'sawtooth', gain: 0.06, attack: 0.02, decay: 2.4 }));
      noise(ac, dest, t0, 1.2, { type: 'highpass', freq: 1500, gain: 0.25, attack: 0.01, release: 1.1, seed });
      thump(ac, dest, t0, 0.9);
      break;
    }
    case 'rain':
      noise(ac, dest, t0, dur, { type: 'highpass', freq: 2500, gain: 0.12, attack: 0.6, release: 0.6, seed });
      break;
    case 'clock':
      for (let t = t0; t < t0 + dur; t += 0.5)
        tone(ac, dest, t, 0.03, (Math.round((t - t0) * 2) % 2) ? 1800 : 2200, { type: 'square', gain: 0.05, decay: 0.03 });
      break;
    case 'thunder': {
      const n = noise(ac, dest, t0, Math.min(dur, 3.5), { type: 'lowpass', freq: 300, gain: 0.6, attack: 0.05, release: 2.8, seed });
      n.filter.frequency.exponentialRampToValueAtTime(80, t0 + 3);
      break;
    }
    default:
  }
}

function music(ac, dest, mood, total, seed) {
  const r = rng(seed);
  const master = ac.createGain(); master.gain.value = 1; master.connect(dest);
  if (mood === 'horror') {
    // low detuned drone with slowly breathing filter
    const f = ac.createBiquadFilter(); f.type = 'lowpass'; f.frequency.value = 220; f.Q.value = 4; f.connect(master);
    [55, 55.6, 82.4].forEach((fr) => {
      const o = ac.createOscillator(); o.type = 'sawtooth'; o.frequency.value = fr;
      const g = ac.createGain(); g.gain.value = 0.08; o.connect(g).connect(f); o.start(0); o.stop(total);
    });
    const lfo = ac.createOscillator(); lfo.frequency.value = 0.07; const lg = ac.createGain(); lg.gain.value = 120;
    lfo.connect(lg).connect(f.frequency); lfo.start(0); lfo.stop(total);
    // dissonant high glass tones
    for (let t = 2; t < total - 2; t += 5 + r() * 4) {
      const base = 880 * 2 ** (Math.floor(r() * 6) / 12);
      tone(ac, master, t, 4, base, { gain: 0.025, attack: 1.5, decay: 4 });
      tone(ac, master, t + 0.3, 4, base * 2 ** (1 / 12), { gain: 0.02, attack: 1.5, decay: 4 });
    }
    // distant booms
    for (let t = 6; t < total - 1; t += 9 + r() * 6) thump(ac, master, t, 0.35);
  } else if (mood === 'crime') {
    const scale = [0, 3, 5, 7, 8, 10, 12];
    for (let t = 0; t < total; t += 0.5) tone(ac, master, t, 0.45, 55 * (Math.floor(t / 4) % 2 ? 2 ** (8 / 12) : 1), { gain: 0.12, attack: 0.01, decay: 0.45 });
    for (let t = 1; t < total - 1; t += 1 + Math.floor(r() * 3) * 0.5) {
      const n = scale[Math.floor(r() * scale.length)];
      tone(ac, master, t, 1.6, 220 * 2 ** (n / 12), { type: 'triangle', gain: 0.05, attack: 0.005, decay: 1.6 });
    }
    const pad = ac.createBiquadFilter(); pad.type = 'lowpass'; pad.frequency.value = 900; pad.connect(master);
    [110, 130.8, 164.8].forEach((fr) => {
      const o = ac.createOscillator(); o.type = 'sawtooth'; o.frequency.value = fr;
      const g = ac.createGain(); g.gain.value = 0.015; o.connect(g).connect(pad); o.start(0); o.stop(total);
    });
  } else {
    // riddle: playful-mysterious whole-tone arpeggio + soft pad
    const wt = [0, 2, 4, 6, 8, 10, 12];
    for (let t = 0, i = 0; t < total; t += 0.25, i++) {
      if (i % 2 === 0 || r() > 0.6) tone(ac, master, t, 0.3, 440 * 2 ** (wt[(i * 3) % wt.length] / 12), { type: 'triangle', gain: 0.035, decay: 0.3 });
    }
    for (let t = 0; t < total; t += 2) tone(ac, master, t, 2, 110 * 2 ** (wt[Math.floor(t / 2) % 4] / 12), { gain: 0.08, attack: 0.3, decay: 2 });
  }
  // fade in / out
  master.gain.setValueAtTime(0, 0);
  master.gain.linearRampToValueAtTime(1, 1.5);
  master.gain.setValueAtTime(1, Math.max(1.6, total - 2));
  master.gain.linearRampToValueAtTime(0, total);
}

/**
 * timeline: [{ start, duration, voiceBuffer?, voiceOffset, sfx }]
 */
export async function buildMix({ timeline, mood, total, seed = 11, musicLevel = 0.55 }) {
  const ac = new OfflineAudioContext(2, Math.ceil(SR * total), SR);
  const comp = ac.createDynamicsCompressor();
  comp.threshold.value = -14; comp.ratio.value = 3; comp.connect(ac.destination);

  const voiceBus = ac.createGain(); voiceBus.gain.value = 1.0; voiceBus.connect(comp);
  const musicBus = ac.createGain(); musicBus.connect(comp);
  const sfxBus = ac.createGain(); sfxBus.gain.value = 0.8; sfxBus.connect(comp);

  // auto-ducking: music dips while the narrator speaks
  musicBus.gain.setValueAtTime(musicLevel, 0);
  timeline.forEach((s) => {
    if (!s.voiceBuffer) return;
    const vs = s.start + s.voiceOffset, ve = vs + s.voiceBuffer.duration;
    musicBus.gain.setTargetAtTime(musicLevel * 0.35, Math.max(0, vs - 0.15), 0.08);
    musicBus.gain.setTargetAtTime(musicLevel, ve + 0.05, 0.25);
  });

  music(ac, musicBus, mood, total, seed);
  timeline.forEach((s, i) => {
    if (s.voiceBuffer) {
      const src = ac.createBufferSource(); src.buffer = s.voiceBuffer;
      src.connect(voiceBus); src.start(s.start + s.voiceOffset);
    }
    if (s.sfx && s.sfx !== 'none') playSfx(ac, sfxBus, s.sfx, s.start, s.duration, seed + i * 31);
  });
  return ac.startRendering();
}

export function audioBufferToWav(buf) {
  const ch = buf.numberOfChannels, len = buf.length * ch * 2 + 44;
  const out = new DataView(new ArrayBuffer(len));
  const w = (o, s) => [...s].forEach((c, i) => out.setUint8(o + i, c.charCodeAt(0)));
  w(0, 'RIFF'); out.setUint32(4, len - 8, true); w(8, 'WAVE'); w(12, 'fmt ');
  out.setUint32(16, 16, true); out.setUint16(20, 1, true); out.setUint16(22, ch, true);
  out.setUint32(24, buf.sampleRate, true); out.setUint32(28, buf.sampleRate * ch * 2, true);
  out.setUint16(32, ch * 2, true); out.setUint16(34, 16, true); w(36, 'data'); out.setUint32(40, len - 44, true);
  const chans = [...Array(ch)].map((_, i) => buf.getChannelData(i));
  let o = 44;
  for (let i = 0; i < buf.length; i++) for (let c = 0; c < ch; c++) {
    const v = Math.max(-1, Math.min(1, chans[c][i]));
    out.setInt16(o, v < 0 ? v * 0x8000 : v * 0x7fff, true); o += 2;
  }
  return new Blob([out], { type: 'audio/wav' });
}

export { ctx as audioContext };

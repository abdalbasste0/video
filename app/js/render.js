// المونتير: يركّب الفيديو داخل المتصفح (حركة كاميرا، انتقالات، ترجمة كلمة بكلمة، مؤثرات بصرية، عدّاد الألغاز)
import { rng } from './procedural-art.js';
import { stripTags, } from './ai.js';
import { audioContext } from './audio.js';

export const FONT = "'Cairo', 'Tajawal', 'Noto Kufi Arabic', 'Segoe UI', Tahoma, sans-serif";

const GRADES = {
  horror: { tint: 'rgba(120,10,20,0.18)', accent: '#ff3b3b', flicker: true },
  crime: { tint: 'rgba(20,60,120,0.20)', accent: '#ffc83d', flicker: false },
  riddle: { tint: 'rgba(90,40,160,0.18)', accent: '#b98cff', flicker: false },
};

export function pickMime() {
  const opts = [
    'video/mp4;codecs=avc1.42E01E,mp4a.40.2',
    'video/mp4',
    'video/webm;codecs=vp9,opus',
    'video/webm;codecs=vp8,opus',
    'video/webm',
  ];
  return opts.find((m) => window.MediaRecorder && MediaRecorder.isTypeSupported(m)) || 'video/webm';
}

function makeGrain(w, h, seed) {
  const c = document.createElement('canvas'); c.width = Math.ceil(w / 3); c.height = Math.ceil(h / 3);
  const g = c.getContext('2d'); const img = g.createImageData(c.width, c.height); const r = rng(seed);
  for (let i = 0; i < img.data.length; i += 4) { const v = r() * 255; img.data[i] = img.data[i + 1] = img.data[i + 2] = v; img.data[i + 3] = 40; }
  g.putImageData(img, 0, 0); return c;
}

function makeVignette(w, h) {
  const c = document.createElement('canvas'); c.width = w; c.height = h; const g = c.getContext('2d');
  const v = g.createRadialGradient(w / 2, h / 2, Math.min(w, h) * 0.35, w / 2, h / 2, Math.max(w, h) * 0.72);
  v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(0,0,0,0.75)');
  g.fillStyle = v; g.fillRect(0, 0, w, h); return c;
}

// Split narration into caption chunks with timings spread across the spoken window.
export function buildCaptions(timeline, wordsPerChunk) {
  const caps = [];
  timeline.forEach((s) => {
    const words = stripTags(s.narration).split(/\s+/).filter(Boolean);
    if (!words.length) return;
    const speak = s.voiceDuration;
    const start = s.start + s.voiceOffset;
    const totalChars = words.reduce((a, w) => a + w.length + 1, 0);
    let acc = 0;
    const timed = words.map((w) => {
      const t0 = start + (acc / totalChars) * speak; acc += w.length + 1;
      return { w, t0, t1: start + (acc / totalChars) * speak };
    });
    for (let i = 0; i < timed.length; i += wordsPerChunk) {
      const chunk = timed.slice(i, i + wordsPerChunk);
      caps.push({ words: chunk, t0: chunk[0].t0, t1: chunk[chunk.length - 1].t1 + 0.12 });
    }
  });
  return caps;
}

function drawCover(g, img, W, H, scale, dx, dy) {
  const ir = img.width / img.height, cr = W / H;
  let w, h;
  if (ir > cr) { h = H * scale; w = h * ir; } else { w = W * scale; h = w / ir; }
  g.drawImage(img, (W - w) / 2 + dx, (H - h) / 2 + dy, w, h);
}

function motionAt(kind, p, W, H, seed, t) {
  const e = p * p * (3 - 2 * p); // smoothstep
  switch (kind) {
    case 'zoomIn': return { s: 1.06 + 0.16 * e, dx: 0, dy: 0 };
    case 'zoomOut': return { s: 1.22 - 0.16 * e, dx: 0, dy: 0 };
    case 'panLeft': return { s: 1.18, dx: (0.5 - e) * W * 0.12, dy: 0 };
    case 'panRight': return { s: 1.18, dx: (e - 0.5) * W * 0.12, dy: 0 };
    case 'shake': {
      const a = Math.min(W, H) * 0.008;
      return { s: 1.14 + 0.05 * e, dx: Math.sin(t * 37 + seed) * a + Math.sin(t * 13) * a, dy: Math.cos(t * 41 + seed) * a };
    }
    default: return { s: 1.08, dx: 0, dy: 0 };
  }
}

function wrapLines(g, text, maxW) {
  const words = text.split(/\s+/); const lines = []; let cur = '';
  words.forEach((w) => {
    const test = cur ? cur + ' ' + w : w;
    if (g.measureText(test).width > maxW && cur) { lines.push(cur); cur = w; } else cur = test;
  });
  if (cur) lines.push(cur);
  return lines;
}

export function drawFrame(g, st, t) {
  const { W, H, timeline, images, captions, mood, grain, vignette, total, outro, channel, cta } = st;
  const grade = GRADES[mood] || GRADES.horror;
  const U = Math.min(W, H) / 100;
  const vertical = H > W;
  g.save();
  g.fillStyle = '#000'; g.fillRect(0, 0, W, H);

  let idx = timeline.findIndex((s) => t >= s.start && t < s.start + s.duration);
  const inOutro = t >= outro.start;
  if (idx < 0) idx = timeline.length - 1;
  const sc = timeline[idx];
  const p = Math.min(1, Math.max(0, (t - sc.start) / sc.duration));
  const m = motionAt(sc.motion, p, W, H, idx, t);
  if (images[idx]) drawCover(g, images[idx], W, H, m.s, m.dx, m.dy);

  // crossfade into next scene during the last 0.45s
  const fade = 0.45;
  const next = timeline[idx + 1];
  if (next && t > sc.start + sc.duration - fade && images[idx + 1]) {
    g.globalAlpha = (t - (sc.start + sc.duration - fade)) / fade;
    const mn = motionAt(next.motion, 0, W, H, idx + 1, t);
    drawCover(g, images[idx + 1], W, H, mn.s, mn.dx, mn.dy);
    g.globalAlpha = 1;
  }

  // colour grade + vignette + grain
  g.globalCompositeOperation = 'soft-light';
  g.fillStyle = grade.tint; g.fillRect(0, 0, W, H);
  g.globalCompositeOperation = 'source-over';
  g.drawImage(vignette, 0, 0);
  g.globalCompositeOperation = 'overlay';
  const gi = Math.floor(t * 24) % grain.length;
  g.drawImage(grain[gi], 0, 0, W, H);
  g.globalCompositeOperation = 'source-over';
  if (grade.flicker) {
    const f = Math.sin(t * 7.3) * Math.sin(t * 2.1 + 1) * Math.sin(t * 17.7);
    if (f > 0.55) { g.fillStyle = `rgba(0,0,0,${(f - 0.55) * 0.9})`; g.fillRect(0, 0, W, H); }
    if (sc.sfx === 'stinger' && t - sc.start < 0.18) { g.fillStyle = 'rgba(255,255,255,0.35)'; g.fillRect(0, 0, W, H); }
  }

  g.direction = 'rtl'; g.textAlign = 'center'; g.textBaseline = 'middle';

  // on-screen headline pop
  if (sc.onScreenText && !inOutro) {
    const k = Math.min(1, (t - sc.start) / 0.35);
    const size = (vertical ? 7.5 : 6) * U * (0.7 + 0.3 * k);
    g.font = `900 ${size}px ${FONT}`;
    const y = vertical ? H * 0.17 : H * 0.15;
    const lines = wrapLines(g, sc.onScreenText, W * 0.86);
    lines.forEach((ln, i) => {
      const ly = y + i * size * 1.25;
      const tw = g.measureText(ln).width;
      g.fillStyle = 'rgba(0,0,0,0.55)';
      g.fillRect(W / 2 - tw / 2 - U * 2, ly - size * 0.65, tw + U * 4, size * 1.3);
      g.fillStyle = grade.accent; g.globalAlpha = k;
      g.fillText(ln, W / 2, ly);
      g.globalAlpha = 1;
    });
  }

  // riddle countdown ring
  if (sc.countdown > 0 && !inOutro) {
    const left = Math.min(sc.countdown, Math.max(0, sc.countdown - (t - (sc.cdStart ?? sc.start))));
    const cx = W / 2, cy = vertical ? H * 0.42 : H * 0.45, rad = U * 13;
    g.lineWidth = U * 2.2; g.strokeStyle = 'rgba(255,255,255,0.2)';
    g.beginPath(); g.arc(cx, cy, rad, 0, Math.PI * 2); g.stroke();
    g.strokeStyle = grade.accent;
    g.beginPath(); g.arc(cx, cy, rad, -Math.PI / 2, -Math.PI / 2 + (left / sc.countdown) * Math.PI * 2); g.stroke();
    g.fillStyle = '#fff'; g.font = `900 ${U * 12}px ${FONT}`;
    g.fillText(String(Math.ceil(left)), cx, cy + U);
  }

  // captions (active word highlighted)
  const cap = captions.find((c) => t >= c.t0 && t < c.t1);
  if (cap && !inOutro) {
    const size = (vertical ? 6.4 : 5) * U;
    g.font = `800 ${size}px ${FONT}`;
    const y = vertical ? H * 0.72 : H * 0.84;
    const full = cap.words.map((w) => w.w).join(' ');
    const lines = wrapLines(g, full, W * 0.88);
    let wi = 0;
    lines.forEach((ln, li) => {
      const ly = y + li * size * 1.3;
      const lw = ln.split(' ');
      // measure for RTL manual layout (right to left)
      const widths = lw.map((w) => g.measureText(w).width);
      const space = g.measureText(' ').width;
      const lineW = widths.reduce((a, b) => a + b, 0) + space * (lw.length - 1);
      let x = W / 2 + lineW / 2;
      lw.forEach((w, k) => {
        const word = cap.words[wi++];
        const active = word && t >= word.t0 && t < word.t1;
        const cx = x - widths[k] / 2;
        g.lineWidth = size * 0.18; g.strokeStyle = 'rgba(0,0,0,0.9)'; g.lineJoin = 'round';
        g.strokeText(w, cx, ly);
        g.fillStyle = active ? grade.accent : '#ffffff';
        if (active) { g.save(); g.translate(cx, ly); g.scale(1.08, 1.08); g.fillText(w, 0, 0); g.restore(); } else g.fillText(w, cx, ly);
        x -= widths[k] + space;
      });
    });
  }

  // outro card
  if (inOutro) {
    const k = Math.min(1, (t - outro.start) / 0.5);
    g.fillStyle = `rgba(0,0,0,${0.65 * k})`; g.fillRect(0, 0, W, H);
    g.globalAlpha = k;
    g.font = `800 ${(vertical ? 5.2 : 4.2) * U}px ${FONT}`; g.fillStyle = '#fff';
    wrapLines(g, cta || '', W * 0.85).forEach((ln, i) => g.fillText(ln, W / 2, H * 0.42 + i * U * 7));
    const bw = U * 40, bh = U * 10, bx = W / 2 - bw / 2, by = H * 0.6;
    g.fillStyle = '#e62117'; roundRect(g, bx, by, bw, bh, U * 2); g.fill();
    g.fillStyle = '#fff'; g.font = `900 ${U * 5}px ${FONT}`; g.fillText('اشترك 🔔', W / 2, by + bh / 2 + U * 0.4);
    g.globalAlpha = 1;
  }

  // retention progress bar + channel tag
  g.fillStyle = 'rgba(255,255,255,0.18)'; g.fillRect(0, 0, W, U * 0.7);
  g.fillStyle = grade.accent; g.fillRect(W - (t / total) * W, 0, (t / total) * W, U * 0.7);
  if (channel) {
    g.font = `700 ${U * 2.6}px ${FONT}`; g.fillStyle = 'rgba(255,255,255,0.55)';
    g.textAlign = 'left'; g.direction = 'ltr'; g.fillText('@' + channel, U * 3, H - U * 4);
  }
  g.restore();
}

function roundRect(g, x, y, w, h, r) {
  g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r);
  g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath();
}

export async function prepareState({ W, H, timeline, images, mood, total, outro, channel, cta }) {
  await document.fonts.load(`800 40px Cairo`).catch(() => {});
  const vertical = H > W;
  return {
    W, H, timeline, images, mood, total, outro, channel, cta,
    captions: buildCaptions(timeline, vertical ? 3 : 5),
    grain: [1, 2, 3, 4].map((s) => makeGrain(W, H, s)),
    vignette: makeVignette(W, H),
  };
}

export async function renderVideo({ st, mix, onProgress, signal }) {
  const canvas = document.createElement('canvas');
  canvas.width = st.W; canvas.height = st.H;
  const g = canvas.getContext('2d');
  drawFrame(g, st, 0);

  const ac = audioContext();
  await ac.resume();
  const dest = ac.createMediaStreamDestination();
  const src = ac.createBufferSource(); src.buffer = mix; src.connect(dest);

  const vstream = canvas.captureStream(30);
  const stream = new MediaStream([...vstream.getVideoTracks(), ...dest.stream.getAudioTracks()]);
  const mimeType = pickMime();
  const rec = new MediaRecorder(stream, { mimeType, videoBitsPerSecond: st.H >= 1080 && st.W >= 1080 ? 8_000_000 : 3_500_000, audioBitsPerSecond: 192_000 });
  const chunks = [];
  rec.ondataavailable = (e) => e.data.size && chunks.push(e.data);
  const done = new Promise((res) => (rec.onstop = res));

  rec.start(1000);
  const t0 = ac.currentTime + 0.1;
  src.start(t0);
  let stopped = false;
  await new Promise((resolve, reject) => {
    const tick = () => {
      if (signal?.aborted) { stopped = true; reject(new DOMException('aborted', 'AbortError')); return; }
      const t = ac.currentTime - t0;
      if (t >= st.total + 0.15) { resolve(); return; }
      drawFrame(g, st, Math.max(0, t));
      onProgress?.(Math.min(1, Math.max(0, t / st.total)));
      // rAF while visible; timer fallback keeps going (slower) if the tab is hidden
      if (document.hidden) setTimeout(tick, 33); else requestAnimationFrame(tick);
    };
    tick();
  }).finally(() => {
    try { src.stop(); } catch { /* already stopped */ }
    rec.stop();
    stream.getTracks().forEach((tr) => tr.stop());
  });
  await done;
  if (stopped) return null;
  return new Blob(chunks, { type: mimeType.split(';')[0] });
}

export async function renderThumbnail({ image, text, mood, W, H, badge }) {
  await document.fonts.load(`900 80px Cairo`).catch(() => {});
  const c = document.createElement('canvas'); c.width = W; c.height = H;
  const g = c.getContext('2d'); const U = Math.min(W, H) / 100;
  const grade = GRADES[mood] || GRADES.horror;
  g.filter = 'contrast(1.25) saturate(1.3) brightness(1.05)';
  if (image) drawCover(g, image, W, H, 1.05, 0, 0);
  g.filter = 'none';
  g.drawImage(makeVignette(W, H), 0, 0);
  const sg = g.createLinearGradient(0, H * 0.45, 0, H);
  sg.addColorStop(0, 'rgba(0,0,0,0)'); sg.addColorStop(1, 'rgba(0,0,0,0.85)');
  g.fillStyle = sg; g.fillRect(0, 0, W, H);

  g.direction = 'rtl'; g.textAlign = 'center'; g.textBaseline = 'middle';
  const size = (H > W ? 13 : 16) * U;
  g.font = `900 ${size}px ${FONT}`;
  const lines = wrapLines(g, text || '', W * 0.9);
  const baseY = H - size * (lines.length * 1.05) - U * 6;
  lines.forEach((ln, i) => {
    const y = baseY + i * size * 1.1;
    g.lineWidth = size * 0.2; g.strokeStyle = '#000'; g.lineJoin = 'round'; g.strokeText(ln, W / 2, y);
    g.fillStyle = i === 0 ? grade.accent : '#fff'; g.fillText(ln, W / 2, y);
  });
  if (badge) {
    g.font = `900 ${U * 6}px ${FONT}`;
    const bw = g.measureText(badge).width + U * 6;
    g.fillStyle = grade.accent; roundRect(g, W - bw - U * 4, U * 4, bw, U * 10, U * 2); g.fill();
    g.fillStyle = '#000'; g.fillText(badge, W - bw / 2 - U * 4, U * 9.4);
  }
  return new Promise((res) => c.toBlob(res, 'image/jpeg', 0.92));
}

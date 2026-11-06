// رسام احتياطي يعمل بدون إنترنت: يرسم مشهدًا سينمائيًا مظلمًا بأسلوب "ستيك مان" من كلمات الوصف
export function rng(seed) {
  let a = (seed >>> 0) || 1;
  return () => {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// Latin keywords match whole words only ("man" must not match "woman"); Arabic ones match as substrings.
const has = (p, words) => words.some((w) => (/^[a-z ]+$/.test(w) ? new RegExp(`\\b${w}s?\\b`).test(p) : p.includes(w)));

export async function paintProcedural({ prompt = '', width = 1080, height = 1920, seed = 1 }) {
  const c = document.createElement('canvas');
  c.width = width; c.height = height;
  const g = c.getContext('2d');
  const r = rng(seed);
  const p = prompt.toLowerCase();
  const W = width, H = height, U = Math.min(W, H) / 100;

  const indoor = has(p, ['room', 'interior', 'غرفة', 'corridor', 'ممر', 'hall', 'office', 'مكتب', 'basement', 'قبو', 'kitchen']);
  const city = has(p, ['city', 'street', 'مدينة', 'شارع', 'alley', 'زقاق', 'police', 'شرطة', 'car', 'سيارة', 'building']);
  const crime = has(p, ['crime', 'detective', 'جريمة', 'محقق', 'evidence', 'دليل', 'police', 'شرطة']);
  const riddle = has(p, ['riddle', 'puzzle', 'لغز', 'clue', 'question', 'سؤال']);

  // sky / wall
  const top = crime ? '#0b1320' : riddle ? '#140f2a' : '#12060a';
  const mid = crime ? '#1d2c44' : riddle ? '#2c1f5a' : '#3a0d14';
  const grd = g.createLinearGradient(0, 0, 0, H);
  grd.addColorStop(0, top); grd.addColorStop(0.65, mid); grd.addColorStop(1, '#050505');
  g.fillStyle = grd; g.fillRect(0, 0, W, H);

  const horizon = H * (indoor ? 0.78 : 0.7);

  if (!indoor) {
    // stars
    g.fillStyle = 'rgba(255,255,255,0.6)';
    for (let i = 0; i < 80; i++) g.fillRect(r() * W, r() * horizon * 0.7, r() * 2 + 0.5, r() * 2 + 0.5);
    // moon
    const mx = W * (0.2 + r() * 0.6), my = H * (0.12 + r() * 0.12), mr = U * (8 + r() * 6);
    const mg = g.createRadialGradient(mx, my, mr * 0.2, mx, my, mr * 4);
    mg.addColorStop(0, crime ? 'rgba(200,220,255,0.35)' : 'rgba(255,220,200,0.35)');
    mg.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = mg; g.fillRect(0, 0, W, H);
    g.fillStyle = crime ? '#dfe8ff' : '#f3e2c9';
    g.beginPath(); g.arc(mx, my, mr, 0, Math.PI * 2); g.fill();
  } else {
    // window with light
    const wx = W * (0.15 + r() * 0.5), wy = H * 0.22, ww = W * 0.22, wh = H * 0.2;
    g.fillStyle = 'rgba(160,190,255,0.18)'; g.fillRect(wx, wy, ww, wh);
    g.strokeStyle = '#000'; g.lineWidth = U * 1.2;
    g.strokeRect(wx, wy, ww, wh);
    g.beginPath(); g.moveTo(wx + ww / 2, wy); g.lineTo(wx + ww / 2, wy + wh); g.moveTo(wx, wy + wh / 2); g.lineTo(wx + ww, wy + wh / 2); g.stroke();
    // door
    if (has(p, ['door', 'باب'])) {
      g.fillStyle = '#0a0a0a'; g.fillRect(W * 0.68, horizon - H * 0.34, W * 0.2, H * 0.34);
      g.fillStyle = 'rgba(255,200,120,0.25)'; g.fillRect(W * 0.68, horizon - H * 0.34, W * 0.025, H * 0.34);
    }
  }

  // ground
  g.fillStyle = '#060606';
  g.beginPath(); g.moveTo(0, horizon);
  for (let x = 0; x <= W; x += W / 20) g.lineTo(x, horizon + (indoor ? 0 : (r() - 0.5) * U * 3));
  g.lineTo(W, H); g.lineTo(0, H); g.fill();

  // landscape elements
  if (!indoor) {
    if (city) {
      for (let i = 0; i < 9; i++) {
        const bw = W * (0.08 + r() * 0.12), bh = H * (0.12 + r() * 0.3), bx = r() * W;
        g.fillStyle = '#07090d'; g.fillRect(bx, horizon - bh, bw, bh);
        g.fillStyle = 'rgba(255,210,120,0.5)';
        for (let k = 0; k < 6; k++) if (r() > 0.55) g.fillRect(bx + r() * bw * 0.8, horizon - bh + r() * bh * 0.85, U, U * 1.4);
      }
      // street lamp
      const lx = W * (0.1 + r() * 0.8);
      g.strokeStyle = '#000'; g.lineWidth = U; g.beginPath(); g.moveTo(lx, horizon); g.lineTo(lx, horizon - H * 0.3); g.stroke();
      const lg = g.createRadialGradient(lx, horizon - H * 0.3, 0, lx, horizon - H * 0.3, H * 0.25);
      lg.addColorStop(0, 'rgba(255,200,120,0.35)'); lg.addColorStop(1, 'rgba(0,0,0,0)');
      g.fillStyle = lg; g.fillRect(0, 0, W, H);
    } else {
      const trees = has(p, ['forest', 'tree', 'غابة', 'شجر', 'cane', 'قصب', 'field', 'حقل', 'غيط']) ? 14 : 6;
      for (let i = 0; i < trees; i++) drawTree(g, r() * W, horizon + r() * U * 4, H * (0.15 + r() * 0.3), r, U);
      if (has(p, ['house', 'بيت', 'منزل', 'village', 'قرية', 'cabin', 'كوخ'])) drawHouse(g, W * (0.55 + r() * 0.3), horizon, W * 0.28, H * 0.16, U);
      if (has(p, ['road', 'طريق', 'path', 'ممر'])) {
        g.fillStyle = '#121212';
        g.beginPath(); g.moveTo(W * 0.42, horizon); g.lineTo(W * 0.58, horizon); g.lineTo(W * 0.95, H); g.lineTo(W * 0.05, H); g.fill();
      }
    }
  }

  // characters (stick-figure silhouettes)
  const people = [];
  if (has(p, ['man', 'father', 'رجل', 'أب', 'detective', 'محقق', 'person', 'شخص'])) people.push('man');
  if (has(p, ['girl', 'daughter', 'بنت', 'فتاة', 'child', 'طفل'])) people.push('child');
  if (has(p, ['woman', 'امرأة', 'lady', 'ghost', 'شبح', 'جنية', 'white dress', 'فستان'])) people.push('ghost');
  if (!people.length && !has(p, ['empty', 'فارغ'])) people.push('man');
  people.forEach((kind, i) => {
    const x = W * (0.3 + i * 0.2 + (r() - 0.5) * 0.08);
    const h = kind === 'child' ? H * 0.13 : H * 0.2;
    drawFigure(g, x, horizon + U * 2, h, kind, U);
  });

  if (has(p, ['eye', 'عين', 'eyes', 'عيون'])) {
    for (let i = 0; i < 2; i++) {
      const ex = W * (0.75 + i * 0.05), ey = horizon - H * 0.15;
      g.fillStyle = '#ff2a2a'; g.shadowColor = '#ff0000'; g.shadowBlur = U * 4;
      g.beginPath(); g.ellipse(ex, ey, U * 1.2, U * 0.6, 0, 0, Math.PI * 2); g.fill();
      g.shadowBlur = 0;
    }
  }
  if (riddle || has(p, ['clock', 'ساعة'])) drawClock(g, W * 0.8, H * 0.18, U * 9, r);
  if (has(p, ['lantern', 'فانوس', 'candle', 'شمعة', 'torch'])) {
    const lx = W * 0.35, ly = horizon - H * 0.1;
    const lg = g.createRadialGradient(lx, ly, 0, lx, ly, H * 0.18);
    lg.addColorStop(0, 'rgba(255,190,90,0.6)'); lg.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = lg; g.fillRect(0, 0, W, H);
  }

  // fog layers
  for (let i = 0; i < 5; i++) {
    const fy = horizon - H * 0.05 + r() * H * 0.15;
    const fg = g.createLinearGradient(0, fy - H * 0.06, 0, fy + H * 0.06);
    fg.addColorStop(0, 'rgba(180,180,200,0)'); fg.addColorStop(0.5, 'rgba(180,180,200,0.08)'); fg.addColorStop(1, 'rgba(180,180,200,0)');
    g.fillStyle = fg; g.fillRect(0, fy - H * 0.06, W, H * 0.12);
  }
  // vignette
  const vg = g.createRadialGradient(W / 2, H / 2, Math.min(W, H) * 0.3, W / 2, H / 2, Math.max(W, H) * 0.75);
  vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(0,0,0,0.85)');
  g.fillStyle = vg; g.fillRect(0, 0, W, H);

  return new Promise((res) => c.toBlob((b) => res(b), 'image/jpeg', 0.9));
}

function drawTree(g, x, base, h, r, U) {
  g.strokeStyle = '#030303'; g.lineCap = 'round';
  const branch = (x1, y1, len, ang, w, depth) => {
    if (depth === 0 || len < U) return;
    const x2 = x1 + Math.cos(ang) * len, y2 = y1 + Math.sin(ang) * len;
    g.lineWidth = w; g.beginPath(); g.moveTo(x1, y1); g.lineTo(x2, y2); g.stroke();
    const n = 2 + Math.floor(r() * 2);
    for (let i = 0; i < n; i++) branch(x2, y2, len * (0.6 + r() * 0.15), ang + (r() - 0.5) * 1.3, w * 0.65, depth - 1);
  };
  branch(x, base, h * 0.4, -Math.PI / 2 + (r() - 0.5) * 0.2, U * 1.8, 6);
}

function drawHouse(g, x, base, w, h, U) {
  g.fillStyle = '#040404';
  g.fillRect(x - w / 2, base - h, w, h);
  g.beginPath(); g.moveTo(x - w * 0.6, base - h); g.lineTo(x, base - h * 1.7); g.lineTo(x + w * 0.6, base - h); g.fill();
  g.fillStyle = 'rgba(255,170,80,0.85)';
  g.fillRect(x - w * 0.3, base - h * 0.7, w * 0.15, h * 0.22);
  g.fillRect(x + w * 0.12, base - h * 0.7, w * 0.15, h * 0.22);
}

function drawFigure(g, x, base, h, kind, U) {
  const head = h * 0.13;
  g.save();
  if (kind === 'ghost') {
    g.fillStyle = 'rgba(235,235,245,0.85)'; g.shadowColor = '#fff'; g.shadowBlur = U * 6;
    g.beginPath(); g.arc(x, base - h + head, head, 0, Math.PI * 2); g.fill();
    g.beginPath(); g.moveTo(x - head * 0.9, base - h + head * 2);
    g.lineTo(x - head * 2.2, base); g.lineTo(x + head * 2.2, base); g.lineTo(x + head * 0.9, base - h + head * 2); g.fill();
    g.shadowBlur = 0; g.fillStyle = '#000';
    g.beginPath(); g.arc(x - head * 0.35, base - h + head, head * 0.18, 0, Math.PI * 2); g.arc(x + head * 0.35, base - h + head, head * 0.18, 0, Math.PI * 2); g.fill();
  } else {
    g.strokeStyle = '#000'; g.fillStyle = '#000'; g.lineWidth = Math.max(2, h * 0.04); g.lineCap = 'round';
    g.beginPath(); g.arc(x, base - h + head, head, 0, Math.PI * 2); g.fill();
    g.beginPath();
    g.moveTo(x, base - h + head * 2); g.lineTo(x, base - h * 0.42);
    g.moveTo(x, base - h * 0.42); g.lineTo(x - h * 0.12, base);
    g.moveTo(x, base - h * 0.42); g.lineTo(x + h * 0.12, base);
    g.moveTo(x, base - h * 0.72); g.lineTo(x - h * 0.16, base - h * 0.5);
    g.moveTo(x, base - h * 0.72); g.lineTo(x + h * 0.16, base - h * 0.5);
    g.stroke();
  }
  g.restore();
}

function drawClock(g, x, y, rad, r) {
  g.save();
  g.strokeStyle = 'rgba(230,220,255,0.9)'; g.lineWidth = rad * 0.08;
  g.beginPath(); g.arc(x, y, rad, 0, Math.PI * 2); g.stroke();
  for (let i = 0; i < 12; i++) {
    const a = (i / 12) * Math.PI * 2;
    g.beginPath(); g.moveTo(x + Math.cos(a) * rad * 0.8, y + Math.sin(a) * rad * 0.8); g.lineTo(x + Math.cos(a) * rad * 0.92, y + Math.sin(a) * rad * 0.92); g.stroke();
  }
  const a1 = r() * Math.PI * 2, a2 = r() * Math.PI * 2;
  g.beginPath(); g.moveTo(x, y); g.lineTo(x + Math.cos(a1) * rad * 0.5, y + Math.sin(a1) * rad * 0.5);
  g.moveTo(x, y); g.lineTo(x + Math.cos(a2) * rad * 0.75, y + Math.sin(a2) * rad * 0.75); g.stroke();
  g.restore();
}

// معالجة الصور: كشف الحواف، تصحيح المنظور، الفلاتر — بدون مكتبات خارجية
'use strict';

const Scanner = (() => {
  const MAX_SIDE = 2400;

  function makeCanvas(w, h) {
    const c = document.createElement('canvas');
    c.width = Math.max(1, Math.round(w));
    c.height = Math.max(1, Math.round(h));
    return c;
  }

  async function loadFile(file) {
    let src;
    try {
      src = await createImageBitmap(file, { imageOrientation: 'from-image' });
    } catch (_) {
      src = await new Promise((res, rej) => {
        const img = new Image();
        img.onload = () => res(img);
        img.onerror = rej;
        img.src = URL.createObjectURL(file);
      });
    }
    const w0 = src.width, h0 = src.height;
    const s = Math.min(1, MAX_SIDE / Math.max(w0, h0));
    const c = makeCanvas(w0 * s, h0 * s);
    c.getContext('2d').drawImage(src, 0, 0, c.width, c.height);
    if (src.close) src.close();
    return c;
  }

  // ---------- كشف حواف الورقة ----------
  function otsu(hist, total) {
    let sum = 0;
    for (let i = 0; i < 256; i++) sum += i * hist[i];
    let sumB = 0, wB = 0, best = 0, thr = 127;
    for (let t = 0; t < 256; t++) {
      wB += hist[t];
      if (!wB) continue;
      const wF = total - wB;
      if (!wF) break;
      sumB += t * hist[t];
      const mB = sumB / wB, mF = (sum - sumB) / wF;
      const v = wB * wF * (mB - mF) * (mB - mF);
      if (v > best) { best = v; thr = t; }
    }
    return thr;
  }

  function boxBlur(src, w, h, r) {
    const tmp = new Float32Array(w * h), out = new Float32Array(w * h);
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        let s = 0, n = 0;
        for (let k = -r; k <= r; k++) {
          const xx = x + k;
          if (xx >= 0 && xx < w) { s += src[y * w + xx]; n++; }
        }
        tmp[y * w + x] = s / n;
      }
    }
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        let s = 0, n = 0;
        for (let k = -r; k <= r; k++) {
          const yy = y + k;
          if (yy >= 0 && yy < h) { s += tmp[yy * w + x]; n++; }
        }
        out[y * w + x] = s / n;
      }
    }
    return out;
  }

  function defaultCorners(w, h, inset = 0.04) {
    const dx = w * inset, dy = h * inset;
    return [
      { x: dx, y: dy }, { x: w - dx, y: dy },
      { x: w - dx, y: h - dy }, { x: dx, y: h - dy },
    ];
  }

  function fullCorners(w, h) { return defaultCorners(w, h, 0); }

  function detectCorners(canvas) {
    const W = canvas.width, H = canvas.height;
    const s = Math.min(1, 320 / Math.max(W, H));
    const w = Math.max(8, Math.round(W * s)), h = Math.max(8, Math.round(H * s));
    const small = makeCanvas(w, h);
    const sctx = small.getContext('2d', { willReadFrequently: true });
    sctx.drawImage(canvas, 0, 0, w, h);
    const d = sctx.getImageData(0, 0, w, h).data;

    // سطوع مع عقوبة للتشبع اللوني (الورق عادة فاتح وقليل التشبع)
    const g = new Float32Array(w * h);
    for (let i = 0, p = 0; i < w * h; i++, p += 4) {
      const r = d[p], gg = d[p + 1], b = d[p + 2];
      const mx = Math.max(r, gg, b), mn = Math.min(r, gg, b);
      g[i] = 0.299 * r + 0.587 * gg + 0.114 * b - 0.5 * (mx - mn);
    }
    const bl = boxBlur(g, w, h, 2);
    const hist = new Uint32Array(256);
    for (let i = 0; i < bl.length; i++) hist[Math.max(0, Math.min(255, bl[i] | 0))]++;
    const t = otsu(hist, bl.length);

    const mask = new Uint8Array(w * h);
    for (let i = 0; i < bl.length; i++) mask[i] = bl[i] > t ? 1 : 0;

    // أكبر مكوّن متصل
    const label = new Int32Array(w * h);
    const stack = new Int32Array(w * h);
    let bestLabel = 0, bestSize = 0, cur = 0;
    for (let i = 0; i < mask.length; i++) {
      if (!mask[i] || label[i]) continue;
      cur++;
      let sp = 0, size = 0;
      stack[sp++] = i; label[i] = cur;
      while (sp) {
        const k = stack[--sp]; size++;
        const x = k % w, y = (k / w) | 0;
        if (x > 0 && mask[k - 1] && !label[k - 1]) { label[k - 1] = cur; stack[sp++] = k - 1; }
        if (x < w - 1 && mask[k + 1] && !label[k + 1]) { label[k + 1] = cur; stack[sp++] = k + 1; }
        if (y > 0 && mask[k - w] && !label[k - w]) { label[k - w] = cur; stack[sp++] = k - w; }
        if (y < h - 1 && mask[k + w] && !label[k + w]) { label[k + w] = cur; stack[sp++] = k + w; }
      }
      if (size > bestSize) { bestSize = size; bestLabel = cur; }
    }

    const frac = bestSize / (w * h);
    if (frac < 0.08 || frac > 0.985) return defaultCorners(W, H);

    let tl, tr, br, bll;
    let mnS = Infinity, mxS = -Infinity, mnD = Infinity, mxD = -Infinity;
    for (let i = 0; i < label.length; i++) {
      if (label[i] !== bestLabel) continue;
      const x = i % w, y = (i / w) | 0;
      const sum = x + y, dif = x - y;
      if (sum < mnS) { mnS = sum; tl = { x, y }; }
      if (sum > mxS) { mxS = sum; br = { x, y }; }
      if (dif > mxD) { mxD = dif; tr = { x, y }; }
      if (dif < mnD) { mnD = dif; bll = { x, y }; }
    }
    const k = 1 / s;
    const pts = [tl, tr, br, bll].map(p => ({
      x: Math.max(0, Math.min(W, (p.x + 0.5) * k)),
      y: Math.max(0, Math.min(H, (p.y + 0.5) * k)),
    }));
    // تحقق من أن الشكل الرباعي معقول
    const area = polyArea(pts);
    if (area < 0.08 * W * H) return defaultCorners(W, H);
    return pts;
  }

  function polyArea(p) {
    let a = 0;
    for (let i = 0; i < p.length; i++) {
      const j = (i + 1) % p.length;
      a += p[i].x * p[j].y - p[j].x * p[i].y;
    }
    return Math.abs(a) / 2;
  }

  // ---------- تصحيح المنظور ----------
  function solve(A, b) {
    const n = b.length;
    for (let i = 0; i < n; i++) {
      let piv = i;
      for (let r = i + 1; r < n; r++) if (Math.abs(A[r][i]) > Math.abs(A[piv][i])) piv = r;
      [A[i], A[piv]] = [A[piv], A[i]];
      [b[i], b[piv]] = [b[piv], b[i]];
      const d = A[i][i] || 1e-12;
      for (let r = i + 1; r < n; r++) {
        const f = A[r][i] / d;
        if (!f) continue;
        for (let c = i; c < n; c++) A[r][c] -= f * A[i][c];
        b[r] -= f * b[i];
      }
    }
    const x = new Array(n).fill(0);
    for (let i = n - 1; i >= 0; i--) {
      let s = b[i];
      for (let c = i + 1; c < n; c++) s -= A[i][c] * x[c];
      x[i] = s / (A[i][i] || 1e-12);
    }
    return x;
  }

  // مصفوفة تحويل من نقاط dst إلى نقاط src
  function homography(dst, src) {
    const A = [], b = [];
    for (let i = 0; i < 4; i++) {
      const { x, y } = dst[i], { x: u, y: v } = src[i];
      A.push([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.push(u);
      A.push([0, 0, 0, x, y, 1, -v * x, -v * y]); b.push(v);
    }
    const h = solve(A, b);
    h.push(1);
    return h;
  }

  const dist = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);

  function warp(canvas, corners) {
    const [tl, tr, br, bl] = corners;
    let ow = Math.max(dist(tl, tr), dist(bl, br));
    let oh = Math.max(dist(tl, bl), dist(tr, br));
    const lim = Math.min(1, MAX_SIDE / Math.max(ow, oh));
    ow = Math.max(16, Math.round(ow * lim));
    oh = Math.max(16, Math.round(oh * lim));

    const W = canvas.width, H = canvas.height;
    const sd = canvas.getContext('2d', { willReadFrequently: true }).getImageData(0, 0, W, H).data;
    const out = makeCanvas(ow, oh);
    const octx = out.getContext('2d');
    const od = octx.createImageData(ow, oh);
    const o = od.data;
    const h = homography(
      [{ x: 0, y: 0 }, { x: ow, y: 0 }, { x: ow, y: oh }, { x: 0, y: oh }],
      corners
    );
    let p = 0;
    for (let y = 0; y < oh; y++) {
      const yy = y + 0.5;
      for (let x = 0; x < ow; x++, p += 4) {
        const xx = x + 0.5;
        const den = h[6] * xx + h[7] * yy + 1;
        let u = (h[0] * xx + h[1] * yy + h[2]) / den - 0.5;
        let v = (h[3] * xx + h[4] * yy + h[5]) / den - 0.5;
        if (u < 0) u = 0; else if (u > W - 1) u = W - 1;
        if (v < 0) v = 0; else if (v > H - 1) v = H - 1;
        const x0 = u | 0, y0 = v | 0;
        const x1 = x0 < W - 1 ? x0 + 1 : x0, y1 = y0 < H - 1 ? y0 + 1 : y0;
        const fx = u - x0, fy = v - y0;
        const i00 = (y0 * W + x0) * 4, i10 = (y0 * W + x1) * 4;
        const i01 = (y1 * W + x0) * 4, i11 = (y1 * W + x1) * 4;
        for (let c = 0; c < 3; c++) {
          const top = sd[i00 + c] + (sd[i10 + c] - sd[i00 + c]) * fx;
          const bot = sd[i01 + c] + (sd[i11 + c] - sd[i01 + c]) * fx;
          o[p + c] = top + (bot - top) * fy;
        }
        o[p + 3] = 255;
      }
    }
    octx.putImageData(od, 0, 0);
    return out;
  }

  // ---------- الفلاتر ----------
  function percentile(hist, total, q) {
    let acc = 0;
    for (let i = 0; i < 256; i++) { acc += hist[i]; if (acc >= total * q) return i; }
    return 255;
  }

  function enhance(d, n) {
    // توازن الألوان بتقدير لون الورق (خلفية) + تمديد التباين
    for (let c = 0; c < 3; c++) {
      const hist = new Uint32Array(256);
      for (let i = 0; i < n; i++) hist[d[i * 4 + c]]++;
      const lo = percentile(hist, n, 0.02), hi = Math.max(lo + 1, percentile(hist, n, 0.9));
      const sc = 255 / (hi - lo);
      for (let i = 0; i < n; i++) {
        const v = (d[i * 4 + c] - lo) * sc;
        d[i * 4 + c] = v < 0 ? 0 : v > 255 ? 255 : v;
      }
    }
  }

  function toGray(d, n) {
    const g = new Uint8ClampedArray(n);
    for (let i = 0, p = 0; i < n; i++, p += 4) g[i] = 0.299 * d[p] + 0.587 * d[p + 1] + 0.114 * d[p + 2];
    return g;
  }

  function adaptiveBW(d, w, h) {
    const n = w * h;
    const g = toGray(d, n);
    const ii = new Float64Array((w + 1) * (h + 1));
    for (let y = 1; y <= h; y++) {
      let row = 0;
      for (let x = 1; x <= w; x++) {
        row += g[(y - 1) * w + (x - 1)];
        ii[y * (w + 1) + x] = ii[(y - 1) * (w + 1) + x] + row;
      }
    }
    const r = Math.max(8, Math.round(Math.max(w, h) / 40));
    for (let y = 0; y < h; y++) {
      const y0 = Math.max(0, y - r), y1 = Math.min(h, y + r + 1);
      for (let x = 0; x < w; x++) {
        const x0 = Math.max(0, x - r), x1 = Math.min(w, x + r + 1);
        const area = (x1 - x0) * (y1 - y0);
        const s = ii[y1 * (w + 1) + x1] - ii[y0 * (w + 1) + x1] - ii[y1 * (w + 1) + x0] + ii[y0 * (w + 1) + x0];
        const mean = s / area;
        const v = g[y * w + x] < mean * 0.88 ? 0 : 255;
        const p = (y * w + x) * 4;
        d[p] = d[p + 1] = d[p + 2] = v;
      }
    }
  }

  function applyFilter(canvas, mode) {
    const w = canvas.width, h = canvas.height;
    const out = makeCanvas(w, h);
    const ctx = out.getContext('2d', { willReadFrequently: true });
    ctx.drawImage(canvas, 0, 0);
    if (mode === 'color') return out;
    const img = ctx.getImageData(0, 0, w, h);
    const d = img.data, n = w * h;
    if (mode === 'enhance') enhance(d, n);
    else if (mode === 'gray') {
      enhance(d, n);
      const g = toGray(d, n);
      for (let i = 0, p = 0; i < n; i++, p += 4) d[p] = d[p + 1] = d[p + 2] = g[i];
    } else if (mode === 'bw') adaptiveBW(d, w, h);
    ctx.putImageData(img, 0, 0);
    return out;
  }

  function rotate(canvas, deg) {
    deg = ((deg % 360) + 360) % 360;
    if (!deg) return canvas;
    const swap = deg === 90 || deg === 270;
    const out = makeCanvas(swap ? canvas.height : canvas.width, swap ? canvas.width : canvas.height);
    const ctx = out.getContext('2d');
    ctx.translate(out.width / 2, out.height / 2);
    ctx.rotate((deg * Math.PI) / 180);
    ctx.drawImage(canvas, -canvas.width / 2, -canvas.height / 2);
    return out;
  }

  function process(page) {
    const warped = warp(page.source, page.corners);
    const filtered = applyFilter(warped, page.filter);
    return rotate(filtered, page.rotation);
  }

  return { loadFile, detectCorners, fullCorners, warp, applyFilter, rotate, process, makeCanvas };
})();

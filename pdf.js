// كاتب PDF بسيط يضمّن صور JPEG مباشرة (DCTDecode) — يعمل بدون إنترنت
'use strict';

const PdfWriter = (() => {
  const SIZES = { a4: [595.28, 841.89], letter: [612, 792] };
  const enc = new TextEncoder();

  async function canvasToJpeg(canvas, quality) {
    const blob = await new Promise(r => canvas.toBlob(r, 'image/jpeg', quality));
    return new Uint8Array(await blob.arrayBuffer());
  }

  // pages: [{canvas}] ; opts: {size: 'a4'|'letter'|'fit', quality, margin}
  async function build(pages, opts = {}) {
    const size = opts.size || 'a4';
    const quality = opts.quality ?? 0.85;
    const margin = opts.margin ?? (size === 'fit' ? 0 : 18);

    const chunks = [];
    const offsets = [];
    let len = 0;
    const push = (data) => {
      const b = typeof data === 'string' ? enc.encode(data) : data;
      chunks.push(b); len += b.length;
    };
    const n = pages.length;
    // ترقيم الكائنات: 1 الكتالوج، 2 الصفحات، ثم لكل صفحة 3 كائنات
    const pageObj = i => 3 + i * 3, imgObj = i => 4 + i * 3, cntObj = i => 5 + i * 3;
    const total = 2 + n * 3;
    const begin = (id) => { offsets[id] = len; push(`${id} 0 obj\n`); };

    push('%PDF-1.4\n%\xE2\xE3\xCF\xD3\n');
    begin(1); push('<< /Type /Catalog /Pages 2 0 R >>\nendobj\n');
    begin(2);
    push(`<< /Type /Pages /Count ${n} /Kids [${pages.map((_, i) => `${pageObj(i)} 0 R`).join(' ')}] >>\nendobj\n`);

    for (let i = 0; i < n; i++) {
      const cv = pages[i].canvas;
      const iw = cv.width, ih = cv.height;
      let pw, ph;
      if (size === 'fit') {
        // 150 نقطة في البوصة تقريباً
        pw = iw * 72 / 150; ph = ih * 72 / 150;
      } else {
        [pw, ph] = SIZES[size];
        if (iw > ih) [pw, ph] = [ph, pw];
      }
      const aw = pw - 2 * margin, ah = ph - 2 * margin;
      const sc = Math.min(aw / iw, ah / ih);
      const dw = iw * sc, dh = ih * sc;
      const dx = (pw - dw) / 2, dy = (ph - dh) / 2;
      const f = v => v.toFixed(2);

      begin(pageObj(i));
      push(`<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${f(pw)} ${f(ph)}] ` +
        `/Resources << /XObject << /Im${i} ${imgObj(i)} 0 R >> /ProcSet [/PDF /ImageC] >> ` +
        `/Contents ${cntObj(i)} 0 R >>\nendobj\n`);

      const jpg = await canvasToJpeg(cv, quality);
      begin(imgObj(i));
      push(`<< /Type /XObject /Subtype /Image /Width ${iw} /Height ${ih} /ColorSpace /DeviceRGB ` +
        `/BitsPerComponent 8 /Filter /DCTDecode /Length ${jpg.length} >>\nstream\n`);
      push(jpg);
      push('\nendstream\nendobj\n');

      const content = `q ${f(dw)} 0 0 ${f(dh)} ${f(dx)} ${f(dy)} cm /Im${i} Do Q`;
      begin(cntObj(i));
      push(`<< /Length ${content.length} >>\nstream\n${content}\nendstream\nendobj\n`);

      if (opts.onProgress) opts.onProgress((i + 1) / n);
    }

    const xref = len;
    let x = `xref\n0 ${total + 1}\n0000000000 65535 f \n`;
    for (let id = 1; id <= total; id++) x += String(offsets[id]).padStart(10, '0') + ' 00000 n \n';
    push(x);
    push(`trailer\n<< /Size ${total + 1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`);
    return new Blob(chunks, { type: 'application/pdf' });
  }

  return { build };
})();

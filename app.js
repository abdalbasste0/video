'use strict';

// ---------- عناصر الواجهة ----------
const $ = (s) => document.querySelector(s);
const el = {
  home: $('#home'), editor: $('#editor'), pages: $('#pages'), empty: $('#empty'),
  camInput: $('#camInput'), galInput: $('#galInput'), exportBtn: $('#exportBtn'), clearAll: $('#clearAll'),
  edCancel: $('#edCancel'), edSave: $('#edSave'), edTitle: $('#edTitle'),
  cropStage: $('#cropStage'), cropWrap: $('#cropWrap'), cropCanvas: $('#cropCanvas'), cropSvg: $('#cropSvg'),
  loupe: $('#loupe'), filterStage: $('#filterStage'), previewCanvas: $('#previewCanvas'),
  cropTools: $('#cropTools'), filterTools: $('#filterTools'),
  autoBtn: $('#autoBtn'), fullBtn: $('#fullBtn'), rotL: $('#rotL'), rotR: $('#rotR'),
  exportDlg: $('#exportDlg'), fileName: $('#fileName'), pageSize: $('#pageSize'), quality: $('#quality'),
  doShare: $('#doShare'), busy: $('#busy'), busyText: $('#busyText'), toast: $('#toast'),
};

/** @type {{id:string, source:HTMLCanvasElement, corners:{x:number,y:number}[], filter:string, rotation:number, processed?:HTMLCanvasElement, thumb?:string}[]} */
let pages = [];
let editing = null; // { page, draft, isNew }

const uid = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
const nextFrame = () => new Promise(r => requestAnimationFrame(() => setTimeout(r, 0)));

function showBusy(text) { el.busyText.textContent = text || 'جارٍ المعالجة…'; el.busy.hidden = false; return nextFrame(); }
function hideBusy() { el.busy.hidden = true; }
let toastTimer;
function toast(msg) {
  el.toast.textContent = msg; el.toast.hidden = false;
  clearTimeout(toastTimer); toastTimer = setTimeout(() => (el.toast.hidden = true), 2600);
}

// ---------- التخزين المحلي (IndexedDB) لكي لا تضيع الصفحات ----------
const DB = (() => {
  let dbp;
  const open = () => dbp || (dbp = new Promise((res, rej) => {
    const r = indexedDB.open('pdf-scanner', 1);
    r.onupgradeneeded = () => r.result.createObjectStore('pages', { keyPath: 'id' });
    r.onsuccess = () => res(r.result);
    r.onerror = () => rej(r.error);
  }));
  const tx = async (mode, fn) => {
    const db = await open();
    return new Promise((res, rej) => {
      const t = db.transaction('pages', mode);
      const out = fn(t.objectStore('pages'));
      t.oncomplete = () => res(out && out.result);
      t.onerror = () => rej(t.error);
    });
  };
  return {
    all: () => tx('readonly', s => s.getAll()),
    put: (rec) => tx('readwrite', s => s.put(rec)),
    del: (id) => tx('readwrite', s => s.delete(id)),
    clear: () => tx('readwrite', s => s.clear()),
  };
})();

async function savePage(p, i) {
  try {
    if (!p.blob) p.blob = await new Promise(r => p.source.toBlob(r, 'image/jpeg', 0.92));
    await DB.put({ id: p.id, order: i, blob: p.blob, corners: p.corners, filter: p.filter, rotation: p.rotation });
  } catch (e) { console.warn('save failed', e); }
}
function saveOrder() { pages.forEach((p, i) => savePage(p, i)); }

async function restore() {
  try {
    const recs = (await DB.all()) || [];
    if (!recs.length) return;
    await showBusy('استعادة الصفحات السابقة…');
    recs.sort((a, b) => a.order - b.order);
    for (const r of recs) {
      const source = await Scanner.loadFile(r.blob);
      const p = { id: r.id, source, blob: r.blob, corners: r.corners, filter: r.filter, rotation: r.rotation };
      await renderPage(p);
      pages.push(p);
    }
    renderList();
  } catch (e) { console.warn('restore failed', e); }
  finally { hideBusy(); }
}

// ---------- إنشاء ومعالجة الصفحات ----------
async function renderPage(p) {
  p.processed = Scanner.process(p);
  const s = Math.min(1, 360 / Math.max(p.processed.width, p.processed.height));
  const t = Scanner.makeCanvas(p.processed.width * s, p.processed.height * s);
  t.getContext('2d').drawImage(p.processed, 0, 0, t.width, t.height);
  p.thumb = t.toDataURL('image/jpeg', 0.8);
}

async function addFiles(files, openEditor) {
  files = [...files].filter(f => f.type.startsWith('image/') || /\.(jpe?g|png|webp|heic|heif|gif|bmp)$/i.test(f.name));
  if (!files.length) return;
  if (openEditor && files.length === 1) {
    await showBusy('تحميل الصورة…');
    try {
      const source = await Scanner.loadFile(files[0]);
      const page = { id: uid(), source, corners: Scanner.detectCorners(source), filter: 'enhance', rotation: 0 };
      hideBusy();
      openEditorFor(page, true);
    } catch (e) { hideBusy(); toast('تعذّر فتح الصورة'); console.error(e); }
    return;
  }
  let i = 0;
  for (const f of files) {
    i++;
    await showBusy(`معالجة الصورة ${i} من ${files.length}…`);
    try {
      const source = await Scanner.loadFile(f);
      const p = { id: uid(), source, corners: Scanner.detectCorners(source), filter: 'enhance', rotation: 0 };
      await renderPage(p);
      pages.push(p);
      savePage(p, pages.length - 1);
    } catch (e) { console.error(e); toast(`تعذّر فتح ${f.name}`); }
  }
  hideBusy();
  renderList();
  if (files.length > 1) toast('اضغط على أي صفحة لتعديل القص أو الفلتر');
}

// ---------- قائمة الصفحات ----------
function renderList() {
  el.pages.innerHTML = '';
  pages.forEach((p, i) => {
    const li = document.createElement('li');
    li.className = 'page';
    li.innerHTML = `
      <div class="thumb" title="تعديل"><img alt="صفحة ${i + 1}" src="${p.thumb}"><span class="num">${i + 1}</span></div>
      <div class="row">
        <button class="icon" data-a="prev" title="تحريك للأمام" ${i === 0 ? 'disabled' : ''}>→</button>
        <button class="icon" data-a="edit" title="تعديل">✏️</button>
        <button class="icon" data-a="del" title="حذف">🗑️</button>
        <button class="icon" data-a="next" title="تحريك للخلف" ${i === pages.length - 1 ? 'disabled' : ''}>←</button>
      </div>`;
    li.querySelector('.thumb').onclick = () => openEditorFor(p, false);
    li.querySelector('.row').onclick = (e) => {
      const a = e.target.closest('button')?.dataset.a;
      if (!a) return;
      if (a === 'edit') openEditorFor(p, false);
      else if (a === 'del') {
        if (!confirm(`حذف الصفحة ${i + 1}؟`)) return;
        pages.splice(i, 1); DB.del(p.id); saveOrder(); renderList();
      } else if (a === 'prev' && i > 0) { [pages[i - 1], pages[i]] = [pages[i], pages[i - 1]]; saveOrder(); renderList(); }
      else if (a === 'next' && i < pages.length - 1) { [pages[i + 1], pages[i]] = [pages[i], pages[i + 1]]; saveOrder(); renderList(); }
    };
    el.pages.appendChild(li);
  });
  el.empty.hidden = pages.length > 0;
  el.exportBtn.disabled = pages.length === 0;
  el.clearAll.hidden = pages.length === 0;
  el.exportBtn.textContent = pages.length ? `⬇️ PDF (${pages.length})` : '⬇️ PDF';
}

// ---------- المحرر ----------
let previewSrc = null; // نسخة مصغّرة بعد تصحيح المنظور، لمعاينة سريعة للفلاتر
let previewKey = '';
let step = 'crop';

function show(screen) {
  el.home.classList.toggle('active', screen === 'home');
  el.editor.classList.toggle('active', screen === 'editor');
}

function openEditorFor(page, isNew) {
  editing = {
    page, isNew,
    draft: { corners: page.corners.map(c => ({ ...c })), filter: page.filter, rotation: page.rotation },
  };
  el.edTitle.textContent = isNew ? 'صفحة جديدة' : `تعديل الصفحة ${pages.indexOf(page) + 1}`;
  previewKey = '';
  // معاينة القص مصغّرة للسرعة
  const src = page.source;
  const s = Math.min(1, 1400 / Math.max(src.width, src.height));
  el.cropCanvas.width = Math.round(src.width * s);
  el.cropCanvas.height = Math.round(src.height * s);
  el.cropCanvas.getContext('2d').drawImage(src, 0, 0, el.cropCanvas.width, el.cropCanvas.height);
  el.cropSvg.setAttribute('viewBox', `0 0 ${src.width} ${src.height}`);
  el.cropSvg.setAttribute('preserveAspectRatio', 'none');
  show('editor');
  setStep('crop');
}

function fitInto(canvasLike, stage, w, h) {
  const aw = stage.clientWidth - 36, ah = stage.clientHeight - 36;
  const s = Math.min(aw / w, ah / h);
  canvasLike.style.width = Math.max(1, Math.floor(w * s)) + 'px';
  canvasLike.style.height = Math.max(1, Math.floor(h * s)) + 'px';
}

function layoutCrop() {
  if (!editing) return;
  const src = editing.page.source;
  fitInto(el.cropWrap, el.cropStage, src.width, src.height);
  el.cropCanvas.style.width = '100%';
  el.cropCanvas.style.height = '100%';
  drawQuad();
}

function drawQuad() {
  const src = editing.page.source;
  const c = editing.draft.corners;
  const rect = el.cropWrap.getBoundingClientRect();
  const k = rect.width ? src.width / rect.width : 1;
  const r = 11 * k, hit = 26 * k;
  const pts = c.map(p => `${p.x},${p.y}`).join(' ');
  let html = `<polygon class="quad" points="${pts}" vector-effect="non-scaling-stroke" />`;
  c.forEach((p, i) => {
    html += `<circle class="hit" data-i="${i}" cx="${p.x}" cy="${p.y}" r="${hit}" />`;
    html += `<circle class="handle" data-i="${i}" cx="${p.x}" cy="${p.y}" r="${r}" vector-effect="non-scaling-stroke" />`;
  });
  el.cropSvg.innerHTML = html;
}

function drawLoupe(pt) {
  const L = el.loupe, ctx = L.getContext('2d');
  const src = editing.page.source;
  const zoomSrc = 60 * (src.width / el.cropWrap.getBoundingClientRect().width) / 2.2;
  ctx.fillStyle = '#000';
  ctx.fillRect(0, 0, L.width, L.height);
  ctx.drawImage(src, pt.x - zoomSrc / 2, pt.y - zoomSrc / 2, zoomSrc, zoomSrc, 0, 0, L.width, L.height);
  ctx.strokeStyle = '#1f5eff'; ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(L.width / 2, 0); ctx.lineTo(L.width / 2, L.height);
  ctx.moveTo(0, L.height / 2); ctx.lineTo(L.width, L.height / 2);
  ctx.stroke();
}

// السحب لتحريك الزوايا
(() => {
  let active = -1, offset = null;
  const toSrc = (e) => {
    const rect = el.cropWrap.getBoundingClientRect();
    const src = editing.page.source;
    return {
      x: ((e.clientX - rect.left) / rect.width) * src.width,
      y: ((e.clientY - rect.top) / rect.height) * src.height,
    };
  };
  el.cropWrap.addEventListener('pointerdown', (e) => {
    if (!editing) return;
    const p = toSrc(e);
    const rect = el.cropWrap.getBoundingClientRect();
    const k = editing.page.source.width / rect.width;
    // أقرب زاوية ضمن مسافة اللمس
    let best = -1, bd = 44 * k;
    editing.draft.corners.forEach((c, i) => {
      const d = Math.hypot(c.x - p.x, c.y - p.y);
      if (d < bd) { bd = d; best = i; }
    });
    if (best < 0) return;
    active = best;
    const c = editing.draft.corners[best];
    offset = { x: c.x - p.x, y: c.y - p.y };
    el.cropWrap.setPointerCapture(e.pointerId);
    el.loupe.hidden = false;
    drawLoupe(c);
    e.preventDefault();
  });
  el.cropWrap.addEventListener('pointermove', (e) => {
    if (active < 0) return;
    const src = editing.page.source;
    const p = toSrc(e);
    const c = editing.draft.corners[active];
    c.x = Math.max(0, Math.min(src.width, p.x + offset.x));
    c.y = Math.max(0, Math.min(src.height, p.y + offset.y));
    drawQuad();
    drawLoupe(c);
  });
  const end = () => { active = -1; el.loupe.hidden = true; };
  el.cropWrap.addEventListener('pointerup', end);
  el.cropWrap.addEventListener('pointercancel', end);
})();

function setStep(s) {
  step = s;
  document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.step === s));
  el.cropStage.hidden = s !== 'crop';
  el.cropTools.hidden = s !== 'crop';
  el.filterStage.hidden = s !== 'filter';
  el.filterTools.hidden = s !== 'filter';
  if (s === 'crop') requestAnimationFrame(layoutCrop);
  else updatePreview();
}

async function updatePreview() {
  const d = editing.draft;
  const key = JSON.stringify(d.corners);
  if (key !== previewKey) {
    const src = editing.page.source;
    // تصحيح المنظور على نسخة مصغّرة للمعاينة السريعة
    const s = Math.min(1, 1100 / Math.max(src.width, src.height));
    let small = src;
    if (s < 1) {
      small = Scanner.makeCanvas(src.width * s, src.height * s);
      small.getContext('2d').drawImage(src, 0, 0, small.width, small.height);
    }
    const corners = d.corners.map(c => ({ x: c.x * (small.width / src.width), y: c.y * (small.height / src.height) }));
    previewSrc = Scanner.warp(small, corners);
    previewKey = key;
  }
  const out = Scanner.rotate(Scanner.applyFilter(previewSrc, d.filter), d.rotation);
  const pc = el.previewCanvas;
  pc.width = out.width; pc.height = out.height;
  pc.getContext('2d').drawImage(out, 0, 0);
  requestAnimationFrame(() => fitInto(pc, el.filterStage, out.width, out.height));
  document.querySelectorAll('[data-filter]').forEach(b => b.classList.toggle('active', b.dataset.filter === d.filter));
}

document.querySelectorAll('.tab').forEach(t => (t.onclick = () => setStep(t.dataset.step)));
document.querySelectorAll('[data-filter]').forEach(b => (b.onclick = () => { editing.draft.filter = b.dataset.filter; updatePreview(); }));
el.rotL.onclick = () => { editing.draft.rotation = (editing.draft.rotation + 270) % 360; updatePreview(); };
el.rotR.onclick = () => { editing.draft.rotation = (editing.draft.rotation + 90) % 360; updatePreview(); };
el.autoBtn.onclick = () => { editing.draft.corners = Scanner.detectCorners(editing.page.source); drawQuad(); toast('تم كشف الحواف'); };
el.fullBtn.onclick = () => { const s = editing.page.source; editing.draft.corners = Scanner.fullCorners(s.width, s.height); drawQuad(); };

el.edCancel.onclick = () => { editing = null; show('home'); };
el.edSave.onclick = async () => {
  const { page, draft, isNew } = editing;
  await showBusy('حفظ الصفحة…');
  try {
    Object.assign(page, { corners: draft.corners, filter: draft.filter, rotation: draft.rotation });
    await renderPage(page);
    if (isNew) pages.push(page);
    await savePage(page, pages.indexOf(page));
  } catch (e) { console.error(e); toast('حدث خطأ أثناء الحفظ'); }
  hideBusy();
  editing = null;
  renderList();
  show('home');
  if (isNew) toast('تمت إضافة الصفحة ✓');
};

window.addEventListener('resize', () => {
  if (!editing) return;
  if (step === 'crop') layoutCrop();
  else fitInto(el.previewCanvas, el.filterStage, el.previewCanvas.width, el.previewCanvas.height);
});

// ---------- الإدخال ----------
el.camInput.onchange = (e) => { addFiles(e.target.files, true); e.target.value = ''; };
el.galInput.onchange = (e) => { addFiles(e.target.files, e.target.files.length === 1); e.target.value = ''; };
el.clearAll.onclick = () => {
  if (!confirm('حذف جميع الصفحات؟')) return;
  pages = []; DB.clear(); renderList();
};

// سحب وإفلات على الحاسوب
document.addEventListener('dragover', (e) => e.preventDefault());
document.addEventListener('drop', (e) => { e.preventDefault(); if (!editing) addFiles(e.dataTransfer.files, false); });

// ---------- التصدير ----------
function defaultName() {
  const d = new Date(), z = (n) => String(n).padStart(2, '0');
  return `Scan_${d.getFullYear()}-${z(d.getMonth() + 1)}-${z(d.getDate())}_${z(d.getHours())}${z(d.getMinutes())}`;
}

el.exportBtn.onclick = () => {
  el.fileName.value = defaultName();
  el.doShare.hidden = !(navigator.canShare && navigator.canShare({ files: [new File([''], 'a.pdf', { type: 'application/pdf' })] }));
  el.exportDlg.showModal();
};

el.exportDlg.addEventListener('close', async () => {
  const action = el.exportDlg.returnValue;
  if (action !== 'download' && action !== 'share') return;
  let name = (el.fileName.value.trim() || defaultName()).replace(/[\\/:*?"<>|]+/g, '_');
  if (!/\.pdf$/i.test(name)) name += '.pdf';
  await showBusy('إنشاء ملف PDF…');
  try {
    for (const p of pages) if (!p.processed) await renderPage(p);
    const blob = await PdfWriter.build(pages.map(p => ({ canvas: p.processed })), {
      size: el.pageSize.value,
      quality: parseFloat(el.quality.value),
      onProgress: (f) => (el.busyText.textContent = `إنشاء ملف PDF… ${Math.round(f * 100)}%`),
    });
    hideBusy();
    const file = new File([blob], name, { type: 'application/pdf' });
    if (action === 'share') {
      try { await navigator.share({ files: [file], title: name }); return; }
      catch (e) { if (e.name === 'AbortError') return; }
    }
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = name;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 60000);
    toast(`تم إنشاء ${name} (${(blob.size / 1024 / 1024).toFixed(2)} م.ب)`);
  } catch (e) {
    hideBusy(); console.error(e); toast('تعذّر إنشاء ملف PDF');
  }
});

// ---------- البدء ----------
renderList();
restore();
if ('serviceWorker' in navigator && location.protocol !== 'file:') {
  navigator.serviceWorker.register('sw.js').catch(() => {});
}

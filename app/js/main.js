// واجهة التطبيق
import { Store, Settings } from './store.js';
import { BOTS, DIALECTS, STAGES, newProject, runPipeline, stopProject, isRunning } from './bots.js';
import { NICHES } from './demo.js';
import { hasClaude, hasVoice } from './ai.js';
import { uploadToYouTube, downloadBlob, testTelegram } from './publish.js';

const $ = (s, el = document) => el.querySelector(s);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const view = $('#view');
let current = 'factory';
const urls = new Map(); // blob url cache

function toast(msg) {
  const t = $('#toast'); t.textContent = msg; t.classList.add('show');
  clearTimeout(toast.t); toast.t = setTimeout(() => t.classList.remove('show'), 3200);
}

async function blobUrl(key) {
  if (!key) return '';
  if (urls.has(key)) return urls.get(key);
  const b = await Store.getBlob(key);
  if (!b) return '';
  const u = URL.createObjectURL(b); urls.set(key, u); return u;
}

const STATUS = { queued: 'في الانتظار', working: 'قيد الإنتاج', review: 'بانتظار موافقتك', approved: 'تمت الموافقة', published: 'منشور', rejected: 'مرفوض', error: 'خطأ', stopped: 'متوقف' };
const STAGE_LABEL = { research: 'البحث', script: 'السيناريو', art: 'الإخراج الفني', images: 'الصور', voice: 'التعليق', sound: 'الصوت', edit: 'المونتاج', seo: 'النشر/SEO', qa: 'فحص الجودة' };

// ---------- navigation ----------
$('#tabs').addEventListener('click', (e) => {
  const b = e.target.closest('button[data-view]'); if (!b) return;
  show(b.dataset.view);
});
function show(v) {
  current = v;
  document.querySelectorAll('#tabs button').forEach((b) => b.classList.toggle('active', b.dataset.view === v));
  render();
  window.scrollTo(0, 0);
}

let renderQueued = false;
function scheduleRender() {
  if (renderQueued) return; renderQueued = true;
  requestAnimationFrame(async () => { renderQueued = false; await render(true); });
}
window.addEventListener('project-updated', scheduleRender);

async function render(soft) {
  const projects = await Store.listProjects();
  $('#badgeReview').textContent = projects.filter((p) => p.status === 'review').length || '';
  $('#badgeLine').textContent = projects.filter((p) => ['working', 'queued'].includes(p.status)).length || '';
  // keep focus/typing intact on forms during background updates
  if (soft && ['factory', 'settings', 'review'].includes(current) && view.contains(document.activeElement) && /INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName)) {
    if (current === 'factory') updateBots(projects);
    return;
  }
  if (soft && current === 'review') return; // don't reset video playback while reviewing
  if (soft && current === 'factory') { updateBots(projects); updateStats(projects); return; }
  const fn = { factory: renderFactory, line: renderLine, review: renderReview, library: renderLibrary, settings: renderSettings }[current];
  await fn(projects);
}

// ---------- factory ----------
let form = { niche: 'horror', format: 'short', minutes: 5, dialect: Settings.get().defaultDialect || 'msa', topic: '', notes: '', count: 1 };

function activeProject(projects) {
  return projects.find((p) => p.status === 'working') || projects[0];
}

function botsHTML(p) {
  return BOTS.map((b) => `<div class="card bot ${p?.status === 'working' || p?.bots?.[b.id] === 'error' ? (p?.bots?.[b.id] || '') : ''}" data-bot="${b.id}">
      <i class="st"></i><div class="ic">${b.icon}</div><div><b>${b.name}</b><small>${b.job}</small></div></div>`).join('');
}
function updateBots(projects) {
  const p = activeProject(projects);
  const el = $('#bots'); if (el) el.innerHTML = botsHTML(p);
  const now = $('#nowLine'); if (now) now.innerHTML = nowLine(p);
}
function updateStats(projects) {
  const el = $('#stats'); if (el) el.innerHTML = statsHTML(projects);
}
function statsHTML(projects) {
  const c = (f) => projects.filter(f).length;
  return `<div class="card stat"><b>${c((p) => ['working', 'queued'].includes(p.status))}</b><small>قيد الإنتاج</small></div>
    <div class="card stat"><b>${c((p) => p.status === 'review')}</b><small>بانتظار موافقتك</small></div>
    <div class="card stat"><b>${c((p) => ['approved', 'published'].includes(p.status))}</b><small>جاهز/منشور</small></div>`;
}
function nowLine(p) {
  if (!p || p.status !== 'working') return '<span class="tag">الفريق في استراحة — ابدأ إنتاجًا جديدًا</span>';
  const last = p.log[p.log.length - 1];
  return `<span class="tag working">يعمل الآن على: ${esc(p.idea?.title || NICHES[p.brief.niche].label)} — ${STAGE_LABEL[p.stage] || ''}</span> <small style="color:var(--muted)">${esc(last?.msg || '')}</small>`;
}

async function renderFactory(projects) {
  const demo = !hasClaude();
  view.innerHTML = `
    <h1>🏭 مصنع إنتاج الفيديوهات</h1>
    <p class="sub">عشرة روبوتات تعمل كفريق واحد: من الفكرة إلى فيديو جاهز بالصوت والصورة والترجمة — ثم يُرسل لك لتوافق قبل النشر.</p>
    ${demo ? `<div class="notice">⚠️ الوضع التجريبي: بدون مفتاح Claude يستخدم الفريق قصصًا جاهزة. أضف المفاتيح من <a href="#" data-go="settings">الإعدادات</a> لإنتاج قصص جديدة كليًا بأعلى كفاءة.</div>` : ''}
    ${!hasVoice() ? `<div class="notice">🎙️ لا يوجد مفتاح ElevenLabs: ستخرج الفيديوهات بالترجمة والموسيقى بدون تعليق صوتي.</div>` : ''}
    <div class="grid stats" id="stats">${statsHTML(projects)}</div>
    <h2>فريق العمل</h2>
    <div id="nowLine" style="margin-bottom:10px">${nowLine(activeProject(projects))}</div>
    <div class="grid bots" id="bots">${botsHTML(activeProject(projects))}</div>

    <h2>🎬 أمر إنتاج جديد</h2>
    <div class="card">
      <label class="f">النيش</label>
      <div class="chips" id="niche">${Object.entries(NICHES).map(([k, v]) => `<button class="chip ${form.niche === k ? 'on' : ''}" data-v="${k}">${v.icon} ${v.label}</button>`).join('')}</div>
      <label class="f">الصيغة</label>
      <div class="chips" id="format">
        <button class="chip ${form.format === 'short' ? 'on' : ''}" data-v="short">📱 Short / Reels / TikTok (60ث، 9:16)</button>
        <button class="chip ${form.format === 'long' ? 'on' : ''}" data-v="long">🖥️ فيديو طويل يوتيوب (16:9)</button>
      </div>
      <div class="row">
        <div class="${form.format === 'long' ? '' : 'hidden'}" id="minutesBox"><label class="f">المدة (دقائق)</label><input type="number" id="minutes" min="2" max="15" value="${form.minutes}" /></div>
        <div><label class="f">اللغة / اللهجة</label><select id="dialect">${Object.entries(DIALECTS).map(([k, v]) => `<option value="${k}" ${form.dialect === k ? 'selected' : ''}>${v}</option>`).join('')}</select></div>
        <div><label class="f">عدد الفيديوهات</label><select id="count">${[1, 2, 3, 5, 10].map((n) => `<option ${form.count == n ? 'selected' : ''}>${n}</option>`).join('')}</select></div>
      </div>
      <label class="f">الفكرة <small>(اختياري — اتركها فارغة ليختار باحث الترندات أقوى فكرة)</small></label>
      <input type="text" id="topic" value="${esc(form.topic)}" placeholder="مثال: النداهة في الريف — أب وابنته على طريق زراعي ليلًا" />
      <label class="f">ملاحظات للفريق <small>(اختياري)</small></label>
      <textarea id="notes" placeholder="مثال: أسلوب ستيك مان، نهاية مفتوحة، بدون دماء…">${esc(form.notes)}</textarea>
      <button class="btn primary big" id="go">🚀 ابدأ الإنتاج</button>
    </div>`;

  $('#niche').onclick = (e) => { const b = e.target.closest('.chip'); if (!b) return; form.niche = b.dataset.v; renderFactory(projects); };
  $('#format').onclick = (e) => { const b = e.target.closest('.chip'); if (!b) return; form.format = b.dataset.v; renderFactory(projects); };
  ['minutes', 'dialect', 'count', 'topic', 'notes'].forEach((id) => { $('#' + id).oninput = (e) => (form[id] = e.target.value); });
  view.querySelectorAll('[data-go]').forEach((a) => (a.onclick = (e) => { e.preventDefault(); show(a.dataset.go); }));
  $('#go').onclick = startProduction;
}

async function startProduction() {
  if ('Notification' in window && Notification.permission === 'default') Notification.requestPermission().catch(() => {});
  const n = Number(form.count) || 1;
  for (let i = 0; i < n; i++) {
    const p = newProject({ niche: form.niche, format: form.format, minutes: Number(form.minutes) || 5, dialect: form.dialect, topic: n > 1 ? '' : form.topic, notes: form.notes });
    if (n > 1 && i === 0 && form.topic) p.brief.topic = form.topic;
    await Store.saveProject(p);
  }
  form.topic = '';
  toast(n > 1 ? `أُضيف ${n} أوامر إنتاج إلى الطابور` : 'بدأ الفريق العمل 🚀');
  pump();
  show('line');
}

// sequential production queue (one project at a time keeps quality and rate limits in check)
let pumping = false;
async function pump() {
  if (pumping) return; pumping = true;
  try {
    for (;;) {
      const projects = await Store.listProjects();
      const next = projects.filter((p) => p.status === 'queued').sort((a, b) => a.createdAt - b.createdAt)[0];
      if (!next) break;
      await runPipeline(next, { from: next.resumeFrom || 'research' });
    }
  } finally { pumping = false; }
}

// ---------- production line ----------
async function renderLine(projects) {
  const list = projects.filter((p) => ['working', 'queued', 'error', 'stopped'].includes(p.status));
  view.innerHTML = `<h1>⚙️ خط الإنتاج</h1><p class="sub">تابع كل روبوت وهو يعمل لحظة بلحظة. يمكنك الإيقاف أو الاستئناف من أي مرحلة.</p>
    ${list.length ? '' : '<div class="empty">لا يوجد إنتاج حاليًا. ابدأ من تبويب المصنع.</div>'}
    ${list.map((p) => `
      <div class="card proj">
        <div class="proj-h"><h3>${NICHES[p.brief.niche].icon} ${esc(p.idea?.title || 'فكرة قيد البحث…')}</h3><span class="tag ${p.status}">${STATUS[p.status]}</span></div>
        <small style="color:var(--muted)">${p.brief.format === 'short' ? 'Short' : 'طويل ' + p.brief.minutes + ' د'} · ${DIALECTS[p.brief.dialect]} · المرحلة: ${STAGE_LABEL[p.stage] || p.stage}${p.stage === 'edit' && p.renderProgress != null && p.status === 'working' ? ` (${Math.round(p.renderProgress * 100)}%)` : ''}</small>
        <div class="bar"><div style="width:${Math.round(((p.progress || 0) + (p.stage === 'edit' ? (p.renderProgress || 0) / STAGES.length : 0)) * 100)}%"></div></div>
        ${p.error ? `<div class="notice">${esc(p.error)}</div>` : ''}
        <div class="log">${p.log.slice(-60).reverse().map((l) => `<div class="${l.level}"><b>${BOTS.find((b) => b.id === l.bot)?.icon || ''} ${BOTS.find((b) => b.id === l.bot)?.name || ''}:</b> ${esc(l.msg)}</div>`).join('')}</div>
        <div class="actions">
          ${p.status === 'working' ? `<button class="btn small" data-stop="${p.id}">⏸️ إيقاف</button>` : ''}
          ${['error', 'stopped'].includes(p.status) ? `<button class="btn small primary" data-resume="${p.id}">▶️ استئناف من ${STAGE_LABEL[p.stage] || ''}</button>` : ''}
          ${p.status !== 'working' ? `<button class="btn small ghost" data-del="${p.id}">🗑️ حذف</button>` : ''}
        </div>
      </div>`).join('')}`;
  view.querySelectorAll('[data-stop]').forEach((b) => (b.onclick = () => stopProject(b.dataset.stop)));
  view.querySelectorAll('[data-resume]').forEach((b) => (b.onclick = async () => {
    const p = await Store.getProject(b.dataset.resume);
    p.status = 'queued'; p.resumeFrom = p.stage; await Store.saveProject(p); pump();
  }));
  view.querySelectorAll('[data-del]').forEach((b) => (b.onclick = async () => { if (confirm('حذف هذا المشروع؟')) await Store.deleteProject(b.dataset.del); }));
}

// ---------- review ----------
async function renderReview(projects) {
  const list = projects.filter((p) => p.status === 'review');
  view.innerHTML = `<h1>👁️ المراجعة والموافقة</h1><p class="sub">كل فيديو ينتظر قرارك هنا. لا شيء يُنشر قبل موافقتك.</p>
    ${list.length ? '' : '<div class="empty">لا توجد فيديوهات بانتظار المراجعة الآن.</div>'}<div id="rlist"></div>`;
  const box = $('#rlist');
  for (const p of list) {
    const [v, th] = await Promise.all([blobUrl(p.videoKey), blobUrl(p.thumbKey)]);
    const sc = p.critique?.scores || {};
    const el = document.createElement('div');
    el.className = 'card proj';
    el.innerHTML = `
      <div class="proj-h"><h3>${NICHES[p.brief.niche].icon} ${esc(p.script?.title)}</h3><span class="tag review">جودة ${p.qa?.score ?? '-'}% · سيناريو ${p.critique?.average?.toFixed(1) ?? '-'}/10</span></div>
      <div class="review" style="margin-top:10px">
        <div>
          <video src="${v}" controls playsinline poster="${th}"></video>
          <details><summary>الصورة المصغرة</summary><img class="thumb" src="${th}" alt="" /></details>
        </div>
        <div>
          <h3>اختر العنوان</h3>
          <div class="radio-titles">${(p.seo?.titles || []).map((t, i) => `<label><input type="radio" name="t-${p.id}" value="${esc(t)}" ${p.publish?.title === t ? 'checked' : ''}/> <span>${esc(t)}</span></label>`).join('')}</div>
          <label class="f">العنوان النهائي</label><input type="text" data-k="title" value="${esc(p.publish?.title)}" maxlength="100" />
          <label class="f">الوصف</label><textarea data-k="description" rows="5">${esc(p.publish?.description)}</textarea>
          <label class="f">الوسوم <small>(افصل بفاصلة)</small></label><input type="text" data-k="tags" value="${esc((p.publish?.tags || []).join(', '))}" />
          <p class="sub" style="margin-top:8px">📌 تعليق مثبت مقترح: ${esc(p.seo?.pinnedComment)}<br/>🕗 أفضل وقت للنشر: ${esc(p.seo?.bestPostTime)}</p>
          <details><summary>تقرير الجودة</summary>
            <div class="scores">${Object.entries({ hook: 'الخطّاف', tension: 'التوتر', clarity: 'الوضوح', twist: 'النهاية', pacing: 'الإيقاع', language: 'اللغة', originality: 'الأصالة', retention: 'الاحتفاظ' }).map(([k, l]) => `<div><b>${sc[k] ?? '-'}</b>${l}</div>`).join('')}</div>
            <ul class="checks">${(p.qa?.checks || []).map((c) => `<li>${c.ok ? '✅' : '⚠️'} ${esc(c.label)}</li>`).join('')}</ul>
            ${(p.critique?.notes || []).length ? `<small style="color:var(--muted)">ملاحظات الناقد: ${esc(p.critique.notes.join(' · '))}</small>` : ''}
          </details>
          <details><summary>السيناريو (${p.script?.scenes?.length} مشهد)</summary>
            ${(p.script?.scenes || []).map((s, i) => `<div class="scene"><b>${i + 1}.</b> ${esc(s.narration)}<br/><small>🎥 ${esc(s.camera)} — ${esc(s.visual)}</small></div>`).join('')}
            ${p.script?.riddle?.answer ? `<div class="scene">🧩 <b>الحل:</b> ${esc(p.script.riddle.answer)}</div>` : ''}
          </details>
          <div class="actions">
            <button class="btn ok" data-a="approve-yt">✅ موافقة ونشر على يوتيوب</button>
            <button class="btn ok" data-a="approve-dl">✅ موافقة وتنزيل</button>
          </div>
          <details><summary>✏️ طلب تعديل</summary>
            <textarea data-k="fb" placeholder="اكتب ملاحظتك للفريق: مثال: النهاية ضعيفة، اجعل الصوت أهدأ، غيّر صورة المشهد 3…"></textarea>
            <div class="row" style="margin-top:8px">
              <select data-k="from">
                <option value="script">أعد كتابة السيناريو (وكل ما بعده)</option>
                <option value="art">أعد الإخراج الفني والصور</option>
                <option value="images">أعد توليد الصور فقط</option>
                <option value="voice">أعد التعليق الصوتي</option>
                <option value="edit">أعد المونتاج فقط</option>
              </select>
              <button class="btn" data-a="revise">🔁 أرسل للفريق</button>
            </div>
          </details>
          <div class="actions"><button class="btn ghost small" data-a="reject">🗑️ رفض وحذف</button></div>
        </div>
      </div>`;
    box.appendChild(el);
    const get = (k) => el.querySelector(`[data-k=${k}]`);
    el.querySelectorAll(`input[name="t-${p.id}"]`).forEach((r) => (r.onchange = () => (get('title').value = r.value)));
    const collect = () => {
      p.publish = { title: get('title').value.trim(), description: get('description').value, tags: get('tags').value.split(',').map((x) => x.trim()).filter(Boolean) };
    };
    el.querySelector('[data-a=approve-dl]').onclick = async () => {
      collect(); p.status = 'approved'; p.approvedAt = Date.now();
      p.log.push({ t: Date.now(), bot: 'director', msg: 'وافق صاحب القناة على الفيديو ✅', level: 'info' });
      await Store.saveProject(p); await downloadPackage(p); toast('تمت الموافقة — بدأ التنزيل'); render();
    };
    el.querySelector('[data-a=approve-yt]').onclick = async (e) => {
      collect(); p.status = 'approved'; p.approvedAt = Date.now();
      await Store.saveProject(p);
      e.target.disabled = true; e.target.textContent = '⏳ جاري الرفع…';
      try {
        const r = await uploadToYouTube(p, { onProgress: (x) => (e.target.textContent = `⏳ ${Math.round(x * 100)}%`) });
        p.status = 'published'; p.youtube = r;
        p.log.push({ t: Date.now(), bot: 'publisher', msg: 'نُشر على يوتيوب: ' + r.url, level: 'info' });
        await Store.saveProject(p); toast('🎉 نُشر على يوتيوب'); render();
      } catch (err) {
        toast('تعذر النشر: ' + err.message + ' — تمت الموافقة ويمكنك التنزيل من المكتبة');
        render();
      }
    };
    el.querySelector('[data-a=revise]').onclick = async () => {
      const text = get('fb').value.trim();
      const from = get('from').value;
      if (text) p.feedback.push({ t: Date.now(), text, stage: from, used: false });
      p.status = 'queued'; p.resumeFrom = from;
      p.log.push({ t: Date.now(), bot: 'director', msg: `طلب صاحب القناة تعديلًا (${STAGE_LABEL[from]}): ${text || '—'}`, level: 'warn' });
      await Store.saveProject(p); toast('أُرسلت ملاحظتك للفريق 🔁'); pump(); show('line');
    };
    el.querySelector('[data-a=reject]').onclick = async () => { if (confirm('رفض وحذف الفيديو نهائيًا؟')) { await Store.deleteProject(p.id); render(); } };
  }
}

async function downloadPackage(p) {
  const v = await Store.getBlob(p.videoKey);
  const th = await Store.getBlob(p.thumbKey);
  const base = (p.publish?.title || p.script?.title || 'video').replace(/[\\/:*?"<>|]+/g, '').slice(0, 60);
  if (v) await downloadBlob(v, `${base}.${v.type.includes('mp4') ? 'mp4' : 'webm'}`);
  if (th) await downloadBlob(th, `${base}-thumbnail.jpg`);
  const txt = `العنوان:\n${p.publish.title}\n\nالوصف:\n${p.publish.description}\n\nالوسوم:\n${p.publish.tags.join(', ')}\n\nالتعليق المثبت:\n${p.seo?.pinnedComment || ''}\n`;
  await downloadBlob(new Blob([txt], { type: 'text/plain;charset=utf-8' }), `${base}-نشر.txt`);
}

// ---------- library ----------
async function renderLibrary(projects) {
  const list = projects.filter((p) => ['approved', 'published'].includes(p.status));
  view.innerHTML = `<h1>📚 المكتبة</h1><p class="sub">الفيديوهات التي وافقت عليها.</p>
    ${list.length ? '' : '<div class="empty">لا توجد فيديوهات معتمدة بعد.</div>'}
    <div class="grid lib" id="lib"></div>`;
  for (const p of list) {
    const th = await blobUrl(p.thumbKey);
    const el = document.createElement('div'); el.className = 'card';
    el.innerHTML = `<img src="${th}" alt="" /><h3 style="margin-top:8px">${esc(p.publish?.title)}</h3>
      <span class="tag ${p.status}">${STATUS[p.status]}</span>
      <div class="actions">${p.youtube ? `<a class="btn small" href="${p.youtube.url}" target="_blank" rel="noopener">▶️ يوتيوب</a>` : `<button class="btn small" data-yt>🚀 نشر على يوتيوب</button>`}
      <button class="btn small" data-dl>⬇️ تنزيل</button><button class="btn small ghost" data-del>🗑️</button></div>`;
    el.querySelector('[data-dl]').onclick = () => downloadPackage(p);
    el.querySelector('[data-del]').onclick = async () => { if (confirm('حذف؟')) await Store.deleteProject(p.id); };
    const yt = el.querySelector('[data-yt]');
    if (yt) yt.onclick = async () => {
      yt.disabled = true;
      try {
        const r = await uploadToYouTube(p, { onProgress: (x) => (yt.textContent = `⏳ ${Math.round(x * 100)}%`) });
        p.status = 'published'; p.youtube = r; await Store.saveProject(p); toast('🎉 نُشر على يوتيوب');
      } catch (e) { toast('تعذر النشر: ' + e.message); yt.disabled = false; yt.textContent = '🚀 نشر على يوتيوب'; }
    };
    $('#lib').appendChild(el);
  }
}

// ---------- settings ----------
async function renderSettings() {
  const s = Settings.get();
  const field = (k, label, type = 'text', hint = '') => `<label class="f">${label} ${hint ? `<small>${hint}</small>` : ''}</label><input type="${type}" data-s="${k}" value="${esc(s[k])}" autocomplete="off" />`;
  view.innerHTML = `<h1>🔑 الإعدادات</h1><p class="sub">المفاتيح تُحفظ على جهازك فقط وتُرسل مباشرة لمزود كل خدمة.</p>
    <div class="card">
      <h3>🧠 العقل (Claude) — للبحث والكتابة والنقد والإخراج والـSEO</h3>
      ${field('claudeKey', 'مفتاح Claude API', 'password', '(من console.anthropic.com)')}
      <label class="f">النموذج</label><select data-s="claudeModel">
        ${[['claude-opus-5-5', 'Claude Opus 5.5 (أعلى جودة — موصى به)'], ['claude-sonnet-5-5', 'Claude Sonnet 5.5 (أسرع وأرخص)'], ['claude-haiku-5-5', 'Claude Haiku 5.5 (الأرخص)']].map(([v, l]) => `<option value="${v}" ${s.claudeModel === v ? 'selected' : ''}>${l}</option>`).join('')}</select>
      <div class="row">
        <div>${field('qualityThreshold', 'حد جودة السيناريو (من 10)', 'number')}</div>
        <div>${field('maxRevisions', 'أقصى جولات إعادة كتابة', 'number')}</div>
      </div>
    </div>
    <div class="card" style="margin-top:12px">
      <h3>🖼️ الصور</h3>
      <label class="f">مزود الصور</label><select data-s="imageProvider">
        <option value="pollinations" ${s.imageProvider === 'pollinations' ? 'selected' : ''}>Pollinations (مجاني بدون مفتاح)</option>
        <option value="openai" ${s.imageProvider === 'openai' ? 'selected' : ''}>OpenAI gpt-image-1 (جودة أعلى، بمفتاح)</option>
        <option value="procedural" ${s.imageProvider === 'procedural' ? 'selected' : ''}>الرسام المحلي (بدون إنترنت)</option></select>
      ${field('openaiKey', 'مفتاح OpenAI', 'password', '(فقط إن اخترت OpenAI)')}
      <label class="f">دقة التصدير</label><select data-s="renderQuality">
        <option value="1080" ${s.renderQuality !== '720' ? 'selected' : ''}>1080p (أفضل جودة)</option>
        <option value="720" ${s.renderQuality === '720' ? 'selected' : ''}>720p (أسرع على الهواتف الضعيفة)</option></select>
    </div>
    <div class="card" style="margin-top:12px">
      <h3>🎙️ التعليق الصوتي (ElevenLabs)</h3>
      ${field('elevenKey', 'مفتاح ElevenLabs', 'password')}
      ${field('elevenVoice', 'Voice ID', 'text', '(من مكتبة الأصوات؛ اختر صوتًا عربيًا باللهجة المطلوبة)')}
      <label class="f">نموذج الصوت</label><select data-s="elevenModel">
        <option value="eleven_v3" ${s.elevenModel === 'eleven_v3' ? 'selected' : ''}>Eleven v3 (يفهم وسوم النبرة: همس/توتر — موصى به)</option>
        <option value="eleven_multilingual_v2" ${s.elevenModel === 'eleven_multilingual_v2' ? 'selected' : ''}>Multilingual v2</option></select>
    </div>
    <div class="card" style="margin-top:12px">
      <h3>📲 إرسال العمل لك للمراجعة (تيليجرام)</h3>
      <p class="sub">أنشئ بوتًا من @BotFather وضع التوكن، ثم أرسل له رسالة واحصل على chat id من @userinfobot. سيصلك كل فيديو جاهز على هاتفك.</p>
      ${field('telegramToken', 'Bot Token', 'password')}
      ${field('telegramChat', 'Chat ID')}
      <div class="actions"><button class="btn small" id="tg">إرسال رسالة تجربة</button></div>
    </div>
    <div class="card" style="margin-top:12px">
      <h3>▶️ النشر على يوتيوب (بعد موافقتك فقط)</h3>
      ${field('youtubeClientId', 'Google OAuth Client ID', 'text', '(نوع Web، وأضف رابط التطبيق في Authorized JavaScript origins)')}
      <label class="f">حالة الفيديو عند النشر</label><select data-s="youtubePrivacy">
        ${[['public', 'عام'], ['unlisted', 'غير مدرج'], ['private', 'خاص']].map(([v, l]) => `<option value="${v}" ${s.youtubePrivacy === v ? 'selected' : ''}>${l}</option>`).join('')}</select>
      ${field('channelName', 'اسم القناة (علامة مائية صغيرة)', 'text')}
      <label class="f">اللهجة الافتراضية</label><select data-s="defaultDialect">${Object.entries(DIALECTS).map(([k, v]) => `<option value="${k}" ${s.defaultDialect === k ? 'selected' : ''}>${v}</option>`).join('')}</select>
    </div>
    <button class="btn primary big" id="save">💾 حفظ الإعدادات</button>`;
  $('#save').onclick = () => {
    const patch = {};
    view.querySelectorAll('[data-s]').forEach((el) => (patch[el.dataset.s] = el.value.trim()));
    Settings.set(patch); form.dialect = patch.defaultDialect || form.dialect; toast('تم الحفظ ✅');
  };
  $('#tg').onclick = async () => {
    $('#save').click();
    try { await testTelegram(); toast('وصلت الرسالة؟ ✅'); } catch (e) { toast('فشل: ' + e.message); }
  };
}

// ---------- install (PWA) ----------
let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => { e.preventDefault(); deferredPrompt = e; $('#installBtn').classList.remove('hidden'); });
$('#installBtn').onclick = async () => {
  if (deferredPrompt) { deferredPrompt.prompt(); await deferredPrompt.userChoice; deferredPrompt = null; $('#installBtn').classList.add('hidden'); }
};
const isIOS = /iphone|ipad|ipod/i.test(navigator.userAgent) && !window.navigator.standalone;
if (isIOS) { const b = $('#installBtn'); b.classList.remove('hidden'); b.onclick = () => toast('على آيفون: اضغط زر المشاركة ثم "إضافة إلى الشاشة الرئيسية"'); }

if ('serviceWorker' in navigator && location.protocol !== 'file:') {
  navigator.serviceWorker.register('sw.js').catch(() => {});
}

// recover projects interrupted by closing the app
(async () => {
  for (const p of await Store.listProjects()) {
    if (p.status === 'working' && !isRunning(p.id)) {
      p.status = 'stopped'; p.error = 'أُغلق التطبيق أثناء الإنتاج — اضغط استئناف';
      await Store.saveProject(p);
    }
  }
  if ((await Store.listProjects()).some((p) => p.status === 'queued')) pump();
  render();
})();

window.__factory = { Store, runPipeline, newProject, pump }; // handy for debugging

import { WORKERS, WPS, countWords } from "./workers.js";
import { NICHES, DURATIONS, SCENE_SECONDS } from "./locked.js";
import { runStation, MODELS, getSample, getDownloads } from "./api.js";
import { W, H, buildTimeline, renderFrame, scheduleMusic, pickMime, MOOD_LABELS } from "./studio.js";
import { VOICES, IMAGE_MODELS, getMcp, mcpErrorText, generateImage, generateSpeech, narrationParts, putBlob, getBlob, clearBlobs, blobToImage, decodeAudio } from "./media.js";

const STORE_KEY = "stickfactory.project.v3";
const LAST = WORKERS.length;
const SETTINGS_KEY = "stickfactory.settings.v1";
const STATUS_AR = {
  idle: "في الانتظار", working: "شغال…", waiting: "محتاج قرارك", done: "خلص ✓", error: "فيه مشكلة", skipped: "متخطّى",
};
const KIND_AR = { input: "قرار", ai: "AI", local: "آلي" };

const $ = (sel) => document.querySelector(sel);
const esc = (t) => String(t ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

// ---------- persistence ----------
function load(key, fallback) {
  try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; }
}
function save(key, val) {
  try { localStorage.setItem(key, JSON.stringify(val)); } catch { /* storage unavailable */ }
}

let settings = load(SETTINGS_KEY, { apiKey: "", model: MODELS[0].id });
let s = load(STORE_KEY, null) || freshState();
let selected = 1;
let running = false;
let abort = null;
let liveNote = "";
let lastError = {};

function freshState() {
  return { status: Object.fromEntries(WORKERS.map((w) => [w.id, "idle"])), dialect: "fusha" };
}
function persist() { save(STORE_KEY, s); }
// A worker that was mid-run when the page closed goes back to idle.
for (const id in s.status) if (s.status[id] === "working") s.status[id] = "idle";

// ---------- AI bridge ----------
function ai(opts) {
  return runStation({
    apiKey: settings.apiKey,
    model: settings.model,
    signal: abort?.signal,
    onProgress: (n) => { liveNote = `بيكتب… ${n.toLocaleString("ar-EG")} حرف`; paintLive(); },
    ...opts,
  });
}

// ---------- engine ----------
function setStatus(id, st) { s.status[id] = st; persist(); paintStations(); }

function invalidateAfter(id) {
  for (const w of WORKERS) if (w.id > id) s.status[w.id] = "idle";
  persist();
}

async function runLine() {
  if (running) return;
  if (!(await canRun())) { openSettings(); return; }
  running = true; abort = new AbortController(); paintControls();
  try {
    for (const w of WORKERS) {
      const st = s.status[w.id];
      if (st === "done" || st === "skipped") continue;
      if (w.skip?.(s)) { setStatus(w.id, "skipped"); continue; }
      if (w.kind === "input" && !w.ready(s)) { setStatus(w.id, "waiting"); select(w.id); break; }
      if (st === "waiting" && w.needsChoice?.(s)) { select(w.id); break; }
      if (w.run) {
        select(w.id); setStatus(w.id, "working"); liveNote = ""; delete lastError[w.id]; paintBody();
        await w.run(s, ai, (note) => { liveNote = note; paintLive(); });
      }
      if (w.needsChoice?.(s)) { setStatus(w.id, "waiting"); select(w.id); break; }
      setStatus(w.id, "done");
      if (w.id === LAST) select(LAST);
    }
  } catch (err) {
    const w = WORKERS.find((x) => s.status[x.id] === "working");
    if (w) { lastError[w.id] = err.message; setStatus(w.id, "error"); select(w.id); }
    else toast(err.message);
  } finally {
    running = false; abort = null; liveNote = ""; paintControls(); paintBody();
  }
}

function stopLine() { abort?.abort(); }

function rerun(id) {
  if (running) return;
  const w = WORKERS.find((x) => x.id === id);
  if (w.kind === "input") {
    s.status[id] = "waiting";
    if (id === 8) { s.characterAr = null; s.charMode = null; s.charOptions = null; }
  } else {
    s.status[id] = "idle";
    if (id === 2) s.topic = null;
  }
  invalidateAfter(id); persist(); paintAll();
  if (w.kind !== "input") runLine();
}

function submit(id, mutate) {
  mutate(s);
  s.status[id] = "done";
  invalidateAfter(id); persist(); paintAll();
  runLine();
}

// ---------- painting ----------
function paintStations() {
  const ol = $("#stations");
  if (!ol.children.length) {
    const tpl = $("#worker-svg");
    for (const w of WORKERS) {
      const li = document.createElement("li");
      li.className = "station"; li.dataset.id = w.id; li.tabIndex = 0;
      li.innerHTML = `<span class="num">${w.id}</span><span class="kind">${KIND_AR[w.kind]}</span>`;
      li.append(tpl.content.cloneNode(true));
      li.insertAdjacentHTML("beforeend", `<div class="name">${esc(w.name)}</div><div class="role">${esc(w.role)}</div><div class="status"></div><div class="belt"></div>`);
      li.addEventListener("click", () => select(w.id));
      li.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); select(w.id); } });
      ol.append(li);
    }
  }
  let done = 0;
  for (const li of ol.children) {
    const id = +li.dataset.id; const st = s.status[id] || "idle";
    if (st === "done" || st === "skipped") done++;
    li.className = `station ${st}${id === selected ? " selected" : ""}`;
    li.querySelector(".status").textContent = STATUS_AR[st];
    li.setAttribute("aria-label", `العامل ${id}: ${WORKERS[id - 1].name} — ${STATUS_AR[st]}`);
  }
  $("#progress-bar").style.width = `${(done / LAST) * 100}%`;
  $("#progress-text").textContent = `${done} / ${LAST}`;
}

function paintControls() {
  $("#btn-run").hidden = running;
  $("#btn-stop").hidden = !running;
  const allDone = WORKERS.every((w) => ["done", "skipped"].includes(s.status[w.id]));
  $("#btn-run").textContent = allDone ? "✓ الباكدج جاهز" : Object.values(s.status).some((x) => x !== "idle") ? "▶ كمل" : "▶ شغّل المصنع";
  $("#btn-run").disabled = allDone;
  const w = WORKERS[selected - 1];
  const st = s.status[selected];
  $("#btn-rerun").hidden = running || !["done", "error", "waiting"].includes(st) || (st === "waiting" && w.kind === "input");
  $("#btn-rerun").textContent = w.kind === "input" ? "✎ غيّر القرار" : "↻ إعادة تشغيل العامل";
}

function select(id) { selected = id; paintAll(); }
function paintAll() { paintStations(); paintControls(); paintBody(); }

function paintLive() {
  const el = $("#live-note"); if (el) el.textContent = liveNote;
}

let renderSeq = 0; // bumps on every repaint so async binders can tell they are stale
function paintBody() {
  renderSeq++;
  copyBuffer = [];
  if (!exporting) stopPreview();
  const w = WORKERS[selected - 1];
  $("#cr-badge").textContent = w.id;
  $("#cr-title").textContent = w.name;
  $("#cr-role").textContent = `— ${w.role}`;
  const body = $("#cr-body");
  const st = s.status[w.id];
  let html = "";
  if (lastError[w.id] && st === "error") html += `<div class="error-box">${esc(lastError[w.id])}</div>`;
  if (st === "working") html += `<p class="live">العامل شغال دلوقتي… <span id="live-note">${esc(liveNote)}</span></p>`;
  html += VIEWS[w.id]?.(st) ?? "";
  body.innerHTML = html || `<p class="empty">العامل ده لسه مستني دوره على الخط.</p>`;
  bindBody(w.id);
  paintControls();
}

// ---------- views ----------
const promptCard = (title, text, idx) =>
  `<article class="prompt-card"><header><span class="t">${title}</span><button class="btn small" data-copy="${idx}">نسخ</button></header><pre>${esc(text)}</pre></article>`;
let copyBuffer = [];
const addCopy = (t) => (copyBuffer.push(t), copyBuffer.length - 1);

const VIEWS = {
  1: (st) => {
    if (st !== "waiting" && s.niche) return `<p>النيتش المختار:</p><p class="script">${esc(s.niche)}</p>`;
    return `<p>في أي نيتش هنشتغل النهارده؟ اختار واحد:</p>
      <div class="choices">${NICHES.map((n, i) => `<button class="choice" data-niche="${esc(n)}"><span class="n">${i + 1}</span>${esc(n)}</button>`).join("")}</div>
      <div class="inline"><input type="text" id="niche-custom" placeholder="أو اكتب نيتش من عندك" /><button class="btn primary" id="niche-go">اعتمد</button></div>`;
  },
  2: () => {
    if (!s.ideas?.length) return "";
    return `<p>${s.topic ? "الموضوع المختار: <strong>" + esc(s.topic) + "</strong>" : "اختار رقم من 1 لـ 15، أو اكتب موضوع مختلف."}</p>
      <div class="choices">${s.ideas.map((t, i) => `<button class="choice${t === s.topic ? " active" : ""}" data-topic="${esc(t)}"><span class="n">${i + 1}</span>${esc(t)}</button>`).join("")}</div>
      <div class="inline"><input type="text" id="topic-custom" placeholder="موضوع مختلف" /><button class="btn primary" id="topic-go">اعتمد</button></div>`;
  },
  3: (st) => {
    if (st !== "waiting" && s.durationSec) return `<div class="meta"><span class="chip">${esc(s.durationLabel)}</span><span class="chip">حوالي ${Math.round(s.durationSec * WPS)} كلمة</span><span class="chip">${s.dialect === "masri" ? "عامية مصرية" : "فصحى مبسطة"}</span><span class="chip">${s.style === "explain" ? "شرح ومعلومات" : "قصة ستيكمان بالفصول"}</span></div>`;
    return `<p>الفيديو ده هيكون مدته قد إيه؟</p>
      <div class="choices">${DURATIONS.map((d) => `<button class="choice" data-sec="${d.seconds}" data-label="${esc(d.label)}">${esc(d.label)} <small>— حوالي ${d.seconds * WPS} كلمة</small></button>`).join("")}</div>
      <label>أو مدة مخصصة بالثواني<div class="inline"><input type="text" inputmode="numeric" id="dur-custom" placeholder="مثلاً 90" /><button class="btn primary" id="dur-go">اعتمد</button></div></label>
      <label>لهجة السرد<select id="dialect"><option value="fusha">فصحى مبسطة لكل العرب</option><option value="masri"${s.dialect === "masri" ? " selected" : ""}>عامية مصرية</option></select></label>
      <label>أسلوب الفيديو<select id="style"><option value="story"${s.style !== "explain" ? " selected" : ""}>قصة ستيكمان مشوقة بالفصول — انت البطل (زي قنوات قصص ستيكمان)</option><option value="explain"${s.style === "explain" ? " selected" : ""}>فيديو شرح ومعلومات</option></select></label>`;
  },
  4: () => s.script ? `<div class="meta"><span class="chip">الهدف: ${s.targetWords} كلمة / ${esc(s.durationLabel)}</span><span class="chip">المسودة: ${countWords(s.script)} كلمة</span></div><div class="script">${esc(s.script)}</div>` : "",
  5: () => {
    if (!s.auditNote) return "";
    const ok = s.auditNote.startsWith("مطابق");
    return `<div class="meta"><span class="chip ${ok ? "ok" : "warn"}">${esc(s.auditNote)}</span></div>
      <p>الهدف: ${s.targetWords} كلمة / ${esc(s.durationLabel)}</p><div class="script">${esc(s.script)}</div><p class="muted">الفعلي: ${s.actualWords} كلمة</p>`;
  },
  6: (st) => {
    if (st !== "waiting" && s.sceneSec) return `<div class="meta"><span class="chip">${s.sceneSec} ثواني للمشهد</span><span class="chip">حوالي ${Math.round(s.sceneSec * WPS)} كلمة لكل بيت</span></div>`;
    return `<p>قبل ما أقسم السكريبت لمشاهد، حدد لي: المشهد الواحد (الكليب الواحد المتحرك) هتكون مدته كام ثانية؟</p>
      <div class="choices">${SCENE_SECONDS.map((x) => `<button class="choice" data-scene="${x.s}">${x.s} ثواني <small>— ${esc(x.hint)}</small></button>`).join("")}</div>
      <div class="inline"><input type="text" inputmode="numeric" id="scene-custom" placeholder="مدة بالثواني" /><button class="btn primary" id="scene-go">اعتمد</button></div>`;
  },
  7: () => {
    if (!s.beats?.length) return "";
    return `<p><strong>إجمالي المشاهد: ${s.beats.length} مشهد × ${s.sceneSec} ثانية = حوالي ${s.beats.length * s.sceneSec} ثانية</strong></p>
      <table><thead><tr><th>رقم المشهد</th><th>التوقيت (بداية)</th><th>كلمات السرد</th></tr></thead><tbody>
      ${s.beats.map((b) => `<tr><td class="num">${b.n}</td><td class="num">${b.start.toFixed(1)}ث</td><td>${esc(b.text)}</td></tr>`).join("")}</tbody></table>`;
  },
  8: (st) => {
    if (st === "done" || st === "skipped") {
      return s.charMode === "skip" ? `<p>تم التخطي — هيتم استخدام ستيك فيجرز عشوائية بدون شخصية رئيسية ثابتة.</p>` : `<p>الشخصية المعتمدة:</p><div class="script">${esc(s.characterAr)}</div>`;
    }
    if (st === "working") return "";
    if (s.charMode === "ai" && s.charOptions?.length) {
      return `<p>اختار شخصيتك، وعدّل أي تفاصيل في الخانة قبل الاعتماد:</p>
        <div class="choices">${s.charOptions.map((o, i) => `<button class="choice" data-char="${i}"><span class="n">${i + 1}</span><span><strong>${esc(o.name)}</strong><br>${esc(o.outfit)}<br><small>الإكسسوارات: ${esc(o.accessories)}<br>الفايب: ${esc(o.vibe)}<br>ليه مناسب: ${esc(o.why)}</small></span></button>`).join("")}</div>
        <label>الوصف النهائي<textarea id="char-text" placeholder="اختار خيار من فوق أو اكتب تعديلك"></textarea></label>
        <div class="row-end"><button class="btn primary" id="char-go">ثبّت الشخصية</button></div>`;
    }
    if (s.charMode === "custom") {
      return `<p>وصّف شكل شخصيتك الرئيسية. اذكر ستايل اللبس والألوان، الإكسسوارات، ستايل الشعر لو موجود، وأي تفاصيل بصرية تانية عايز تثبتها في كل صورة.</p>
        <textarea id="char-text"></textarea><div class="row-end"><button class="btn primary" id="char-go">ثبّت الشخصية</button></div>`;
    }
    return `<p>قبل ما أكتب برومتات الصور محتاج أثبّت شكل الشخصية الرئيسية عشان كل صورة في الفيديو تطلع متطابقة تماماً.</p>
      <div class="choices">
        <button class="choice" data-mode="ai"><span class="n">1</span><span>خلي الذكاء الاصطناعي يقترح 3 شخصيات</span></button>
        <button class="choice" data-mode="custom"><span class="n">2</span><span>اكتب شكل شخصيتك بنفسك</span></button>
        <button class="choice" data-mode="skip"><span class="n">3</span><span>تخطي — ستيك فيجرز عشوائية بدون شخصية ثابتة</span></button>
      </div>`;
  },
  9: (st) => {
    if (st === "skipped") return `<p>متخطّى لأنك اخترت بدون شخصية رئيسية ثابتة.</p>`;
    if (!s.charSheet) return "";
    return `<p>تم تثبيت الشخصية. ${esc(s.characterSummary)}. وده برومت الكراكتر شيت بتاعها بالإنجليزية — ولّده كصورة مرجعية واستخدمها مع كل الصور الجاية:</p>
      ${promptCard("Character Sheet Prompt", s.charSheet, addCopy(s.charSheet))}`;
  },
  10: () => {
    if (!s.plans?.length) return "";
    return s.plans.map((p, i) => p ? `<article class="prompt-card"><header><span class="t">مشهد ${i + 1} — ${esc(s.beats[i]?.text)}</span></header><pre>${esc(`SCENE: ${p.environment}\n\nCHARACTERS: ${p.characters}\n\nACTION: ${p.action}`)}</pre></article>` : "").join("");
  },
  11: () => {
    if (!s.imagePrompts?.length) return "";
    const all = s.imagePrompts.map((p, i) => `${i + 1}.\n${p}`).join("\n\n");
    return `<div class="row-end" style="margin-top:0"><button class="btn small" data-copy="${addCopy(all)}">نسخ كل البرومتات</button></div>` +
      s.imagePrompts.map((p, i) => promptCard(`${i + 1}. مشهد ${i + 1} — ${esc(s.beats[i]?.text)}`, p, addCopy(p))).join("");
  },
  12: () => {
    if (!s.qa) return "";
    return `<div class="meta"><span class="chip">${s.qa.checked} برومت اتفحص</span><span class="chip">تغطية السكريبت ${s.qa.coverage}%</span><span class="chip ${s.qa.issues.length ? "warn" : "ok"}">${s.qa.issues.length ? s.qa.issues.length + " ملاحظة" : "كل حاجة ثابتة ✓"}</span></div>
      <p>اتأكدت إن كل برومت فيه: وصف المشهد، التصميم المثبت للشخصيات حرفياً${s.characterEn ? "، وصف البطل منفصل تحت MAIN CHARACTER" : ""}، الستايل المثبت حرفياً، وجملة الختام.</p>
      ${s.qa.issues.length ? `<ul>${s.qa.issues.map((x) => `<li>${esc(x)}</li>`).join("")}</ul><p class="muted">أعد تشغيل "مخرج المشاهد" لو فيه خطط ناقصة.</p>` : ""}`;
  },
  13: () => s.animPrompt ? `<p>ده البرومت الموحد — استخدمه مع كل صورة لتحويلها لمشهد متحرك مدته ${s.sceneSec} ثواني:</p>${promptCard("Master Animation Prompt", s.animPrompt, addCopy(s.animPrompt))}` : "",
  14: () => s.thumbs?.length ? s.thumbs.map((t, i) => `<p><strong>${i + 1}.</strong> ${esc(t.ideaAr)}</p>${promptCard(`Thumbnail ${i + 1}`, t.prompt, addCopy(t.prompt))}`).join("") : "",
  15: () => {
    if (!s.motion?.specs?.length) return "";
    const o = s.motion.outfit;
    return `<p>جهزت حركة ${s.motion.specs.length} مشهد. لبس البطل في الأنيميشن: قميص <span class="chip" style="background:${esc(o.shirt)};color:#fff">${esc(o.shirt)}</span> بنطلون <span class="chip" style="background:${esc(o.pants)};color:#fff">${esc(o.pants)}</span></p>
      <table><thead><tr><th>#</th><th>المكان</th><th>الشخصيات</th><th>الإكسسوارات</th></tr></thead><tbody>
      ${s.motion.specs.map((sc, i) => sc ? `<tr><td class="num">${i + 1}</td><td>${esc(sc.bg)} · ${esc(sc.light)}</td><td>${sc.characters.map((c) => `${c.main ? "البطل" : "شخصية"}: ${esc(c.action)} / ${esc(c.emotion)}`).join("<br>")}</td><td>${sc.props.map((p) => esc(p.type)).join("، ")}</td></tr>` : `<tr><td class="num">${i + 1}</td><td colspan="3">ناقص</td></tr>`).join("")}</tbody></table>`;
  },
  16: (st) => {
    const n = s.beats?.length || 0;
    const have = (s.imageKeys || []).length;
    const models = IMAGE_MODELS.map((m) => `<option value="${m.id}"${(s.imageModel || IMAGE_MODELS[0].id) === m.id ? " selected" : ""}>${m.label}</option>`).join("");
    return `<p>كل مشهد محتاج صورة. عندك طريقتين، وتقدر تخلطهم:</p>
      <ol class="note" style="margin:0 0 10px;padding-inline-start:18px">
        <li><strong>تلقائي:</strong> المصنع يولّد الصور بموديل Google Nano Banana (نفس موديلات Google Flow) عن طريق حسابك في ElevenLabs.</li>
        <li><strong>يدوي من Google Flow:</strong> انسخ برومت المشهد، ولّده في <a href="https://labs.google/fx/tools/flow" target="_blank" rel="noopener">Google Flow</a>، ونزّل الصورة وارفعها هنا.</li>
      </ol>
      <p class="note">أي مشهد من غير صورة هيترسم تلقائياً بالستيك مان المتحرك بتاع المصنع.</p>
      <div class="meta"><span class="chip ${have === n ? "ok" : ""}" id="img-count">${have} / ${n} صورة جاهزة</span></div>
      <div class="inline" style="flex-wrap:wrap">
        <select id="img-model" style="flex:1;min-width:200px">${models}</select>
        <button class="btn primary" id="img-gen-all">🎨 ولّد الصور الناقصة</button>
        <button class="btn" id="img-stop" hidden>■ وقف</button>
      </div>
      <p class="note" id="img-status"></p>
      <div class="scene-grid">${(s.beats || []).map((bt, i) => `
        <article class="scene-card" data-n="${bt.n}">
          <div class="thumb" id="thumb-${bt.n}"><span>${bt.n}</span></div>
          <p class="t">${esc(bt.text)}</p>
          <div class="acts">
            <button class="btn small" data-copy="${addCopy(s.imagePrompts?.[i] || "")}">نسخ البرومت</button>
            <label class="btn small upl">رفع صورة<input type="file" accept="image/*" data-upload="${bt.n}" hidden /></label>
            <button class="btn small" data-gen="${bt.n}">توليد</button>
          </div>
          <p class="note err" id="err-${bt.n}"></p>
        </article>`).join("")}</div>
      <div class="row-end"><button class="btn primary" id="images-go">${st === "done" ? "حدّث وكمّل" : "اعتمد الصور وكمّل للصوت"}</button></div>`;
  },
  17: (st) => {
    const moods = Object.entries(MOOD_LABELS).map(([k, v]) => `<option value="${k}"${(s.music || "mystery") === k ? " selected" : ""}>${v}</option>`).join("");
    const voices = VOICES.map((v) => `<option value="${v.id}"${(s.voiceId || VOICES[0].id) === v.id ? " selected" : ""}>${v.label}</option>`).join("");
    const parts = s.beats ? narrationParts(s.beats) : [];
    const ready = voiceState();
    return `<div class="meta"><span class="chip ${ready.ok ? "ok" : ""}" id="voice-chip">${esc(ready.label)}</span></div>
      <h3 style="font-size:1rem;margin:6px 0">التعليق الصوتي بـ ElevenLabs</h3>
      <div class="inline" style="flex-wrap:wrap"><select id="voice-id" style="flex:1;min-width:220px">${voices}</select>
        <button class="btn" id="voice-preview">▶ اسمع عيّنة</button>
        <button class="btn primary" id="voice-gen">🎙 ولّد التعليق (${parts.length} جزء)</button></div>
      <p class="note">بيقرأ السكريبت بموديل ElevenLabs Multilingual v2 على ${parts.length} جزء، وكل جزء مدته بتظبط توقيت مشاهده بالظبط. السكريبت ${(s.script || "").length.toLocaleString("ar-EG")} حرف — اتأكد إن رصيد ElevenLabs يكفي.</p>
      <p class="note" id="voice-status"></p>
      <h3 style="font-size:1rem;margin:14px 0 6px">أو ارفع تسجيل جاهز</h3>
      <input type="file" id="voice-file" accept="audio/*" />
      <h3 style="font-size:1rem;margin:14px 0 6px">الموسيقى والترجمة</h3>
      <label>الموسيقى الخلفية<select id="music">${moods}</select></label>
      <label style="display:flex;gap:8px;align-items:center;font-weight:600"><input type="checkbox" id="captions" ${s.captions === false ? "" : "checked"} /> ترجمة عربية متحركة (كلمة بكلمة)</label>
      <div class="row-end"><button class="btn ghost" id="audio-none">كمّل من غير تعليق</button><button class="btn primary" id="audio-go">اعتمد وكمّل للمونتاج</button></div>`;
  },
  18: () => {
    if (!s.videoReady || !s.motion) return "";
    const mime = pickMime();
    return `<div class="stage-wrap"><canvas id="stage" width="${W}" height="${H}"></canvas></div>
      <input type="range" class="seek" id="seek" min="0" max="1000" value="0" aria-label="مكان التشغيل" />
      <div class="player">
        <button class="btn" id="play">▶ معاينة</button>
        <button class="btn primary" id="export" ${mime === null ? "disabled" : ""}>🎬 صدّر الفيديو النهائي</button>
        <span class="time" id="time">0:00 / 0:00</span>
      </div>
      <div class="export-bar" id="export-bar" hidden><div></div></div>
      <p class="note" id="stage-info"></p>
      <p class="note" id="export-note">${mime === null ? "المتصفح ده مابيدعمش تسجيل الفيديو. جرّب Chrome." : `التصدير بيتسجل في وقت حقيقي (فيديو دقيقة = دقيقة تسجيل). خلّي الصفحة مفتوحة والشاشة منورة لحد ما يخلص. الصيغة: ${mime.startsWith("video/mp4") ? "MP4" : "WebM"}.`}</p>`;
  },
  19: () => s.packageMd ? `<p>الإنجن خلص. الباكدج الكامل جاهز: السكريبت، جدول المشاهد، الكراكتر شيت، ${s.imagePrompts.length} برومت صورة، برومت الأنيميشن الماستر، و3 ثمبنيل. والفيديو النهائي تصدّره من عند العامل 18 (المونتير).</p>
      <div class="row-end" style="justify-content:flex-start"><button class="btn primary" id="dl-md">⬇ تحميل الباكدج (.md)</button><button class="btn" data-copy="${addCopy(s.packageMd)}">نسخ الكل</button><button class="btn ghost" id="new-project">مشروع جديد</button></div>` : "",
};

// ---------- body bindings ----------
function bindBody(id) {
  const body = $("#cr-body");
  body.querySelectorAll("[data-copy]").forEach((b) => b.addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(copyBuffer[+b.dataset.copy]); toast("اتنسخ"); } catch { toast("النسخ مش متاح في المتصفح ده"); }
  }));
  const on = (sel, fn) => body.querySelector(sel)?.addEventListener("click", fn);
  const val = (sel) => body.querySelector(sel)?.value.trim();

  if (id === 1) {
    body.querySelectorAll("[data-niche]").forEach((b) => b.addEventListener("click", () => submit(1, (x) => { x.niche = b.dataset.niche; x.ideas = null; x.topic = null; })));
    on("#niche-go", () => { const v = val("#niche-custom"); if (v) submit(1, (x) => { x.niche = v; x.ideas = null; x.topic = null; }); });
  }
  if (id === 2) {
    const pick = (t) => submit(2, (x) => { x.topic = t; });
    body.querySelectorAll("[data-topic]").forEach((b) => b.addEventListener("click", () => pick(b.dataset.topic)));
    on("#topic-go", () => { const v = val("#topic-custom"); if (v) pick(v); });
  }
  if (id === 3) {
    const pick = (sec, label) => submit(3, (x) => { x.durationSec = sec; x.durationLabel = label; x.dialect = val("#dialect") || "fusha"; x.style = val("#style") || "story"; });
    body.querySelectorAll("[data-sec]").forEach((b) => b.addEventListener("click", () => pick(+b.dataset.sec, b.dataset.label)));
    on("#dur-go", () => { const n = parseInt(val("#dur-custom"), 10); if (n >= 10 && n <= 1800) pick(n, `${n} ثانية`); else toast("اكتب مدة بين 10 و1800 ثانية"); });
  }
  if (id === 6) {
    body.querySelectorAll("[data-scene]").forEach((b) => b.addEventListener("click", () => submit(6, (x) => { x.sceneSec = +b.dataset.scene; })));
    on("#scene-go", () => { const n = parseInt(val("#scene-custom"), 10); if (n >= 2 && n <= 20) submit(6, (x) => { x.sceneSec = n; }); else toast("اكتب مدة بين 2 و20 ثانية"); });
  }
  if (id === 8) {
    body.querySelectorAll("[data-mode]").forEach((b) => b.addEventListener("click", () => chooseCharMode(b.dataset.mode)));
    body.querySelectorAll("[data-char]").forEach((b) => b.addEventListener("click", () => {
      const o = s.charOptions[+b.dataset.char];
      body.querySelectorAll("[data-char]").forEach((x) => x.classList.toggle("active", x === b));
      body.querySelector("#char-text").value = `${o.name}\nاللبس: ${o.outfit}\nالإكسسوارات: ${o.accessories}\nالفايب: ${o.vibe}`;
    }));
    on("#char-go", () => { const v = val("#char-text"); if (v) submit(8, (x) => { x.characterAr = v; }); else toast("اختار أو اكتب وصف الشخصية"); });
  }
  if (id === 16) bindImages(body);
  if (id === 17) bindAudio(body);
  if (id === 18) setupStage(body);
  if (id === 19) {
    on("#dl-md", async () => {
      const filename = `stickman-${Date.now()}.md`;
      const downloads = await getDownloads();
      if (downloads) {
        try { await downloads.save({ filename, data: s.packageMd }); }
        catch (e) { if (e?.code !== "declined") toast("التحميل مش متاح هنا — استخدم نسخ الكل"); }
        return;
      }
      const blob = new Blob([s.packageMd], { type: "text/markdown;charset=utf-8" });
      const a = Object.assign(document.createElement("a"), { href: URL.createObjectURL(blob), download: filename });
      a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 2000);
    });
    on("#new-project", resetProject);
  }
}

async function chooseCharMode(mode) {
  if (mode === "skip") {
    submit(8, (x) => { x.charMode = "skip"; x.characterAr = null; x.characterEn = null; x.charSheet = null; x.characterSummary = null; });
    return;
  }
  s.charMode = mode; s.characterEn = null; s.charSheet = null; persist();
  if (mode === "custom") { paintBody(); return; }
  if (!(await canRun())) { openSettings(); return; }
  running = true; abort = new AbortController(); setStatus(8, "working"); paintAll();
  try {
    await WORKERS[7].suggest(s, ai);
    setStatus(8, "waiting");
  } catch (err) {
    lastError[8] = err.message; s.charMode = null; setStatus(8, "error");
  } finally {
    running = false; abort = null; paintAll();
  }
}


// ---------- media (workers 16–18) ----------
// Images and narration live in IndexedDB (blobs) + memory (decoded), so a reload keeps them.
const images = new Map();   // beat n -> ImageBitmap/HTMLImageElement
let voiceParts = null;      // [{from, to, buffer}] from ElevenLabs
let voiceUpload = null;     // {name, buffer}
let preview = null;         // {raf, actx, stops}
let exporting = false;
let mediaAbort = null;

async function loadMedia() {
  for (const n of s.imageKeys || []) {
    if (images.has(n)) continue;
    const blob = await getBlob(`img-${n}`);
    if (blob) { try { images.set(n, await blobToImage(blob)); } catch { /* broken file */ } }
  }
  if (s.voiceMode === "eleven" && !voiceParts && s.voiceParts?.length) {
    const parts = [];
    for (const p of s.voiceParts) {
      const blob = await getBlob(`voice-${p.from}`);
      if (!blob) { parts.length = 0; break; }
      parts.push({ ...p, buffer: await decodeAudio(blob) });
    }
    if (parts.length) voiceParts = parts;
  }
  if (s.voiceMode === "upload" && !voiceUpload) {
    const blob = await getBlob("voice-upload");
    if (blob) voiceUpload = { name: s.voiceName || "voice", buffer: await decodeAudio(blob) };
  }
}

function voiceState() {
  if (s.voiceMode === "eleven" && s.voiceParts?.length) return { ok: true, label: `✓ تعليق ElevenLabs جاهز (${s.voiceParts.length} جزء، ${fmt(s.voiceParts.reduce((a, p) => a + p.dur, 0))})` };
  if (s.voiceMode === "upload" && s.voiceName) return { ok: true, label: `✓ تسجيل مرفوع: ${s.voiceName}` };
  return { ok: false, label: "لسه مفيش تعليق صوتي" };
}

async function saveImage(n, blob) {
  await putBlob(`img-${n}`, blob);
  images.set(n, await blobToImage(blob));
  s.imageKeys = [...new Set([...(s.imageKeys || []), n])].sort((a, b) => a - b);
  persist();
}

function paintThumb(body, n) {
  const el = body.querySelector(`#thumb-${n}`); if (!el) return;
  const img = images.get(n);
  if (!img) return;
  const c = document.createElement("canvas"); c.width = 320; c.height = 180;
  const g = c.getContext("2d"); const k = Math.max(320 / img.width, 180 / img.height);
  g.drawImage(img, (320 - img.width * k) / 2, (180 - img.height * k) / 2, img.width * k, img.height * k);
  el.replaceChildren(c);
  const cnt = body.querySelector("#img-count");
  if (cnt) cnt.textContent = `${(s.imageKeys || []).length} / ${s.beats.length} صورة جاهزة`;
}

async function genOneImage(body, n) {
  const i = s.beats.findIndex((b) => b.n === n);
  const err = body.querySelector(`#err-${n}`);
  if (err) err.textContent = "بيتولّد…";
  try {
    const { blob } = await generateImage(s.imagePrompts[i], s.imageModel || IMAGE_MODELS[0].id, {
      signal: mediaAbort?.signal, onStatus: (sec) => { if (err) err.textContent = `بيتولّد… ${sec}ث`; },
    });
    await saveImage(n, blob); if (err) err.textContent = ""; paintThumb(body, n);
    return true;
  } catch (e) {
    if (err) {
      if (e?.code === "fetch_blocked") err.innerHTML = `الصورة اتولدت بس المتصفح منع تحميلها. <a href="${esc(e.url)}" target="_blank" rel="noopener">افتحها</a> واحفظها وارفعها هنا.`;
      else err.textContent = mcpErrorText(e);
    }
    return e;
  }
}

async function bindImages(body) {
  const seq = renderSeq;
  await loadMedia();
  if (seq !== renderSeq) return;
  for (const n of s.imageKeys || []) paintThumb(body, n);
  const status = body.querySelector("#img-status");
  const mcp = await getMcp();
  if (seq !== renderSeq) return;
  if (!mcp) { body.querySelector("#img-gen-all").disabled = true; body.querySelectorAll("[data-gen]").forEach((b) => (b.disabled = true)); status.textContent = "التوليد التلقائي بيشتغل لما تفتح الصفحة من claude.ai ومتوصل بـ ElevenLabs. تقدر ترفع الصور يدوي."; }
  body.querySelector("#img-model").addEventListener("change", (e) => { s.imageModel = e.target.value; persist(); });
  body.querySelectorAll("[data-upload]").forEach((inp) => inp.addEventListener("change", async () => {
    const f = inp.files?.[0]; if (!f) return; const n = +inp.dataset.upload;
    try { await saveImage(n, f); paintThumb(body, n); body.querySelector(`#err-${n}`).textContent = ""; } catch { body.querySelector(`#err-${n}`).textContent = "مقدرتش أقرا الصورة دي."; }
  }));
  body.querySelectorAll("[data-gen]").forEach((b) => b.addEventListener("click", async () => {
    b.disabled = true; mediaAbort ??= new AbortController(); await genOneImage(body, +b.dataset.gen); b.disabled = false;
  }));
  const stopBtn = body.querySelector("#img-stop"), allBtn = body.querySelector("#img-gen-all");
  stopBtn.addEventListener("click", () => mediaAbort?.abort());
  allBtn.addEventListener("click", async () => {
    const missing = s.beats.map((b) => b.n).filter((n) => !images.has(n));
    if (!missing.length) { status.textContent = "كل المشاهد عندها صور ✓"; return; }
    mediaAbort = new AbortController(); allBtn.disabled = true; stopBtn.hidden = false;
    let ok = 0, fails = 0;
    for (const [k, n] of missing.entries()) {
      if (mediaAbort.signal.aborted) break;
      status.textContent = `بولّد صورة المشهد ${n} (${k + 1} من ${missing.length})…`;
      const r = await genOneImage(body, n);
      if (r === true) ok++; else { fails++; if (r?.code && !["tool_error", "fetch_blocked"].includes(r.code)) break; }
    }
    status.textContent = `خلصت: ${ok} صورة جديدة${fails ? `، و${fails} فشلت — اضغط "توليد" على المشهد أو ارفع صورته` : ""}.`;
    allBtn.disabled = false; stopBtn.hidden = true; mediaAbort = null;
  });
  body.querySelector("#images-go").addEventListener("click", () => submit(16, (x) => { x.imagesSet = true; }));
}

async function bindAudio(body) {
  const seq = renderSeq;
  await loadMedia();
  if (seq !== renderSeq) return;
  const status = body.querySelector("#voice-status"), chip = body.querySelector("#voice-chip");
  const refreshChip = () => { const v = voiceState(); chip.textContent = v.label; chip.classList.toggle("ok", v.ok); };
  const mcp = await getMcp();
  if (seq !== renderSeq) return;
  if (!mcp) { body.querySelector("#voice-gen").disabled = true; body.querySelector("#voice-preview").disabled = true; status.textContent = "التعليق بـ ElevenLabs بيشتغل لما تفتح الصفحة من claude.ai ومتوصل بـ ElevenLabs. تقدر ترفع تسجيل جاهز."; }
  body.querySelector("#voice-id").addEventListener("change", (e) => { s.voiceId = e.target.value; persist(); });
  body.querySelector("#voice-preview").addEventListener("click", async (e) => {
    const b = e.currentTarget; b.disabled = true; status.textContent = "بجهّز عيّنة…";
    try {
      const sample = s.beats.slice(0, 2).map((x) => x.text.replace(/^#+\s*/, "")).join(" ").slice(0, 220);
      const { blob } = await generateSpeech(sample, s.voiceId || VOICES[0].id, {});
      new Audio(URL.createObjectURL(blob)).play(); status.textContent = "";
    } catch (err) { status.textContent = err?.code === "fetch_blocked" ? "العيّنة اتولدت بس المتصفح منع تشغيلها." : mcpErrorText(err); }
    b.disabled = false;
  });
  body.querySelector("#voice-gen").addEventListener("click", async (e) => {
    const b = e.currentTarget; b.disabled = true;
    const parts = narrationParts(s.beats);
    const done = [];
    try {
      for (const [k, p] of parts.entries()) {
        status.textContent = `بسجّل الجزء ${k + 1} من ${parts.length}…`;
        const { blob } = await generateSpeech(p.text, s.voiceId || VOICES[0].id, { onStatus: (sec) => (status.textContent = `بسجّل الجزء ${k + 1} من ${parts.length}… ${sec}ث`) });
        const buffer = await decodeAudio(blob);
        await putBlob(`voice-${p.from}`, blob);
        done.push({ from: p.from, to: p.to, dur: buffer.duration, buffer });
      }
      voiceParts = done; voiceUpload = null;
      s.voiceMode = "eleven"; s.voiceParts = done.map(({ from, to, dur }) => ({ from, to, dur })); persist();
      status.textContent = "التعليق جاهز ✓";
    } catch (err) {
      status.textContent = (err?.code === "fetch_blocked" ? "الصوت اتولد بس المتصفح منع تحميله. افتح ElevenLabs ونزّل الملفات وارفعهم كتسجيل واحد." : mcpErrorText(err)) + (done.length ? ` (اتسجل ${done.length} من ${parts.length} — اضغط تاني يكمّل من الأول)` : "");
    }
    refreshChip(); b.disabled = false;
  });
  body.querySelector("#voice-file").addEventListener("change", async (e) => {
    const f = e.target.files?.[0]; if (!f) return;
    status.textContent = "بقرأ الملف…";
    try {
      const buffer = await decodeAudio(f);
      await putBlob("voice-upload", f);
      voiceUpload = { name: f.name, buffer }; voiceParts = null;
      s.voiceMode = "upload"; s.voiceName = f.name; persist();
      status.textContent = `✓ ${f.name} — ${fmt(buffer.duration)}`;
    } catch { status.textContent = "مقدرتش أقرا الملف ده. جرّب MP3 أو M4A أو WAV."; }
    refreshChip();
  });
  const finish = (mode) => submit(17, (x) => {
    if (mode === "none") { x.voiceMode = "none"; voiceParts = null; voiceUpload = null; }
    x.audioSet = true; x.music = body.querySelector("#music").value || "none"; x.captions = body.querySelector("#captions").checked;
  });
  body.querySelector("#audio-go").addEventListener("click", () => {
    if (!voiceState().ok) { toast("لسه مفيش تعليق — ولّده أو ارفعه، أو اضغط كمّل من غير تعليق"); return; }
    finish("keep");
  });
  body.querySelector("#audio-none").addEventListener("click", () => finish("none"));
}

function timeline() {
  if (s.voiceMode === "eleven" && voiceParts) {
    const anchors = voiceParts.map((p) => ({ from: p.from, to: p.to, dur: p.dur + 0.25 }));
    return buildTimeline(s.beats, s.motion.specs, WPS, null, anchors);
  }
  return buildTimeline(s.beats, s.motion.specs, WPS, s.voiceMode === "upload" ? voiceUpload?.buffer.duration : null);
}
const fmt = (sec) => `${Math.floor(sec / 60)}:${String(Math.floor(sec % 60)).padStart(2, "0")}`;

function stopPreview() {
  if (!preview) return;
  cancelAnimationFrame(preview.raf);
  preview.stops.forEach((f) => { try { f(); } catch { /* already stopped */ } });
  preview.actx?.close();
  preview = null;
}

/** Schedule narration + music from `from` seconds. Returns {at, stops}. */
function startAudio(actx, dest, tl, from) {
  const at = actx.currentTime + 0.2;
  const stops = [];
  const play = (buffer, when, offset) => {
    const src = actx.createBufferSource(); src.buffer = buffer; src.connect(dest);
    src.start(at + Math.max(0, when - from), Math.max(0, offset)); stops.push(() => src.stop());
  };
  if (s.voiceMode === "eleven" && voiceParts) {
    for (const p of voiceParts) {
      const first = tl.items.find((it) => it.n === p.from); if (!first) continue;
      const start = first.start;
      if (start + p.dur < from) continue;
      play(p.buffer, start, from > start ? from - start : 0);
    }
  } else if (s.voiceMode === "upload" && voiceUpload) {
    play(voiceUpload.buffer, 0, from);
  }
  stops.push(scheduleMusic(actx, dest, s.music || "none", at, Math.max(0.5, tl.total - from), s.voiceMode === "none" ? 0.16 : 0.07));
  return { at, stops };
}

async function setupStage(body) {
  const canvas = body.querySelector("#stage"); if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const seq = renderSeq;
  try { await document.fonts.load("800 44px Cairo"); } catch { /* fallback font */ }
  await loadMedia();
  if (seq !== renderSeq) return;
  const tl = timeline();
  const info = body.querySelector("#stage-info");
  const withImg = s.beats.filter((b) => images.has(b.n)).length;
  info.textContent = `${tl.items.length} مشهد — ${withImg} بصور AI متحركة بالكاميرا، و${tl.items.length - withImg} مرسوم بالستيك مان. ` +
    (s.voiceMode === "eleven" ? (voiceParts ? "التعليق: ElevenLabs." : "⚠ ملفات التعليق مش موجودة — ارجع للعامل 17.") : s.voiceMode === "upload" ? (voiceUpload ? `التعليق: ${s.voiceName}.` : "⚠ ارفع التسجيل تاني من العامل 17.") : "من غير تعليق.");
  const seek = body.querySelector("#seek"), time = body.querySelector("#time"), play = body.querySelector("#play");
  const opts = { captions: s.captions !== false, images };
  let pos = 0;
  const draw = (T) => {
    renderFrame(ctx, tl, T, s.motion.outfit, opts);
    seek.value = Math.round((T / tl.total) * 1000);
    time.textContent = `${fmt(T)} / ${fmt(tl.total)}`;
  };
  draw(0.7);

  seek.addEventListener("input", () => { stopPreview(); play.textContent = "▶ معاينة"; pos = (seek.value / 1000) * tl.total; draw(pos); });
  play.addEventListener("click", () => {
    if (preview) { stopPreview(); play.textContent = "▶ معاينة"; return; }
    if (pos >= tl.total - 0.05) pos = 0;
    const actx = new (window.AudioContext || window.webkitAudioContext)();
    const { at, stops } = startAudio(actx, actx.destination, tl, pos);
    const from = pos;
    preview = { actx, stops, raf: 0 };
    play.textContent = "⏸ إيقاف";
    const tick = () => {
      const T = from + Math.max(0, actx.currentTime - at);
      pos = Math.min(T, tl.total); draw(pos);
      if (T >= tl.total) { stopPreview(); play.textContent = "▶ معاينة"; return; }
      preview.raf = requestAnimationFrame(tick);
    };
    preview.raf = requestAnimationFrame(tick);
  });
  body.querySelector("#export").addEventListener("click", () => exportVideo(body, canvas, ctx, tl, opts));
}

async function exportVideo(body, canvas, ctx, tl, opts) {
  if (exporting) return;
  stopPreview();
  const mime = pickMime();
  const btn = body.querySelector("#export"), note = body.querySelector("#export-note"), bar = body.querySelector("#export-bar");
  exporting = true; btn.disabled = true; body.querySelector("#play").disabled = true; bar.hidden = false;
  const actx = new (window.AudioContext || window.webkitAudioContext)();
  const dest = actx.createMediaStreamDestination();
  const stream = new MediaStream([...canvas.captureStream(30).getVideoTracks(), ...dest.stream.getAudioTracks()]);
  const rec = new MediaRecorder(stream, mime ? { mimeType: mime, videoBitsPerSecond: 6_000_000 } : undefined);
  const chunks = [];
  rec.ondataavailable = (e) => e.data.size && chunks.push(e.data);
  const stopped = new Promise((r) => (rec.onstop = r));
  renderFrame(ctx, tl, 0, s.motion.outfit, opts);
  rec.start(1000);
  const { at, stops } = startAudio(actx, dest, tl, 0);
  await new Promise((resolve) => {
    const tick = () => {
      const T = Math.max(0, actx.currentTime - at);
      renderFrame(ctx, tl, Math.min(T, tl.total), s.motion.outfit, opts);
      bar.firstElementChild.style.width = `${Math.min(100, (T / tl.total) * 100)}%`;
      note.textContent = `بسجّل الفيديو… ${fmt(T)} من ${fmt(tl.total)} — خلّي الصفحة مفتوحة`;
      if (T >= tl.total + 0.3) return resolve();
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  });
  rec.stop(); await stopped; stops.forEach((f) => { try { f(); } catch { /* done */ } }); actx.close();
  const type = (mime || "video/webm").split(";")[0];
  const blob = new Blob(chunks, { type });
  const filename = `stickman-video-${Date.now()}.${type === "video/mp4" ? "mp4" : "webm"}`;
  note.textContent = `الفيديو جاهز (${(blob.size / 1048576).toFixed(1)} ميجا).`;
  exporting = false; btn.disabled = false; body.querySelector("#play").disabled = false;
  const downloads = await getDownloads();
  if (downloads) {
    try { await downloads.save({ filename, data: blob }); note.textContent += " اتحفظ ✓"; }
    catch (e) { if (e?.code !== "declined") note.textContent += " مقدرتش أحفظه هنا."; }
  } else {
    const a = Object.assign(document.createElement("a"), { href: URL.createObjectURL(blob), download: filename });
    a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 5000);
  }
}
// ---------- chrome ----------
function toast(msg) {
  const t = Object.assign(document.createElement("div"), { className: "toast", textContent: msg, role: "status" });
  document.body.append(t); setTimeout(() => t.remove(), 2200);
}

// Inside claude.ai the factory runs on the viewer's Claude account; elsewhere it needs an API key.
async function canRun() { return !!(await getSample()) || !!settings.apiKey; }

async function openSettings() {
  const inClaude = !!(await getSample());
  $("#key-fields").hidden = inClaude;
  $("#claude-note").hidden = !inClaude;
  $("#api-key").value = settings.apiKey;
  $("#model").value = settings.model;
  $("#settings").showModal();
}

function resetProject() {
  if (running) return;
  const btn = $("#btn-reset");
  if (!btn.dataset.armed) {
    btn.dataset.armed = "1"; btn.textContent = "⚠ اضغط تاني للتأكيد";
    setTimeout(() => { delete btn.dataset.armed; btn.textContent = "↺ مشروع جديد"; }, 3000);
    toast("اضغط \"مشروع جديد\" تاني عشان تمسح المشروع الحالي");
    return;
  }
  delete btn.dataset.armed; btn.textContent = "↺ مشروع جديد";
  s = freshState(); lastError = {}; persist();
  images.clear(); voiceParts = null; voiceUpload = null; clearBlobs();
  select(1);
}

$("#model").innerHTML = MODELS.map((m) => `<option value="${m.id}">${m.label}</option>`).join("");
$("#settings").addEventListener("close", () => {
  if ($("#settings").returnValue !== "save") return;
  settings = { apiKey: $("#api-key").value.trim(), model: $("#model").value };
  save(SETTINGS_KEY, settings);
  toast("اتحفظت الإعدادات");
});
$("#btn-settings").addEventListener("click", openSettings);
$("#btn-run").addEventListener("click", runLine);
$("#btn-stop").addEventListener("click", stopLine);
$("#btn-rerun").addEventListener("click", () => rerun(selected));
$("#btn-reset").addEventListener("click", resetProject);

// Start on the first station that needs attention.
const firstOpen = WORKERS.find((w) => !["done", "skipped"].includes(s.status[w.id]));
select(firstOpen ? firstOpen.id : LAST);
canRun().then((ok) => { if (!ok) openSettings(); });

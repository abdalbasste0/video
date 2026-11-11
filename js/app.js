import { WORKERS, WPS, countWords } from "./workers.js";
import { NICHES, DURATIONS, SCENE_SECONDS } from "./locked.js";
import { runStation, MODELS, getSample, getDownloads } from "./api.js";
import { W, H, buildTimeline, renderFrame, scheduleMusic, pickMime, MOOD_LABELS } from "./studio.js";

const STORE_KEY = "stickfactory.project.v2";
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

function paintBody() {
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
    if (st !== "waiting" && s.durationSec) return `<div class="meta"><span class="chip">${esc(s.durationLabel)}</span><span class="chip">حوالي ${Math.round(s.durationSec * WPS)} كلمة</span><span class="chip">${s.dialect === "masri" ? "عامية مصرية" : "فصحى مبسطة"}</span></div>`;
    return `<p>الفيديو ده هيكون مدته قد إيه؟</p>
      <div class="choices">${DURATIONS.map((d) => `<button class="choice" data-sec="${d.seconds}" data-label="${esc(d.label)}">${esc(d.label)} <small>— حوالي ${d.seconds * WPS} كلمة</small></button>`).join("")}</div>
      <label>أو مدة مخصصة بالثواني<div class="inline"><input type="text" inputmode="numeric" id="dur-custom" placeholder="مثلاً 90" /><button class="btn primary" id="dur-go">اعتمد</button></div></label>
      <label>لهجة السرد<select id="dialect"><option value="fusha">فصحى مبسطة لكل العرب</option><option value="masri"${s.dialect === "masri" ? " selected" : ""}>عامية مصرية</option></select></label>`;
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
    const moods = Object.entries(MOOD_LABELS).map(([k, v]) => `<option value="${k}"${(s.music || "calm") === k ? " selected" : ""}>${v}</option>`).join("");
    const done = st !== "waiting" && s.audioSet;
    return `${done ? `<div class="meta"><span class="chip">${voice ? "التعليق: " + esc(voice.name) : s.voiceName ? "⚠ ارفع ملف التعليق تاني (" + esc(s.voiceName) + ")" : "من غير تعليق صوتي"}</span><span class="chip">الموسيقى: ${esc(MOOD_LABELS[s.music || "none"])}</span><span class="chip">الترجمة: ${s.captions === false ? "مقفولة" : "شغالة"}</span></div>` : ""}
      <p>التعليق الصوتي: سجّل السكريبت بصوتك (مثلاً بتطبيق تسجيل الصوت في الموبايل) أو من أي موقع تعليق صوتي، وارفع الملف هنا. المونتير هيظبط مدة كل مشهد على طول التسجيل.</p>
      <label>ملف التعليق (اختياري)<input type="file" id="voice-file" accept="audio/*" /></label>
      <p class="note" id="voice-info">${voice ? `✓ ${esc(voice.name)} — ${voice.buffer.duration.toFixed(1)} ثانية` : "لو مارفعتش ملف، الفيديو هيطلع بالترجمة والموسيقى بس."}</p>
      <label>الموسيقى الخلفية<select id="music">${moods}</select></label>
      <label style="display:flex;gap:8px;align-items:center;font-weight:600"><input type="checkbox" id="captions" ${s.captions === false ? "" : "checked"} /> ترجمة عربية على الفيديو</label>
      <div class="row-end"><button class="btn primary" id="audio-go">اعتمد وكمّل للمونتاج</button></div>`;
  },
  17: () => {
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
      <p class="note" id="export-note">${mime === null ? "المتصفح ده مابيدعمش تسجيل الفيديو. جرّب Chrome." : `التصدير بيتسجل في وقت حقيقي (فيديو دقيقة = دقيقة تسجيل). خلّي الصفحة مفتوحة وقدامك لحد ما يخلص. الصيغة: ${mime.startsWith("video/mp4") ? "MP4" : "WebM"}.`}</p>
      ${s.voiceName && !voice ? `<p class="error-box">ملف التعليق مش متحمّل بعد إعادة فتح الصفحة. ارجع للعامل 16 وارفعه تاني لو عايزه في الفيديو.</p>` : ""}`;
  },
  18: () => s.packageMd ? `<p>الإنجن خلص. الباكدج الكامل جاهز: السكريبت، جدول المشاهد، الكراكتر شيت، ${s.imagePrompts.length} برومت صورة، برومت الأنيميشن الماستر، و3 ثمبنيل. والفيديو النهائي تصدّره من عند العامل 17 (المونتير).</p>
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
    const pick = (sec, label) => submit(3, (x) => { x.durationSec = sec; x.durationLabel = label; x.dialect = val("#dialect") || "fusha"; });
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
  if (id === 16) {
    body.querySelector("#voice-file")?.addEventListener("change", async (e) => {
      const file = e.target.files?.[0]; if (!file) return;
      const info = body.querySelector("#voice-info"); info.textContent = "بقرأ الملف…";
      try {
        const actx = new (window.AudioContext || window.webkitAudioContext)();
        const buffer = await actx.decodeAudioData(await file.arrayBuffer());
        actx.close();
        voice = { name: file.name, buffer };
        info.textContent = `✓ ${file.name} — ${buffer.duration.toFixed(1)} ثانية`;
      } catch { voice = null; info.textContent = "مقدرتش أقرا الملف ده. جرّب MP3 أو M4A أو WAV."; }
    });
    on("#audio-go", () => submit(16, (x) => {
      x.audioSet = true; x.voiceName = voice?.name || null;
      x.music = val("#music") || "none"; x.captions = body.querySelector("#captions").checked;
    }));
  }
  if (id === 17) setupStage(body);
  if (id === 18) {
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


// ---------- studio (worker 17) ----------
let voice = null;          // {name, buffer} — kept in memory only
let preview = null;        // {raf, actx, stopMusic, src}
let exporting = false;

function timeline() {
  return buildTimeline(s.beats, s.motion.specs, WPS, voice?.buffer.duration || null);
}
const fmt = (sec) => `${Math.floor(sec / 60)}:${String(Math.floor(sec % 60)).padStart(2, "0")}`;

function stopPreview() {
  if (!preview) return;
  cancelAnimationFrame(preview.raf);
  preview.stopMusic?.(); try { preview.src?.stop(); } catch { /* not started */ }
  preview.actx?.close();
  preview = null;
}

function startAudio(actx, dest, from, total) {
  const at = actx.currentTime + 0.15;
  let src = null;
  if (voice) {
    src = actx.createBufferSource(); src.buffer = voice.buffer; src.connect(dest);
    src.start(at, Math.min(from, voice.buffer.duration));
  }
  const stopMusic = scheduleMusic(actx, dest, s.music || "none", at, Math.max(0.5, total - from));
  return { at, src, stopMusic };
}

async function setupStage(body) {
  const canvas = body.querySelector("#stage"); if (!canvas) return;
  const ctx = canvas.getContext("2d");
  try { await document.fonts.load("800 44px Cairo"); } catch { /* fallback font */ }
  const tl = timeline();
  const seek = body.querySelector("#seek"), time = body.querySelector("#time"), play = body.querySelector("#play");
  const opts = { captions: s.captions !== false };
  let pos = 0;
  const draw = (T) => {
    renderFrame(ctx, tl, T, s.motion.outfit, opts);
    seek.value = Math.round((T / tl.total) * 1000);
    time.textContent = `${fmt(T)} / ${fmt(tl.total)}`;
  };
  draw(0);

  seek.addEventListener("input", () => { stopPreview(); play.textContent = "▶ معاينة"; pos = (seek.value / 1000) * tl.total; draw(pos); });
  play.addEventListener("click", () => {
    if (preview) { stopPreview(); play.textContent = "▶ معاينة"; return; }
    if (pos >= tl.total - 0.05) pos = 0;
    const actx = new (window.AudioContext || window.webkitAudioContext)();
    const { at, src, stopMusic } = startAudio(actx, actx.destination, pos, tl.total);
    const from = pos;
    preview = { actx, src, stopMusic, raf: 0 };
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
  const rec = new MediaRecorder(stream, mime ? { mimeType: mime, videoBitsPerSecond: 5_000_000 } : undefined);
  const chunks = [];
  rec.ondataavailable = (e) => e.data.size && chunks.push(e.data);
  const stopped = new Promise((r) => (rec.onstop = r));
  renderFrame(ctx, tl, 0, s.motion.outfit, opts);
  rec.start(1000);
  const { at, stopMusic } = startAudio(actx, dest, 0, tl.total);
  // keep the canvas painting even if the screen is idle
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
  rec.stop(); await stopped; stopMusic(); actx.close();
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
  s = freshState(); lastError = {}; persist(); select(1);
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

// Media for the final video: ElevenLabs (through the viewer's claude.ai connector) for the
// Arabic voice-over and for images made with Google's Nano Banana models, plus manual uploads
// (e.g. images made in Google Flow), all kept in the browser's IndexedDB so a reload keeps them.

export const SERVER = "ElevenLabs";

export const VOICES = [
  { id: "6cFz1T5FQxQS8Xk88qQi", label: "أحمد — فصحى وثائقي عميق (رجالي)" },
  { id: "BrKeRgI6Ivb2zWjD6qte", label: "جليل — راوي فصحى دافي (رجالي)" },
  { id: "zkCGJHfZ7LHDgElbSPyO", label: "عادل — فصحى هادي وعميق (رجالي)" },
  { id: "fdAuK2EvQlttApnrJPMx", label: "حسن — فصحى واضح (رجالي)" },
  { id: "s7VusoUfleDWGRQNqsF6", label: "عرين — فصحى رخيم (نسائي)" },
  { id: "LBWTcQo7Ie6Rzp2s8Xff", label: "آلان — راوي قصص أردني (رجالي)" },
  { id: "jpmzWsrGMTnSHjVCQIrU", label: "ميمو — راوي مصري دافي (رجالي)" },
  { id: "K8FOFikqnvN14gWsgd9R", label: "صوت مصري وثائقي (رجالي)" },
  { id: "uj9BxaPZUGD5nukc6KG1", label: "ويل حلمي — مصري هادي (رجالي)" },
];

export const IMAGE_MODELS = [
  { id: "gemini-3.1-flash-image", label: "Google Nano Banana 2 (سريع وممتاز)" },
  { id: "gemini-3-pro-image", label: "Google Nano Banana Pro (أعلى جودة وأبطأ)" },
  { id: "gemini-nano-banana-2.1", label: "Google Nano Banana 2.1" },
  { id: "gemini-3.1-flash-lite-image", label: "Google Nano Banana 2 Lite (الأرخص)" },
];

// ---------- IndexedDB blob store ----------
let dbp = null;
function db() {
  dbp ??= new Promise((res, rej) => {
    const r = indexedDB.open("stickfactory-media", 1);
    r.onupgradeneeded = () => r.result.createObjectStore("blobs");
    r.onsuccess = () => res(r.result);
    r.onerror = () => rej(r.error);
  });
  return dbp;
}
async function tx(mode, fn) {
  const d = await db();
  return new Promise((res, rej) => {
    const t = d.transaction("blobs", mode); const st = t.objectStore("blobs");
    const out = fn(st);
    t.oncomplete = () => res(out?.result ?? out); t.onerror = () => rej(t.error);
  });
}
export const putBlob = (key, blob) => tx("readwrite", (s) => s.put(blob, key)).catch(() => null);
export const getBlob = (key) => tx("readonly", (s) => s.get(key)).catch(() => null);
export const delBlob = (key) => tx("readwrite", (s) => s.delete(key)).catch(() => null);
export async function clearBlobs() { try { await tx("readwrite", (s) => s.clear()); } catch { /* storage unavailable */ } }

// ---------- connector ----------
let mcpP = null;
export function getMcp() {
  mcpP ??= window.claude?.use ? window.claude.use("mcp").catch(() => null) : Promise.resolve(null);
  return mcpP;
}

export function mcpErrorText(e) {
  switch (e?.code) {
    case "server_not_connected": return "ElevenLabs مش متوصل بحسابك. ضيفه من claude.ai ← Settings ← Connectors.";
    case "needs_reauth": return "لازم تعيد توصيل ElevenLabs من claude.ai ← Settings ← Connectors.";
    case "not_in_manifest": case "approval_required": return "لازم توافق إن الصفحة تستخدم ElevenLabs (اضغط سماح لما تطلب).";
    case "selection_required": return "عندك أكتر من اتصال ElevenLabs — اختار واحد من الرسالة اللي ظهرت.";
    case "blocked_by_policy": return "إعدادات حسابك مانعة استخدام ElevenLabs هنا.";
    case "server_unavailable": return "ElevenLabs مش بيرد دلوقتي. جرّب كمان شوية.";
    case "tool_error": {
      const m = String(e.message || "");
      if (/busy|Free generations/i.test(m)) return "التوليد المجاني في ElevenLabs مشغول دلوقتي. استنى دقيقة وجرّب تاني (أو رقّي الاشتراك).";
      if (/credit|quota|insufficient/i.test(m)) return "رصيد ElevenLabs خلص.";
      return "ElevenLabs رجّع خطأ: " + m.slice(0, 160);
    }
    case "cancelled": return "اتلغى.";
    case "not_granted": case "capability_disabled": case "capability_removed": return "الاتصال بـ ElevenLabs مش متاح في العرض ده — افتح الصفحة من claude.ai.";
    default: return e?.message ? String(e.message).slice(0, 160) : "حصلت مشكلة مع ElevenLabs.";
  }
}

// Find values anywhere in a tool's JSON answer (the connector's exact shape may vary).
function walk(v, fn, key = "") {
  if (v == null) return;
  if (typeof v === "string") { fn(key, v); if (/^\s*[{[]/.test(v)) { try { walk(JSON.parse(v), fn, key); } catch { /* plain text */ } } return; }
  if (typeof v !== "object") { fn(key, v); return; }
  if (Array.isArray(v)) { v.forEach((x) => walk(x, fn, key)); return; }
  for (const k of Object.keys(v)) walk(v[k], fn, k);
}
function findFirst(v, keys) { let out; walk(v, (k, x) => { if (out === undefined && keys.includes(k)) out = x; }); return out; }
function findAll(v, keys) { const out = []; walk(v, (k, x) => { if (keys.includes(k) && typeof x === "string") out.push(x); }); return [...new Set(out)]; }
function findUrls(v, kind) {
  const urls = []; walk(v, (k, x) => { if (typeof x === "string" && /^https?:\/\//.test(x)) urls.push({ k, x }); });
  const bad = /orb|preview|thumbnail|\/app\/|\/flows?\/|canvas/i;
  const ext = kind === "audio" ? /\.(mp3|wav|m4a|ogg|aac|opus)(\?|$)/i : /\.(png|jpe?g|webp|gif)(\?|$)/i;
  const scored = urls.filter((u) => !bad.test(u.x)).map((u) => ({ u: u.x, s: (ext.test(u.x) ? 3 : 0) + (/url|output|file|src|download|media/i.test(u.k) ? 1 : 0) + (new RegExp(kind, "i").test(u.x + u.k) ? 1 : 0) }));
  scored.sort((a, b) => b.s - a.s);
  return scored.map((x) => x.u);
}

async function callTool(mcp, tool, input, signal) {
  const r = await mcp.callTool(SERVER, tool, input, { cache: false, signal });
  return r.payload ?? r;
}

const sleep = (ms, signal) => new Promise((res, rej) => {
  const t = setTimeout(res, ms);
  signal?.addEventListener("abort", () => { clearTimeout(t); rej({ code: "cancelled" }); }, { once: true });
});

/** Start a generation, wait for it, return {url, flowUrl}. */
async function generate(tool, input, kind, { signal, onStatus } = {}) {
  const mcp = await getMcp();
  if (!mcp) throw { code: "capability_disabled" };
  const started = await callTool(mcp, tool, input, signal);
  const flowId = findFirst(started, ["flow_id", "flowId"]);
  const sessions = findAll(started, ["session_ids", "session_id", "sessionIds"]);
  const flowUrl = findUrls(started, "app").find((u) => /elevenlabs/i.test(u)) || findFirst(started, ["url"]);
  let direct = findUrls(started, kind)[0];
  if (direct && /\.(mp3|wav|m4a|png|jpe?g|webp)/i.test(direct)) return { url: direct, flowUrl };
  if (!flowId || !sessions.length) throw { code: "tool_error", message: "رد ElevenLabs ماكانش فيه رقم العملية." };
  const t0 = Date.now();
  while (Date.now() - t0 < 12 * 60 * 1000) {
    const wait = Number(findFirst(started, ["poll_after_seconds"])) || 4;
    await sleep(Math.min(15, Math.max(2, wait)) * 1000, signal);
    const st = await callTool(mcp, "creative_get_flow_run_status", { flow_id: flowId, session_ids: sessions, context: "Wait for a stick figure video asset to finish generating" }, signal);
    const done = findFirst(st, ["all_completed"]), failed = findFirst(st, ["has_failures"]);
    onStatus?.(Math.round((Date.now() - t0) / 1000));
    if (failed === true) throw { code: "tool_error", message: String(findFirst(st, ["error", "error_message", "failure_reason"]) || "فشل التوليد") };
    if (done === true) {
      const url = findUrls(st, kind)[0];
      if (!url) throw { code: "tool_error", message: "التوليد خلص بس مالقيتش رابط الملف.", flowUrl };
      return { url, flowUrl };
    }
  }
  throw { code: "tool_error", message: "التوليد أخد وقت طويل جداً." };
}

/** Download a generated file into a Blob (needs the host to allow it). */
export async function fetchBlob(url) {
  try {
    const r = await fetch(url);
    if (!r.ok) throw new Error(r.status);
    return await r.blob();
  } catch {
    throw { code: "fetch_blocked", url };
  }
}

export async function generateImage(prompt, model, opts) {
  const { url, flowUrl } = await generate("creative_generate_image", {
    prompt, model_id: model, generations_count: 1,
    context: "Generate one 16:9 stick figure scene image for an animated Arabic story video",
  }, "image", opts);
  return { blob: await fetchBlob(url), url, flowUrl };
}

export async function generateSpeech(text, voiceId, opts) {
  const { url, flowUrl } = await generate("creative_generate_speech", {
    prompt: text, model_id: "eleven_multilingual_v2", voice_id: voiceId, generations_count: 1,
    context: "Narrate one part of an Arabic stick figure story video",
  }, "audio", opts);
  return { blob: await fetchBlob(url), url, flowUrl };
}

/** Split the beats into narration parts of at most ~maxChars, on beat boundaries. */
export function narrationParts(beats, maxChars = 1800) {
  const parts = []; let cur = null;
  for (const b of beats) {
    const isTitle = b.text.trim().startsWith("##");
    const t = b.text.replace(/^#+\s*/, "").trim() + (isTitle ? " ..." : "");
    if (!cur || cur.text.length + t.length > maxChars || isTitle) {
      cur = { from: b.n, to: b.n, text: t }; parts.push(cur);
    } else { cur.to = b.n; cur.text += " " + t; }
  }
  return parts;
}

export async function blobToImage(blob) {
  if (window.createImageBitmap) { try { return await createImageBitmap(blob); } catch { /* fall back */ } }
  const url = URL.createObjectURL(blob);
  const img = new Image(); img.src = url; await img.decode(); return img;
}

export async function decodeAudio(blob) {
  const actx = new (window.AudioContext || window.webkitAudioContext)();
  try { return await actx.decodeAudioData(await blob.arrayBuffer()); } finally { actx.close(); }
}

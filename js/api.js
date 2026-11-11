// Two engines for the workers:
// 1) Inside claude.ai (published Artifact): the `sample` capability — runs on the viewer's own
//    Claude account, no API key needed.
// 2) Anywhere else (GitHub Pages, local server): the official Anthropic SDK with the visitor's
//    own API key, sent straight to api.anthropic.com.

export const MODELS = [
  { id: "claude-opus-5-5", label: "Claude Opus 5.5 (الأفضل جودة)" },
  { id: "claude-sonnet-5-5", label: "Claude Sonnet 5.5 (أسرع وأرخص)" },
  { id: "claude-haiku-5-5", label: "Claude Haiku 5.5 (الأرخص)" },
];

const SYSTEM_BASE =
  "You are an Elite Stick Figure Animation Director, Visual Storytelling Expert, Scene Composition Specialist, and Motion Design Director working inside a 15-worker video production factory. " +
  "All Arabic outputs (ideas, script, beats, explanations) are natural, clear Arabic. All image, character sheet, animation and thumbnail prompts are written entirely in English. " +
  "No preambles, no filler. Follow the station brief exactly.";

// ---------- engine detection ----------
let samplePromise = null;
/** Resolves the claude.ai `sample` function, or null outside claude.ai. */
export function getSample() {
  if (!samplePromise) {
    samplePromise =
      typeof window !== "undefined" && window.claude?.use
        ? window.claude.use("sample").catch(() => null)
        : Promise.resolve(null);
  }
  return samplePromise;
}

let downloadsPromise = null;
export function getDownloads() {
  if (!downloadsPromise) {
    downloadsPromise =
      typeof window !== "undefined" && window.claude?.use
        ? window.claude.use("downloads").catch(() => null)
        : Promise.resolve(null);
  }
  return downloadsPromise;
}

/**
 * Run one station call.
 * @param {object} opts
 * @param {string} [opts.apiKey]  needed only outside claude.ai
 * @param {string} opts.model
 * @param {string} opts.brief     station instructions
 * @param {string} opts.input     user content
 * @param {object} [opts.schema]  JSON schema -> returns parsed object
 * @param {AbortSignal} [opts.signal]
 * @param {(chars:number)=>void} [opts.onProgress]
 */
export async function runStation(opts) {
  const sample = await getSample();
  if (sample) return viaSample(sample, opts);
  if (!opts.apiKey) throw new Error("حط مفتاح Claude API من الإعدادات الأول.");
  return viaSdk(opts);
}

// ---------- engine 1: claude.ai sample ----------
async function viaSample(sample, { brief, input, schema, signal, onProgress }) {
  let prompt = SYSTEM_BASE + "\n\nSTATION BRIEF:\n" + brief + "\n\n---\nINPUT:\n" + input;
  if (schema) {
    prompt +=
      "\n\n---\nReply with ONLY one JSON value matching this JSON schema, nothing before or after it:\n" +
      JSON.stringify(schema);
  }
  const options = {
    modelTier: "complex",
    signal,
    cache: false,
    onText: ({ text }) => onProgress?.(text.length),
  };
  try {
    if (schema) return await sample.json(prompt, options);
    const { text, truncated } = await sample(prompt, options);
    if (truncated) throw { code: "truncated" };
    return text.trim();
  } catch (e) {
    throw new Error(sampleError(e));
  }
}

function sampleError(e) {
  switch (e?.code) {
    case "not_granted": return "لازم توافق إن الصفحة تستخدم Claude. افتح قائمة الصلاحيات (Permissions) في الأرتيفاكت وفعّلها.";
    case "sampling_disabled": return "Claude مش متاح لحسابك هنا.";
    case "rate_limited": return "وصلت لحد الاستخدام. استنى شوية وجرّب تاني.";
    case "session_expired": return "سجّل دخول تاني في claude.ai.";
    case "refused": return "Claude رفض الطلب ده. جرّب تعدّل الموضوع أو الصياغة.";
    case "invalid_json": return "الرد مكانش بالشكل المطلوب. اضغط إعادة تشغيل العامل.";
    case "prompt_too_large": return "المدخلات كبيرة جداً. جرّب مدة فيديو أقصر.";
    case "truncated": return "الرد اتقطع لأنه طويل جداً. جرّب مدة أقصر.";
    case "cancelled": return "تم إيقاف العامل.";
    case "empty_completion": return "Claude مرجّعش رد. اضغط إعادة تشغيل العامل.";
    default: return "حصلت مشكلة في الاتصال. اضغط إعادة تشغيل العامل.";
  }
}

// ---------- engine 2: Anthropic SDK with an API key ----------
let sdkPromise = null;
function loadSdk() {
  sdkPromise ??= import("https://cdn.jsdelivr.net/npm/@anthropic-ai/sdk@1.3.0/+esm").then((m) => m.default);
  return sdkPromise;
}

async function viaSdk({ apiKey, model, brief, input, schema, signal, onProgress }) {
  let Anthropic;
  try {
    Anthropic = await loadSdk();
  } catch {
    sdkPromise = null;
    throw new Error("مقدرتش أحمّل مكتبة Claude. اتأكد من الإنترنت.");
  }
  const client = new Anthropic({ apiKey, dangerouslyAllowBrowser: true });

  const params = {
    model,
    max_tokens: 64000,
    system: SYSTEM_BASE + "\n\nSTATION BRIEF:\n" + brief,
    messages: [{ role: "user", content: input }],
    output_config: { effort: "medium" },
  };
  if (schema) params.output_config.format = { type: "json_schema", schema };
  // Opus 5.5 / Sonnet 5.5: let the API re-run a declined request on a recommended fallback model.
  const useFallback = model === "claude-opus-5-5" || model === "claude-sonnet-5-5";
  if (useFallback) {
    params.betas = ["server-side-fallback-2026-07-01"];
    params.fallbacks = "default";
  }

  const stream = useFallback
    ? client.beta.messages.stream(params, { signal })
    : client.messages.stream(params, { signal });

  let chars = 0;
  stream.on("text", (t) => {
    chars += t.length;
    onProgress?.(chars);
  });

  let message;
  try {
    message = await stream.finalMessage();
  } catch (err) {
    throw new Error(sdkError(Anthropic, err));
  }

  if (message.stop_reason === "refusal") throw new Error("النموذج رفض الطلب ده. جرّب تعدّل الموضوع أو الصياغة.");
  if (message.stop_reason === "max_tokens") throw new Error("الرد اتقطع لأنه طويل جداً. جرّب مدة أقصر.");
  const text = message.content.filter((b) => b.type === "text").map((b) => b.text).join("");

  if (!schema) return text.trim();
  try {
    return JSON.parse(text);
  } catch {
    throw new Error("الرد مكانش JSON سليم. اضغط إعادة تشغيل العامل.");
  }
}

function sdkError(Anthropic, err) {
  if (err instanceof Anthropic.AuthenticationError) return "مفتاح الـ API غلط أو منتهي.";
  if (err instanceof Anthropic.PermissionDeniedError) return "المفتاح ده مالوش صلاحية على الموديل المختار.";
  if (err instanceof Anthropic.NotFoundError) return "الموديل المختار مش متاح لحسابك.";
  if (err instanceof Anthropic.RateLimitError) return "تخطيت حد الطلبات. استنى دقيقة وجرّب تاني.";
  if (err instanceof Anthropic.APIUserAbortError || err?.name === "AbortError") return "تم إيقاف العامل.";
  if (err instanceof Anthropic.APIConnectionError) return "مفيش اتصال بسيرفر Claude. اتأكد من الإنترنت.";
  if (err instanceof Anthropic.APIError) return `خطأ من الـ API (${err.status ?? "?"}): ${err.message}`;
  return err?.message || String(err);
}

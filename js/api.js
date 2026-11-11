// Claude API access straight from the browser, using the official Anthropic TypeScript/JS SDK.
// The API key stays in the visitor's own browser (localStorage) and is sent only to api.anthropic.com.
import Anthropic from "https://cdn.jsdelivr.net/npm/@anthropic-ai/sdk@1.3.0/+esm";

export const MODELS = [
  { id: "claude-opus-5-5", label: "Claude Opus 5.5 (الأفضل جودة)" },
  { id: "claude-sonnet-5-5", label: "Claude Sonnet 5.5 (أسرع وأرخص)" },
  { id: "claude-haiku-5-5", label: "Claude Haiku 5.5 (الأرخص)" },
];

const SYSTEM_BASE =
  "You are an Elite Stick Figure Animation Director, Visual Storytelling Expert, Scene Composition Specialist, and Motion Design Director working inside a 15-worker video production factory. " +
  "All Arabic outputs (ideas, script, beats, explanations) are natural, clear Arabic. All image, character sheet, animation and thumbnail prompts are written entirely in English. " +
  "No preambles, no filler. Follow the station brief exactly.";

/**
 * Run one station call.
 * @param {object} opts
 * @param {string} opts.apiKey
 * @param {string} opts.model
 * @param {string} opts.brief    station instructions (system addition)
 * @param {string} opts.input    user content
 * @param {object} [opts.schema] JSON schema -> structured output; returns parsed object
 * @param {AbortSignal} [opts.signal]
 * @param {(chars:number)=>void} [opts.onProgress]
 */
export async function runStation({ apiKey, model, brief, input, schema, signal, onProgress }) {
  const client = new Anthropic({ apiKey, dangerouslyAllowBrowser: true });

  const params = {
    model,
    max_tokens: 64000,
    system: SYSTEM_BASE + "\n\nSTATION BRIEF:\n" + brief,
    messages: [{ role: "user", content: input }],
    output_config: { effort: "medium" },
  };
  if (schema) {
    params.output_config.format = { type: "json_schema", schema };
  }
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
    throw new Error(describeError(err));
  }

  if (message.stop_reason === "refusal") {
    throw new Error("النموذج رفض الطلب ده. جرّب تعدّل الموضوع أو الصياغة.");
  }
  if (message.stop_reason === "max_tokens") {
    throw new Error("الرد اتقطع لأنه طويل جداً. جرّب مدة أقصر.");
  }
  const text = message.content
    .filter((b) => b.type === "text")
    .map((b) => b.text)
    .join("");

  if (!schema) return text.trim();
  try {
    return JSON.parse(text);
  } catch {
    throw new Error("الرد مكانش JSON سليم. اضغط إعادة تشغيل العامل.");
  }
}

function describeError(err) {
  if (err instanceof Anthropic.AuthenticationError) return "مفتاح الـ API غلط أو منتهي.";
  if (err instanceof Anthropic.PermissionDeniedError) return "المفتاح ده مالوش صلاحية على الموديل المختار.";
  if (err instanceof Anthropic.NotFoundError) return "الموديل المختار مش متاح لحسابك.";
  if (err instanceof Anthropic.RateLimitError) return "تخطيت حد الطلبات. استنى دقيقة وجرّب تاني.";
  if (err instanceof Anthropic.APIConnectionError) return "مفيش اتصال بسيرفر Claude. اتأكد من الإنترنت.";
  if (err instanceof Anthropic.APIError) return `خطأ من الـ API (${err.status ?? "?"}): ${err.message}`;
  if (err?.name === "AbortError" || err instanceof Anthropic.APIUserAbortError) return "تم إيقاف العامل.";
  return err?.message || String(err);
}

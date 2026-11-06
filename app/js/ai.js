// عملاء الذكاء الاصطناعي: Claude للنصوص، مزوّدو الصور، وElevenLabs للصوت
import Anthropic from '../vendor/anthropic-sdk.mjs';
import { Settings } from './store.js';
import { paintProcedural } from './procedural-art.js';

// ---------- Claude ----------
// Builds a strict JSON-schema object: every key required, no extras (structured-outputs requirement).
export function obj(props) {
  return { type: 'object', properties: props, required: Object.keys(props), additionalProperties: false };
}
export const str = (description) => (description ? { type: 'string', description } : { type: 'string' });
export const num = (description) => (description ? { type: 'number', description } : { type: 'number' });
export const arr = (items, description) => (description ? { type: 'array', items, description } : { type: 'array', items });
export const en = (values, description) => ({ type: 'string', enum: values, ...(description ? { description } : {}) });

const FALLBACK_MODELS = ['claude-opus-5-5', 'claude-sonnet-5-5', 'claude-opus-5', 'claude-fable-5-1'];

export function hasClaude() {
  return !!Settings.get().claudeKey;
}

export async function claudeJSON({ system, prompt, schema, effort = 'high', maxTokens = 32000, signal }) {
  const s = Settings.get();
  if (!s.claudeKey) throw new Error('مفتاح Claude غير مضبوط');
  const client = new Anthropic({ apiKey: s.claudeKey, dangerouslyAllowBrowser: true, maxRetries: 3 });
  const useFallbacks = FALLBACK_MODELS.includes(s.claudeModel);

  const base = {
    model: s.claudeModel,
    max_tokens: maxTokens,
    thinking: { type: 'adaptive' },
    system,
    messages: [{ role: 'user', content: prompt }],
    ...(useFallbacks ? { betas: ['server-side-fallback-2026-07-01'], fallbacks: 'default' } : {}),
  };

  const run = async (params) => {
    const stream = client.beta.messages.stream(params, { signal });
    const msg = await stream.finalMessage();
    if (msg.stop_reason === 'refusal') {
      throw new Error('رفض النموذج الطلب: ' + (msg.stop_details?.explanation || msg.stop_details?.category || ''));
    }
    if (msg.stop_reason === 'max_tokens') throw new Error('انقطع الرد لطوله (max_tokens)');
    return msg.content.filter((b) => b.type === 'text').map((b) => b.text).join('');
  };

  let text;
  try {
    text = await run({ ...base, output_config: { effort, format: { type: 'json_schema', schema } } });
  } catch (e) {
    // If the selected model rejects structured outputs, retry asking for raw JSON.
    if (e?.status === 400 && /format|schema|output_config/i.test(e.message || '')) {
      text = await run({
        ...base,
        output_config: { effort },
        messages: [{ role: 'user', content: prompt + '\n\nأعد JSON فقط مطابقًا لهذا المخطط دون أي نص آخر:\n' + JSON.stringify(schema) }],
      });
    } else {
      throw e;
    }
  }
  return parseJSONLoose(text);
}

function parseJSONLoose(text) {
  try {
    return JSON.parse(text);
  } catch {
    const m = text.match(/\{[\s\S]*\}/);
    if (m) return JSON.parse(m[0]);
    throw new Error('تعذر قراءة رد JSON من النموذج');
  }
}

// ---------- الصور ----------
export async function generateImage({ prompt, width, height, seed, hint }) {
  const s = Settings.get();
  const provider = s.imageProvider;
  try {
    if (provider === 'openai' && s.openaiKey) return await openaiImage(prompt, width, height, s.openaiKey);
    if (provider === 'pollinations') return await pollinationsImage(prompt, width, height, seed);
  } catch (e) {
    console.warn('image provider failed, using procedural art', e);
    const blob = await paintProcedural({ prompt: hint || prompt, width, height, seed });
    blob.fallback = String(e.message || e);
    return blob;
  }
  return paintProcedural({ prompt: hint || prompt, width, height, seed });
}

async function pollinationsImage(prompt, width, height, seed) {
  const url = `https://image.pollinations.ai/prompt/${encodeURIComponent(prompt)}?width=${width}&height=${height}&seed=${seed}&nologo=true&model=flux&enhance=false`;
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), 90000);
  try {
    const r = await fetch(url, { signal: ctrl.signal });
    if (!r.ok) throw new Error('Pollinations HTTP ' + r.status);
    const blob = await r.blob();
    if (!blob.type.startsWith('image/')) throw new Error('Pollinations returned non-image');
    return blob;
  } finally {
    clearTimeout(t);
  }
}

async function openaiImage(prompt, width, height, key) {
  const size = width > height ? '1536x1024' : width < height ? '1024x1536' : '1024x1024';
  const r = await fetch('https://api.openai.com/v1/images/generations', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + key },
    body: JSON.stringify({ model: 'gpt-image-1', prompt, size, n: 1, quality: 'medium' }),
  });
  if (!r.ok) throw new Error('OpenAI images HTTP ' + r.status + ' ' + (await r.text()).slice(0, 200));
  const j = await r.json();
  const b64 = j.data?.[0]?.b64_json;
  if (!b64) throw new Error('OpenAI images: empty');
  const bin = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
  return new Blob([bin], { type: 'image/png' });
}

// ---------- الصوت (التعليق) ----------
export function hasVoice() {
  const s = Settings.get();
  return !!s.elevenKey;
}

const DEFAULT_VOICE = 'JBFqnCBsd6RMkjVDRZzb';

export async function synthesizeSpeech(text) {
  const s = Settings.get();
  const voice = s.elevenVoice || DEFAULT_VOICE;
  // eleven_v3 understands inline audio tags like [whispers]; older models would read them aloud.
  const finalText = s.elevenModel === 'eleven_v3' ? text : stripTags(text);
  const r = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${voice}?output_format=mp3_44100_128`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'xi-api-key': s.elevenKey, Accept: 'audio/mpeg' },
    body: JSON.stringify({ text: finalText, model_id: s.elevenModel || 'eleven_v3' }),
  });
  if (!r.ok) throw new Error('ElevenLabs HTTP ' + r.status + ' ' + (await r.text()).slice(0, 200));
  return r.blob();
}

export function stripTags(t) {
  return String(t || '').replace(/\[[^\]]*\]/g, '').replace(/\s+/g, ' ').trim();
}

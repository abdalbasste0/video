"""One small helper every thinking worker uses to talk to Claude."""
import json
import os

import anthropic

from .style import STORY_GUIDE, STYLE_GUIDE

FALLBACK_BETA = "server-side-fallback-2026-07-01"
# Models that accept server-side refusal fallbacks ("default" routing).
_FALLBACK_MODELS = ("claude-opus-5-5", "claude-sonnet-5-5", "claude-fable-5")

_clients = {}


class LLMError(RuntimeError):
    pass


NO_KEY = ("No Claude API key. Open the dashboard → Settings (الإعدادات) → «مفتاح Anthropic API», paste your key "
          "from https://console.anthropic.com/settings/keys (it starts with sk-ant-), press Save, then press "
          "«🔑 جرّب مفتاح Claude». | مفيش مفتاح Claude: حطه في الإعدادات واضغط حفظ.")


def api_key(settings):
    """The key from the dashboard (spaces/newlines from copy-paste removed) or the environment."""
    return "".join((settings.get("anthropic_api_key") or os.environ.get("ANTHROPIC_API_KEY") or "").split())


def has_key(settings):
    return bool(api_key(settings) or os.environ.get("ANTHROPIC_AUTH_TOKEN"))


def _client(settings):
    key = api_key(settings)
    if not has_key(settings):
        raise LLMError(NO_KEY)
    if key not in _clients:
        _clients[key] = anthropic.Anthropic(api_key=key, max_retries=4) if key else anthropic.Anthropic(max_retries=4)
    return _clients[key]


NO_CREDIT = ("Your Anthropic API account has no credit. Add credit at https://console.anthropic.com/settings/billing "
             "(API credit is separate from a claude.ai subscription), or make the video from a ready plan "
             "(Run tab → «📄 فيديو من خطة جاهزة»). | الرصيد خلص: اشحن من صفحة Billing أو استخدم خطة جاهزة.")


def _status_message(e):
    if "credit balance" in str(e.message).lower():
        return NO_CREDIT
    return f"Claude API error {e.status_code}: {e.message}"


def check_key(settings):
    """Tiny request to confirm the key works. Returns (ok, message)."""
    try:
        r = _client(settings).messages.create(model=settings["model_main"], max_tokens=16,
                                               messages=[{"role": "user", "content": "Reply with the word OK."}])
        return True, f"OK ({r.model})"
    except LLMError as e:
        return False, str(e)
    except anthropic.AuthenticationError:
        return False, "The key was rejected (invalid or revoked). Create a new key at console.anthropic.com. | المفتاح غلط."
    except anthropic.PermissionDeniedError as e:
        return False, f"Key has no access to this model or no credit: {e.message}"
    except anthropic.APIStatusError as e:
        return False, _status_message(e)
    except anthropic.APIConnectionError:
        return False, "Could not reach api.anthropic.com. Check your internet connection."


def model_for(settings, worker_id):
    slot = settings["workers"].get(worker_id, {}).get("model", "main")
    return settings["model_fast"] if slot == "fast" else settings["model_main"]


def ask(settings, worker_id, role, task, schema=None, web=False, max_tokens=16000):
    """Run one worker turn. Returns parsed JSON when `schema` is given, else text.
    Web research + JSON is done in two passes (search -> notes, notes -> JSON) because
    search citations and strict JSON output don't mix in one response."""
    if web and schema and settings.get("web_research", True):
        notes = _ask(settings, worker_id, role, task + "\n\nاكتب ملاحظاتك كاملة بالمصادر (روابط).", None, True, max_tokens)
        return _ask(settings, worker_id, role,
                    task + "\n\nاعتمد فقط على ملاحظات البحث دي وحوّلها للصيغة المطلوبة:\n" + notes, schema, False, max_tokens)
    return _ask(settings, worker_id, role, task, schema, web, max_tokens)


def _ask(settings, worker_id, role, task, schema, web, max_tokens):
    model = model_for(settings, worker_id)
    ch = settings["channel"]
    system = [
        {"type": "text", "text": STORY_GUIDE if ch.get("format") == "story" else STYLE_GUIDE},
        {"type": "text", "text": (
            f"القناة: {ch['name']} | المجال: {ch['niche']} | اللهجة: {ch['dialect']} | الجمهور: {ch['audience']}\n"
            f"أنت عامل في مصنع فيديوهات. دورك: {role}\n"
            "اشتغل على دورك بس، وسلّم نتيجة جاهزة للعامل اللي بعدك. ممنوع تخترع حقائق أو أرقام أو مصادر."
            + ("\nVIDEO LANGUAGE: ENGLISH. Write every narration line, title, label, stamp, caption, thumbnail text and "
               "SEO field in natural spoken English (ignore the dialect line above). Keep the same structure and style."
               if ch.get("language") == "en" else "")
        ), "cache_control": {"type": "ephemeral"}},
    ]
    params = dict(
        model=model,
        max_tokens=max_tokens,
        system=system,
        thinking={"type": "adaptive"},
        output_config={"effort": settings.get("effort", "high")},
    )
    if schema:
        params["output_config"]["format"] = {"type": "json_schema", "schema": schema}
    if web and settings.get("web_research", True):
        params["tools"] = [{"type": "web_search_20260209", "name": "web_search", "max_uses": 8}]
    if model.startswith(_FALLBACK_MODELS):
        params["betas"] = [FALLBACK_BETA]
        params["fallbacks"] = "default"

    messages = [{"role": "user", "content": task}]
    client = _client(settings)
    for _ in range(6):  # web search may pause a long turn; continue it
        try:
            with client.beta.messages.stream(messages=messages, **params) as stream:
                resp = stream.get_final_message()
        except anthropic.AuthenticationError as e:
            raise LLMError("مفتاح Anthropic غير صحيح أو غير موجود (الإعدادات ← مفتاح API).") from e
        except anthropic.RateLimitError as e:
            raise LLMError("تم تجاوز حد الطلبات - قلّل عدد الفيديوهات المتوازية أو انتظر قليلاً.") from e
        except anthropic.APIStatusError as e:
            raise LLMError(_status_message(e)) from e
        except anthropic.APIConnectionError as e:
            raise LLMError("تعذر الاتصال بـ Claude API - تأكد من الإنترنت.") from e

        if resp.stop_reason == "pause_turn":
            messages = [messages[0], {"role": "assistant", "content": resp.content}]
            continue
        if resp.stop_reason == "refusal":
            raise LLMError(f"النموذج رفض مهمة العامل {worker_id}. غيّر الموضوع أو صياغته.")
        if resp.stop_reason == "max_tokens":
            raise LLMError(f"رد العامل {worker_id} اتقطع (max_tokens).")
        text = "".join(b.text for b in resp.content if b.type == "text").strip()
        if not schema:
            return text
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise LLMError(f"العامل {worker_id} رجّع JSON غير صالح.") from e
    raise LLMError(f"العامل {worker_id} ما خلّصش بعد عدة محاولات.")


def obj(props, required=None):
    """Tiny JSON-schema builder."""
    return {"type": "object", "properties": props,
            "required": required or list(props), "additionalProperties": False}


S = {"type": "string"}
I = {"type": "integer"}


def arr(item):
    return {"type": "array", "items": item}

"""Ready-made connections to image generators. Pick one in the dashboard (الإعدادات ← الصور),
paste its key, press «جرّب توليد صورة». Every provider returns a PIL image.

  pollinations  free, no key (rate-limited, quality varies)
  openai        OpenAI Images (gpt-image-1)           key from platform.openai.com
  stability     Stability AI Stable Image Core         key from platform.stability.ai
  fal           fal.ai FLUX schnell (fast, cheap)      key from fal.ai
  a1111         Stable Diffusion WebUI on your own GPU (free; start it with --api)
  http          any other API: POST {prompt,width,height} → image bytes or JSON (b64 / url)
"""
import base64
import io
import urllib.parse

import requests
from PIL import Image

T = 240

PROVIDERS = {
    "cards": "بدون (رسم محلي فقط)",
    "pollinations": "Pollinations — مجاني بدون مفتاح",
    "openai": "OpenAI (gpt-image-1)",
    "stability": "Stability AI (Stable Image Core)",
    "fal": "fal.ai (FLUX schnell)",
    "a1111": "Stable Diffusion على جهازك (AUTOMATIC1111)",
    "http": "API مخصص",
}


def _img(data):
    return Image.open(io.BytesIO(data)).convert("RGB")


def _from_json(j):
    """Find an image in common JSON response shapes."""
    if isinstance(j, dict):
        for key in ("data", "images", "output", "artifacts"):
            v = j.get(key)
            if isinstance(v, list) and v:
                return _from_json(v[0])
            if isinstance(v, (dict, str)) and v:
                return _from_json(v)
        for key in ("b64_json", "image_base64", "b64", "base64", "image"):
            if isinstance(j.get(key), str) and len(j[key]) > 200:
                return _img(base64.b64decode(j[key].split(",", 1)[-1]))
        url = j.get("url") or j.get("image_url")
        if url:
            return _img(requests.get(url, timeout=T).content)
    if isinstance(j, str):
        if j.startswith("http"):
            return _img(requests.get(j, timeout=T).content)
        return _img(base64.b64decode(j.split(",", 1)[-1]))
    raise ValueError("لم أجد صورة في رد الـ API")


def _check(r):
    if r.status_code >= 400:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")
    return r


def generate(prompt, cfg, w=1280, h=720, seed=None):
    p = cfg.get("provider", "cards")
    key = cfg.get("api_key", "")
    model = cfg.get("model", "")
    base = (cfg.get("base_url") or "").rstrip("/")

    if p == "pollinations":
        url = (base or "https://image.pollinations.ai") + "/prompt/" + urllib.parse.quote(prompt, safe="")
        params = {"width": w, "height": h, "nologo": "true", "model": model or "flux"}
        if seed is not None:
            params["seed"] = seed
        headers = {"Authorization": f"Bearer {key}"} if key else {}
        r = _check(requests.get(url, params=params, headers=headers, timeout=T))
        return _img(r.content)

    if p == "openai":
        r = _check(requests.post((base or "https://api.openai.com") + "/v1/images/generations",
                                 headers={"Authorization": f"Bearer {key}"},
                                 json={"model": model or "gpt-image-1", "prompt": prompt, "size": "1536x1024", "n": 1},
                                 timeout=T))
        return _from_json(r.json())

    if p == "stability":
        r = _check(requests.post((base or "https://api.stability.ai") + "/v2beta/stable-image/generate/core",
                                 headers={"Authorization": f"Bearer {key}", "Accept": "image/*"},
                                 files={"none": ("", "")},
                                 data={"prompt": prompt, "aspect_ratio": "16:9", "output_format": "png"}, timeout=T))
        return _img(r.content)

    if p == "fal":
        r = _check(requests.post((base or "https://fal.run") + "/" + (model or "fal-ai/flux/schnell"),
                                 headers={"Authorization": f"Key {key}"},
                                 json={"prompt": prompt, "image_size": "landscape_16_9", "num_images": 1}, timeout=T))
        return _from_json(r.json())

    if p == "a1111":
        r = _check(requests.post((base or "http://127.0.0.1:7860") + "/sdapi/v1/txt2img",
                                 json={"prompt": prompt, "negative_prompt": "text, watermark, letters, blurry",
                                       "width": min(w, 1344), "height": min(h, 768), "steps": 25,
                                       "seed": seed if seed is not None else -1}, timeout=T))
        return _from_json(r.json())

    if p == "http":
        headers = {"Content-Type": "application/json"}
        if cfg.get("http_auth_header"):
            name, _, value = cfg["http_auth_header"].partition(":")
            headers[name.strip()] = value.strip()
        r = _check(requests.post(cfg.get("http_url") or base, json={"prompt": prompt, "width": w, "height": h},
                                 headers=headers, timeout=T))
        if r.headers.get("content-type", "").startswith("image/"):
            return _img(r.content)
        return _from_json(r.json())

    raise ValueError("مفيش مولّد صور مختار")


def enabled(cfg):
    p = cfg.get("provider", "cards")
    if p in ("cards", "", None):
        return False
    if p == "http":
        return bool(cfg.get("http_url"))
    if p in ("openai", "stability", "fal"):
        return bool(cfg.get("api_key"))
    return True

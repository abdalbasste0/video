"""Learn from a draft YOU made in CapCut:
  1. detect whether your CapCut version encrypts drafts,
  2. print the JSON structure (tracks, material types, keyframe property names),
  3. harvest effect / transition / animation / filter IDs into effects_library.json.

Usage:  python main.py learn-draft "<drafts_dir>/FactorySample"
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path

ADJUST_NAMES = {"brightness", "contrast", "saturation", "temperature", "tone", "highlight", "shadow",
                "sharpen", "light_sensation", "fade", "vignetting", "particle"}


def slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", (name or "").lower()).strip("_")
    return s or "item"


def entropy(data: bytes) -> float:
    if not data:
        return 0.0
    c = Counter(data)
    return -sum(n / len(data) * math.log2(n / len(data)) for n in c.values())


def load_draft(folder: Path) -> tuple[dict | None, str]:
    for name in ("draft_content.json", "draft_info.json"):
        f = folder / name
        if not f.exists():
            continue
        raw = f.read_bytes()
        try:
            return json.loads(raw.decode("utf-8")), name
        except (UnicodeDecodeError, json.JSONDecodeError):
            e = entropy(raw[:65536])
            return None, (f"{name} is NOT plain JSON (entropy {e:.2f} bits/byte"
                          f"{' → looks ENCRYPTED' if e > 7.0 else ''})")
    return None, "no draft_content.json / draft_info.json found"


def summarize(doc: dict) -> dict:
    tracks = [{"type": t.get("type"), "segments": len(t.get("segments", [])), "name": t.get("name", "")}
              for t in doc.get("tracks", [])]
    mats = {k: len(v) for k, v in (doc.get("materials") or {}).items() if isinstance(v, list) and v}
    kf_props = sorted({kf.get("property_type") for t in doc.get("tracks", []) for s in t.get("segments", [])
                       for kf in (s.get("common_keyframes") or [])} - {None})
    effect_types = sorted({e.get("type") for e in doc.get("materials", {}).get("effects", [])} - {None})
    return {"canvas": doc.get("canvas_config"), "fps": doc.get("fps"), "version": doc.get("version"),
            "new_version": doc.get("new_version"), "platform": doc.get("platform"),
            "tracks": tracks, "materials": mats, "keyframe_properties": kf_props, "effect_types": effect_types}


def harvest(doc: dict, library: dict) -> dict:
    m = doc.get("materials", {})
    added: Counter = Counter()

    def put(section: str, item: dict, extra: dict | None = None) -> None:
        if not item.get("resource_id") and not item.get("effect_id"):
            return
        lib = library.setdefault(section, {})
        target = next((k for k, v in lib.items() if v.get("name", "").lower() == (item.get("name") or "").lower()),
                      None) or slug(item.get("name"))
        entry = lib.setdefault(target, {})
        entry.update({"name": item.get("name", target), "resource_id": item.get("resource_id"),
                      "effect_id": item.get("effect_id") or item.get("id"), "path": item.get("path", "")})
        if extra:
            entry.update(extra)
        added[section] += 1

    for t in m.get("transitions", []):
        put("transitions", t, {"duration_us": t.get("duration", 400000), "is_overlap": t.get("is_overlap", True)})
    for e in m.get("video_effects", []):
        put("video_effects", e)
    for e in m.get("effects", []):
        if e.get("type") == "filter":
            put("filters", e)
        elif e.get("type") in ADJUST_NAMES:
            library.setdefault("adjust", {})[e["type"]] = {"type": e["type"], "path": e.get("path", "")}
            added["adjust"] += 1
    for ma in m.get("material_animations", []):
        for a in ma.get("animations", []):
            put("text_animations", {**a, "effect_id": a.get("id")},
                {"type": a.get("type", "in"), "duration_us": a.get("duration", 300000)})
    for s in m.get("stickers", []):
        put("stickers", s)
    library["_learned_counts"] = dict(added)
    return library


def learn(folder: Path, library_path: Path) -> str:
    doc, msg = load_draft(folder)
    if doc is None:
        return ("❌ " + msg + "\n\nYour CapCut version appears to ENCRYPT drafts. Options (README §2b):\n"
                "  A) Install an older CapCut Desktop that writes plain JSON (community reports ≤ 5.x),\n"
                "     disable auto-update, recreate the sample, run learn-draft again.\n"
                "  B) Keep your CapCut and use render.backend: ffmpeg (full render without CapCut) —\n"
                "     drafts are still produced for older/compatible installs.\n")
    summary = summarize(doc)
    library = json.loads(library_path.read_text(encoding="utf-8")) if library_path.exists() else {}
    library = harvest(doc, library)
    library_path.write_text(json.dumps(library, ensure_ascii=False, indent=2), encoding="utf-8")
    (library_path.parent / "learned_draft_structure.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return ("✅ " + msg + " is plain JSON — drafts can be generated.\n"
            + json.dumps(summary, ensure_ascii=False, indent=2)
            + f"\n\nLearned into effects_library.json: {library.get('_learned_counts')}\n"
              f"Tip: set capcut.template_draft to this folder in config.yaml (template mode).")

"""
Quality Control helpers (the QC department head uses these + its own judgement).

Automatic checks implemented here:
  - originality: text similarity vs data/history.jsonl (must be < qc.max_similarity)
  - pacing:      no static screen longer than episode.max_static_seconds
  - length:      14:00-16:00
  - cast:        no two main characters share a color or accessory
Scored metrics (1-10, below qc.min_score = rework):
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter

from .config import DATA, settings
from . import shots as SH

METRICS = ["story_clarity", "mystery_fairness", "pacing", "animation_smoothness", "character_distinguishability",
           "audio_clarity", "sync", "text_readability", "originality"]


def _tokens(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def _vec(text: str, n=3) -> Counter:
    """Word 3-gram counts (works for any language, including Arabic)."""
    t = _tokens(text)
    grams = [" ".join(t[i:i + n]) for i in range(max(0, len(t) - n + 1))]
    return Counter(grams + t)  # unigrams too, so short texts still compare


def similarity(a: str, b: str) -> float:
    va, vb = _vec(a), _vec(b)
    dot = sum(va[k] * vb.get(k, 0) for k in va)
    na = math.sqrt(sum(v * v for v in va.values()))
    nb = math.sqrt(sum(v * v for v in vb.values()))
    return dot / (na * nb) if na and nb else 0.0


def history() -> list[dict]:
    f = DATA / "history.jsonl"
    if not f.exists():
        return []
    return [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]


def originality(text: str, exclude_id: str = None) -> dict:
    worst = {"id": None, "similarity": 0.0}
    for h in history():
        if h.get("id") == exclude_id:
            continue
        s = similarity(text, h.get("summary", "") + " " + h.get("premise", "") + " " + h.get("script_excerpt", ""))
        if s > worst["similarity"]:
            worst = {"id": h.get("id"), "similarity": round(s, 3)}
    limit = settings()["qc"]["max_similarity"]
    return {"max_similarity": worst["similarity"], "closest": worst["id"], "pass": worst["similarity"] < limit,
            "score": max(1, min(10, round(10 - worst["similarity"] * 10 / limit * 2 + 2)))}


def pacing(shots: list) -> dict:
    limit = settings()["episode"]["max_static_seconds"]
    bad = [(s["id"], SH.static_seconds(s)) for s in shots if SH.static_seconds(s) > limit]
    return {"static_over_limit": bad, "pass": not bad}


def length(seconds: float) -> dict:
    e = settings()["episode"]
    return {"seconds": round(seconds, 1), "pass": e["min_minutes"] * 60 <= seconds <= e["max_minutes"] * 60}


def cast_distinct(cast: list) -> dict:
    mains = [c for c in cast if c.get("role") != "extra"]
    cols = Counter(c.get("color") for c in mains)
    accs = Counter(c.get("accessory") for c in mains)
    dup = [k for k, v in list(cols.items()) + list(accs.items()) if v > 1]
    return {"duplicates": dup, "pass": not dup}


def verdict(scores: dict) -> dict:
    """scores: {metric: 1-10}. Returns which metrics need rework."""
    m = settings()["qc"]["min_score"]
    missing = [k for k in METRICS if k not in scores]
    low = {k: v for k, v in scores.items() if v < m}
    return {"pass": not low and not missing, "rework": low, "missing": missing}

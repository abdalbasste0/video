"""
Episode state machine + the department order.

output/<id>/state.json keeps everything about one episode:
  lang, status, each department's status and per-role results, QC loop count, event log.
data/episodes.csv is a one-line-per-episode overview (open it in Excel).

Status flow
  new -> in_progress -> needs_review  (after Script + Fact & Logic pass; YOU read review.md)
      -> approved -> in_progress (Storyboard ... Packaging) -> ready_for_final_review
      -> final_approved
  rejected        : you rejected the script (it goes back to Script)
  flagged_for_human: QC failed after max loops - needs you
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import re

from .config import DATA, OUTPUT, StudioError, episode_dir, read_json, roster, settings, write_json

REVIEW_GATE_AFTER = "fact_logic"


def departments() -> list[dict]:
    return sorted(roster()["departments"], key=lambda d: d["order"])


def dept_keys() -> list[str]:
    return [d["key"] for d in departments()]


def roles_of(dept: str) -> list[dict]:
    return [r for r in roster()["roles"] if r["department"] == dept]


def now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def state_path(ep_id):
    return episode_dir(ep_id) / "state.json"


def load(ep_id: str) -> dict | None:
    return read_json(OUTPUT / ep_id / "state.json")


def save(st: dict):
    st["updated"] = now()
    write_json(state_path(st["id"]), st)
    _sync_csv(st)


def log_event(st: dict, msg: str):
    st.setdefault("log", []).append({"t": now(), "event": msg})


def create(ep_id: str, lang: str) -> dict:
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", ep_id):
        raise StudioError("Episode id may only contain letters, numbers, - and _ (e.g. E001).")
    st = {"id": ep_id, "lang": lang, "status": "new", "created": now(), "updated": now(), "qc_loops": 0,
          "departments": {k: {"status": "pending", "roles": {}} for k in dept_keys()}, "log": []}
    log_event(st, f"created (language={lang})")
    save(st)
    return st


def next_department(st: dict) -> str | None:
    for k in dept_keys():
        if st["departments"][k]["status"] != "passed":
            return k
    return None


def can_start(st: dict, dept: str) -> tuple[bool, str]:
    keys = dept_keys()
    i = keys.index(dept)
    if i > 0 and st["departments"][keys[i - 1]]["status"] != "passed":
        return False, f"{keys[i - 1]} has not passed yet"
    if i > keys.index(REVIEW_GATE_AFTER) and settings()["review"].get("require_script_approval", True) \
            and st["status"] not in ("approved", "in_progress_after_review", "ready_for_final_review", "final_approved"):
        return False, "waiting for your script approval (python make.py review --id %s --approve)" % st["id"]
    return True, ""


def parse_report(text: str) -> dict:
    """Read '| R0xx | name | PASS/FAIL | notes |' rows from a department report."""
    out = {}
    for m in re.finditer(r"\|\s*(R\d{3})\s*\|[^|]*\|\s*(PASS|FAIL)\s*\|", text, re.I):
        out[m.group(1).upper()] = m.group(2).lower()
    return out


def mark(ep_id: str, dept: str, result: str) -> dict:
    st = load(ep_id)
    if not st:
        raise StudioError(f"Episode {ep_id} does not exist.")
    if dept not in st["departments"]:
        raise StudioError(f"Unknown department '{dept}'. Use one of: {', '.join(dept_keys())}")
    ok, why = can_start(st, dept)
    if not ok:
        raise StudioError(f"{dept} cannot be marked yet: {why}")
    rep = OUTPUT / ep_id / "reports" / f"{dept}.md"
    roles = parse_report(rep.read_text(encoding="utf-8")) if rep.exists() else {}
    expected = [r["id"] for r in roles_of(dept)]
    missing = [r for r in expected if r not in roles]
    if result == "pass" and (missing or any(v != "pass" for v in roles.values())):
        raise StudioError(f"Cannot mark {dept} as passed: report reports/{dept}.md is missing roles {missing} "
                          f"or has FAIL rows.")
    d = st["departments"][dept]
    d.update(status="passed" if result == "pass" else "failed", roles=roles, updated=now())
    log_event(st, f"{dept} -> {d['status']}")
    if result == "pass" and dept == REVIEW_GATE_AFTER:
        st["status"] = "needs_review"
        log_event(st, "waiting for human script review (review.md)")
    elif result == "pass" and dept == dept_keys()[-1]:
        st["status"] = "ready_for_final_review"
    elif st["status"] in ("new",):
        st["status"] = "in_progress"
    save(st)
    return st


def review(ep_id: str, approve=False, reject: str = None, final_approve=False) -> dict:
    st = load(ep_id)
    if not st:
        raise StudioError(f"Episode {ep_id} does not exist.")
    if approve:
        if st["status"] != "needs_review":
            raise StudioError(f"{ep_id} is '{st['status']}', not waiting for script review.")
        st["status"] = "approved"
        log_event(st, "script approved by human")
    elif reject is not None:
        st["status"] = "rejected"
        st["rejection"] = reject
        for k in ("script", "fact_logic"):
            st["departments"][k]["status"] = "pending"
        log_event(st, f"rejected by human: {reject}")
    elif final_approve:
        final = OUTPUT / ep_id / "final.mp4"
        if st["status"] != "ready_for_final_review" or not final.exists():
            raise StudioError("Final approval needs status ready_for_final_review and output/%s/final.mp4." % ep_id)
        st["status"] = "final_approved"
        log_event(st, "final video approved by human (this project never uploads)")
        summary = read_json(OUTPUT / ep_id / "summary.json", {}) or {}
        with open(DATA / "history.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": ep_id, "lang": st["lang"], "date": now(), **summary}, ensure_ascii=False) + "\n")
    save(st)
    return st


CSV_COLS = ["id", "lang", "status", "next_department", "created", "updated"]


def _sync_csv(st: dict):
    f = DATA / "episodes.csv"
    rows = []
    if f.exists():
        with open(f, encoding="utf-8", newline="") as fh:
            rows = [r for r in csv.DictReader(fh) if r.get("id") != st["id"]]
    rows.append({"id": st["id"], "lang": st["lang"], "status": st["status"], "next_department": next_department(st) or "",
                 "created": st["created"], "updated": st["updated"]})
    rows.sort(key=lambda r: r["id"])
    with open(f, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_COLS)
        w.writeheader()
        w.writerows(rows)


def latest_state() -> dict | None:
    states = [read_json(p) for p in OUTPUT.glob("*/state.json")]
    states = [s for s in states if s]
    return max(states, key=lambda s: s.get("updated", "")) if states else None


def word_budget(lang: dict) -> dict:
    e = settings()["episode"]
    wpm = lang["words_per_minute"]
    target = int(wpm * e["target_minutes"])
    acts = e["acts"]
    cold = int(wpm * e["cold_open_seconds"] / 60)
    outro = int(wpm * 0.5)
    per_act = (target - cold - outro) // acts
    return {"words_per_minute": wpm, "target_words": target, "min_words": int(wpm * e["min_minutes"]),
            "max_words": int(wpm * e["max_minutes"]), "cold_open": cold, "per_act": [per_act] * acts, "outro": outro}

#!/usr/bin/env python3
"""Company state tool: the single place every agent uses to report what it is doing.

All state lives in plain JSON under company/ so it is versioned in git and can be read
by the live office page. Writes take a file lock so parallel agents don't clobber each other.

Usage (run from the repo root):
  python3 tools/company.py init
  python3 tools/company.py status
  python3 tools/company.py start  <agent> "<what I'm doing>" [--task T-001]
  python3 tools/company.py bubble <agent> "<short speech bubble>"
  python3 tools/company.py done   <agent> "<what I delivered>" [--task T-001] [--file path]
  python3 tools/company.py task new "<title>" [--owner ceo] [--project slug]
  python3 tools/company.py task set <T-001> <status> [--note "..."]     status: todo|doing|review|approved|rejected|done
  python3 tools/company.py task list [--open]
  python3 tools/company.py need add "<what the owner must do>" --from <agent> [--task T-001]
  python3 tools/company.py need done <N-001>
  python3 tools/company.py approve <T-001>          (owner approved: XP to everyone who worked on it)
  python3 tools/company.py reject  <T-001> "<why>"
  python3 tools/company.py xp <agent> <amount> "<reason>"
  python3 tools/company.py brief-data                (JSON snapshot used by /brief and /sunday-meeting)
  python3 tools/company.py office                    (render office/dist/index.html with state embedded)
"""
import argparse
import contextlib
import datetime as dt
import fcntl
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPANY = os.path.join(ROOT, "company")
CONFIG = os.path.join(COMPANY, "config.json")
ROSTER = os.path.join(COMPANY, "roster.json")
STATE = os.path.join(COMPANY, "state.json")
LOCK = os.path.join(COMPANY, ".lock")
OFFICE_SRC = os.path.join(ROOT, "office", "index.html")
OFFICE_OUT = os.path.join(ROOT, "office", "dist", "index.html")
LOG_LIMIT = 300


def now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def load(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, path)


@contextlib.contextmanager
def locked():
    with open(LOCK, "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)


def members():
    return {m["id"]: m for m in load(ROSTER)["members"]}


def level_for(xp):
    lv = load(CONFIG)["levels"][0]
    for row in load(CONFIG)["levels"]:
        if xp >= row["xp"]:
            lv = row
    return lv


def empty_state():
    return {
        "updated": now(),
        "agents": {mid: {"status": "idle", "task": None, "bubble": "", "since": now()} for mid in members()},
        "tasks": {},
        "needs_you": {},
        "log": [],
        "counters": {"task": 0, "need": 0},
    }


def get_state():
    st = load(STATE)
    if st is None:
        st = empty_state()
    for mid in members():  # new hires appear automatically
        st["agents"].setdefault(mid, {"status": "idle", "task": None, "bubble": "", "since": now()})
    return st


def log(st, agent, kind, text, task=None):
    st["log"].append({"t": now(), "agent": agent, "kind": kind, "text": text, "task": task})
    st["log"] = st["log"][-LOG_LIMIT:]


def check_agent(agent):
    if agent not in members():
        sys.exit(f"Unknown agent '{agent}'. Known: {', '.join(members())}")


def add_xp(agent, amount, reason, st):
    roster = load(ROSTER)
    for m in roster["members"]:
        if m["id"] == agent:
            before = level_for(m["xp"])["level"]
            m["xp"] = max(0, m["xp"] + amount)
            after = level_for(m["xp"])
            save(ROSTER, roster)
            log(st, agent, "xp", f"+{amount} XP: {reason}")
            if after["level"] > before:
                log(st, agent, "level-up", f"Level {after['level']} ({after['title']} / {after['title_ar']})")
            return after
    return None


# ---------------------------------------------------------------- commands

def cmd_init(a):
    with locked():
        if os.path.exists(STATE) and not a.reset:
            print("state.json already exists (use --reset to wipe it)")
            return
        save(STATE, empty_state())
    print("Company state initialised.")


def cmd_status(a):
    st, ms = get_state(), members()
    print(f"{'agent':22} {'name':8} {'lv':>3} {'status':8} task")
    for mid, m in ms.items():
        ag = st["agents"][mid]
        lv = level_for(m["xp"])
        print(f"{mid:22} {m['name']:8} {lv['level']:>3} {ag['status']:8} {ag['task'] or ''}")
    open_t = [t for t in st["tasks"].values() if t["status"] not in ("done", "approved")]
    print(f"\nOpen tasks: {len(open_t)}   Waiting on owner: {sum(1 for n in st['needs_you'].values() if not n['done'])}")


def cmd_start(a):
    check_agent(a.agent)
    with locked():
        st = get_state()
        st["agents"][a.agent] = {"status": "working", "task": a.text, "bubble": a.text[:60], "since": now(), "task_id": a.task}
        if a.task and a.task in st["tasks"]:
            t = st["tasks"][a.task]
            t["status"] = "doing" if t["status"] == "todo" else t["status"]
            if a.agent not in t["workers"]:
                t["workers"].append(a.agent)
        log(st, a.agent, "start", a.text, a.task)
        st["updated"] = now()
        save(STATE, st)
    print(f"{a.agent}: working on '{a.text}'")


def cmd_bubble(a):
    check_agent(a.agent)
    with locked():
        st = get_state()
        st["agents"][a.agent]["bubble"] = a.text[:60]
        st["updated"] = now()
        save(STATE, st)


def cmd_done(a):
    check_agent(a.agent)
    xp = load(CONFIG)["xp_rules"]["task_done"]
    with locked():
        st = get_state()
        st["agents"][a.agent] = {"status": "idle", "task": None, "bubble": "Handed to Yasmin ✓", "since": now()}
        if a.task and a.task in st["tasks"]:
            t = st["tasks"][a.task]
            if a.agent not in t["workers"]:
                t["workers"].append(a.agent)
            t["deliverables"].extend(a.file or [])
        log(st, a.agent, "done", a.text + (f" → {', '.join(a.file)}" if a.file else ""), a.task)
        add_xp(a.agent, xp, f"delivered: {a.text[:50]}", st)
        st["updated"] = now()
        save(STATE, st)
    print(f"{a.agent}: delivered '{a.text}' (+{xp} XP)")


def cmd_task(a):
    with locked():
        st = get_state()
        if a.action == "new":
            st["counters"]["task"] += 1
            tid = f"T-{st['counters']['task']:03d}"
            st["tasks"][tid] = {"id": tid, "title": a.text, "status": "todo", "owner": a.owner,
                                "project": a.project, "workers": [], "deliverables": [],
                                "notes": [], "created": now(), "updated": now()}
            log(st, a.owner, "task", f"{tid} created: {a.text}", tid)
            print(tid)
        elif a.action == "set":
            t = st["tasks"].get(a.text)
            if not t:
                sys.exit(f"No task {a.text}")
            t["status"] = a.status
            t["updated"] = now()
            if a.note:
                t["notes"].append({"t": now(), "note": a.note})
            log(st, t["owner"], "task", f"{t['id']} → {a.status}" + (f": {a.note}" if a.note else ""), t["id"])
            print(f"{t['id']} → {a.status}")
        elif a.action == "list":
            for t in st["tasks"].values():
                if a.open and t["status"] in ("done", "approved"):
                    continue
                print(f"{t['id']}  {t['status']:9} {t['title']}  [{', '.join(t['workers'])}]")
            return
        st["updated"] = now()
        save(STATE, st)


def cmd_need(a):
    with locked():
        st = get_state()
        if a.action == "add":
            st["counters"]["need"] += 1
            nid = f"N-{st['counters']['need']:03d}"
            st["needs_you"][nid] = {"id": nid, "text": a.text, "from": a.frm, "task": a.task, "done": False, "created": now()}
            log(st, a.frm, "needs-you", a.text, a.task)
            print(nid)
        else:
            n = st["needs_you"].get(a.text)
            if not n:
                sys.exit(f"No item {a.text}")
            n["done"] = True
            n["closed"] = now()
            log(st, "chief-of-staff", "needs-you", f"{a.text} done by owner")
        st["updated"] = now()
        save(STATE, st)


def _review(a, approved):
    rules = load(CONFIG)["xp_rules"]
    with locked():
        st = get_state()
        t = st["tasks"].get(a.task)
        if not t:
            sys.exit(f"No task {a.task}")
        t["status"] = "approved" if approved else "rejected"
        t["updated"] = now()
        if not approved:
            t["notes"].append({"t": now(), "note": "Owner rejected: " + a.reason})
        log(st, "ceo", "review", f"{t['id']} {'approved' if approved else 'rejected'} by owner" + ("" if approved else f": {a.reason}"), t["id"])
        amount = rules["owner_approved"] if approved else rules["owner_rejected"]
        if amount:
            for w in set(t["workers"]) | {"ceo"}:
                add_xp(w, amount, f"{t['id']} approved", st)
        for n in st["needs_you"].values():
            if n.get("task") == t["id"] and not n["done"]:
                n["done"] = True
                n["closed"] = now()
        st["updated"] = now()
        save(STATE, st)
    print(f"{a.task} {'approved' if approved else 'rejected'}")


def cmd_approve(a):
    _review(a, True)


def cmd_reject(a):
    _review(a, False)


def cmd_xp(a):
    check_agent(a.agent)
    with locked():
        st = get_state()
        lv = add_xp(a.agent, a.amount, a.reason, st)
        st["updated"] = now()
        save(STATE, st)
    print(f"{a.agent} now level {lv['level']} ({lv['title']})")


def snapshot():
    cfg, roster, st = load(CONFIG), load(ROSTER), get_state()
    for m in roster["members"]:
        lv = level_for(m["xp"])
        m["level"], m["level_title"], m["level_title_ar"] = lv["level"], lv["title"], lv["title_ar"]
        nxt = [r for r in cfg["levels"] if r["xp"] > m["xp"]]
        m["next_level_xp"] = nxt[0]["xp"] if nxt else None
    return {"generated": now(), "company": cfg["company"], "niche": cfg["niche"]["title"],
            "schedule": cfg["schedule"], "levels": cfg["levels"], "roster": roster, "state": st}


def cmd_brief_data(a):
    print(json.dumps(snapshot(), ensure_ascii=False, indent=2))


def cmd_office(a):
    with open(OFFICE_SRC, encoding="utf-8") as f:
        html = f.read()
    marker = "/*__EMBEDDED_SNAPSHOT__*/null"
    if marker not in html:
        sys.exit("office/index.html is missing the snapshot marker")
    data = json.dumps(snapshot(), ensure_ascii=False).replace("</", "<\\/")
    os.makedirs(os.path.dirname(OFFICE_OUT), exist_ok=True)
    with open(OFFICE_OUT, "w", encoding="utf-8") as f:
        f.write(html.replace(marker, data))
    print(OFFICE_OUT)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)

    s = sp.add_parser("init"); s.add_argument("--reset", action="store_true"); s.set_defaults(fn=cmd_init)
    sp.add_parser("status").set_defaults(fn=cmd_status)
    for name, fn in (("start", cmd_start), ("done", cmd_done)):
        s = sp.add_parser(name); s.add_argument("agent"); s.add_argument("text"); s.add_argument("--task")
        if name == "done":
            s.add_argument("--file", action="append")
        s.set_defaults(fn=fn)
    s = sp.add_parser("bubble"); s.add_argument("agent"); s.add_argument("text"); s.set_defaults(fn=cmd_bubble)
    s = sp.add_parser("task"); s.add_argument("action", choices=["new", "set", "list"]); s.add_argument("text", nargs="?")
    s.add_argument("status", nargs="?"); s.add_argument("--owner", default="ceo"); s.add_argument("--project")
    s.add_argument("--note"); s.add_argument("--open", action="store_true"); s.set_defaults(fn=cmd_task)
    s = sp.add_parser("need"); s.add_argument("action", choices=["add", "done"]); s.add_argument("text")
    s.add_argument("--from", dest="frm", default="chief-of-staff"); s.add_argument("--task"); s.set_defaults(fn=cmd_need)
    s = sp.add_parser("approve"); s.add_argument("task"); s.set_defaults(fn=cmd_approve)
    s = sp.add_parser("reject"); s.add_argument("task"); s.add_argument("reason"); s.set_defaults(fn=cmd_reject)
    s = sp.add_parser("xp"); s.add_argument("agent"); s.add_argument("amount", type=int); s.add_argument("reason"); s.set_defaults(fn=cmd_xp)
    sp.add_parser("brief-data").set_defaults(fn=cmd_brief_data)
    sp.add_parser("office").set_defaults(fn=cmd_office)

    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()

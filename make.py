#!/usr/bin/env python3
"""
Stickman Mystery Studio - one command for everything.

  python make.py doctor                         check your setup
  python make.py roster                         the 100 robot employees + last run status
  python make.py demo [--lang ar]               20 s rig test clip (step 2)
  python make.py episode --id E001 [--lang ar]  run the pipeline (asks for language if not given)
  python make.py review --id E001 --approve | --reject "reason" | --final-approve
  python make.py status --id E001
"""
from __future__ import annotations

import argparse
import sys

# Make Arabic/emoji print correctly on Windows terminals
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

from studio.config import StudioError, language, languages, load_env, write_json, episode_dir  # noqa: E402


def choose_language(saved: str | None = None) -> str:
    """Ask the user which language to use (only when --lang was not given)."""
    langs = languages()
    codes = list(langs)
    if saved:
        return saved
    if not sys.stdin.isatty():
        raise StudioError(f"Please choose a language with --lang ({', '.join(codes)}).")
    print("\nChoose the episode language / اختر لغة الحلقة:")
    for i, c in enumerate(codes, 1):
        print(f"  {i}) {c}  {langs[c]['name']}  ({langs[c]['english_name']})")
    while True:
        a = input(f"Number or code [1-{len(codes)}]: ").strip().lower()
        if a.isdigit() and 1 <= int(a) <= len(codes):
            return codes[int(a) - 1]
        if a in codes:
            return a
        print("  Not a valid choice, try again.")


def cmd_episode(args):
    from studio import queue as Q
    st = Q.load(args.id)
    if st and args.lang and args.lang != st["lang"]:
        raise StudioError(f"{args.id} was started in '{st['lang']}'. Use a new id for another language "
                          f"(the story is written natively, never translated).")
    lang_code = args.lang or (st and st["lang"]) or choose_language()
    lang = language(lang_code)  # validates it exists
    if not st:
        st = Q.create(args.id, lang_code)
        write_json(episode_dir(args.id) / "word_budget.json", Q.word_budget(lang))
        print(f"Created {args.id} in {lang['english_name']} ({lang['name']}).")
    print(f"{args.id}: language={lang_code}, status={st['status']}")
    dept = Q.next_department(st)
    if not dept:
        print("All departments passed. Watch output/%s/final.mp4 then run review --final-approve." % args.id)
        return
    ok, why = Q.can_start(st, dept)
    if not ok:
        print(f"⏸  Next department '{dept}' is blocked: {why}")
        return
    from studio import pipeline
    pipeline.run_department(st, dept)


def cmd_review(args):
    from studio import queue as Q
    st = Q.review(args.id, approve=args.approve, reject=args.reject, final_approve=args.final_approve)
    print(f"{args.id}: status is now {st['status']}")


def cmd_mark(args):
    from studio import queue as Q
    st = Q.mark(args.id, args.dept, args.result)
    print(f"{args.id}: {args.dept} -> {st['departments'][args.dept]['status']}; episode status {st['status']}")


def cmd_status(args):
    from studio import queue as Q
    st = Q.load(args.id)
    if not st:
        raise StudioError(f"No episode {args.id}")
    print(f"{st['id']}  lang={st['lang']}  status={st['status']}  qc_loops={st['qc_loops']}")
    for k in Q.dept_keys():
        d = st["departments"][k]
        print(f"  {k:12s} {d['status']}")


def cmd_budget(args):
    from studio import queue as Q
    st = Q.load(args.id)
    lang = language(args.lang or (st and st["lang"]) or choose_language())
    b = Q.word_budget(lang)
    if st:
        write_json(episode_dir(args.id) / "word_budget.json", b)
    print(b)


def cmd_roster(args):
    from studio import queue as Q
    st = Q.load(args.id) if args.id else Q.latest_state()
    print(f"Stickman Mystery Studio - 100 robot employees" + (f"   (last run: {st['id']}, {st['status']})" if st else "   (no runs yet)"))
    icons = {"pass": "✅", "fail": "❌"}
    for d in Q.departments():
        dstat = st["departments"][d["key"]]["status"] if st else "-"
        print(f"\n{d['order']:>2}. {d['name']}  [{dstat}]")
        roles = st["departments"][d["key"]].get("roles", {}) if st else {}
        for r in Q.roles_of(d["key"]):
            print(f"    {r['id']}  {icons.get(roles.get(r['id']), '·')}  {r['name']:<32} → {r['output']}")


def cmd_doctor(args):
    from studio import doctor
    sys.exit(0 if doctor.run() else 1)


def cmd_demo(args):
    from studio import demo
    for code in (args.lang or ["ar", "en"]):
        language(code)
        demo.build(code)


def main():
    load_env()
    p = argparse.ArgumentParser(prog="make.py", description="Stickman Mystery Studio")
    sub = p.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("episode", help="run the production pipeline for one episode")
    e.add_argument("--id", required=True)
    e.add_argument("--lang", help="language code from config/languages.yaml (asked if missing)")
    r = sub.add_parser("review", help="human gates")
    r.add_argument("--id", required=True)
    g = r.add_mutually_exclusive_group(required=True)
    g.add_argument("--approve", action="store_true", help="approve the script (review.md)")
    g.add_argument("--reject", metavar="REASON", help="send the script back with a reason")
    g.add_argument("--final-approve", action="store_true", help="approve final.mp4 (never uploads)")
    m = sub.add_parser("mark", help="(used by department heads) record a department result")
    m.add_argument("--id", required=True)
    m.add_argument("--dept", required=True)
    m.add_argument("--result", choices=["pass", "fail"], required=True)
    s = sub.add_parser("status", help="show an episode's progress")
    s.add_argument("--id", required=True)
    b = sub.add_parser("budget", help="word budget for 15 minutes in a language")
    b.add_argument("--id", default="")
    b.add_argument("--lang")
    ro = sub.add_parser("roster", help="print the 100 roles and last run status")
    ro.add_argument("--id", help="show a specific episode instead of the latest")
    sub.add_parser("doctor", help="check Python, FFmpeg, fonts, voices, keys")
    d = sub.add_parser("demo", help="render the 20 s rig test clip")
    d.add_argument("--lang", nargs="+", help="one or more language codes (default: ar en)")
    args = p.parse_args()
    handlers = {"episode": cmd_episode, "review": cmd_review, "mark": cmd_mark, "status": cmd_status,
                "budget": cmd_budget, "roster": cmd_roster, "doctor": cmd_doctor, "demo": cmd_demo}
    try:
        handlers[args.cmd](args)
    except StudioError as ex:
        print(f"\n❌ {ex}", file=sys.stderr)
        sys.exit(2)
    except KeyboardInterrupt:
        print("\nStopped. Everything finished so far is cached - run the same command to continue.")
        sys.exit(130)


if __name__ == "__main__":
    main()

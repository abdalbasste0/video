#!/usr/bin/env python3
"""Video Factory — command line.

  python main.py daemon                         always-on: Telegram bot + worker (use this on the phone)
  python main.py run "idea" [--format 16:9] [--lang en]   build one video up to PENDING_APPROVAL
  python main.py submit "idea"                  queue an idea for the running daemon (phone widget)
  python main.py status [video_id]
  python main.py decide <video_id> publish --platforms youtube,tiktok
  python main.py decide <video_id> revise --notes "warmer colors, music lower"
  python main.py decide <video_id> reject
  python main.py learn-draft "<CapCut drafts dir>/FactorySample"
  python main.py install-draft <draft.zip|folder>   (PC: import a draft built on the phone)
  python main.py doctor                         check FFmpeg, keys, CapCut paths
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

from factory.approval_bot import FactoryDaemon, owner_decide
from factory.config import load_settings
from factory.logging_setup import setup_root
from factory.orchestrator import Orchestrator
from factory.state import Store


def main() -> int:
    ap = argparse.ArgumentParser(description="Video Factory")
    ap.add_argument("--config", default=None)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("daemon")
    r = sub.add_parser("run")
    r.add_argument("idea")
    r.add_argument("--format", choices=["9:16", "16:9"])
    r.add_argument("--lang", choices=["ar", "en"])
    sq = sub.add_parser("submit", help="queue an idea for the running daemon")
    sq.add_argument("idea")
    sq.add_argument("--format", choices=["9:16", "16:9"])
    sq.add_argument("--lang", choices=["ar", "en"])
    st = sub.add_parser("status")
    st.add_argument("video_id", nargs="?")
    d = sub.add_parser("decide")
    d.add_argument("video_id")
    d.add_argument("decision", choices=["publish", "revise", "reject"])
    d.add_argument("--notes", default="")
    d.add_argument("--platforms", default="")
    ld = sub.add_parser("learn-draft")
    ld.add_argument("folder")
    inst = sub.add_parser("install-draft")
    inst.add_argument("source")
    sub.add_parser("doctor")
    args = ap.parse_args()

    s = load_settings(args.config)
    setup_root(s.root / "logs" / "factory.log")
    store = Store(s.db_path)
    orch = Orchestrator(s, store)

    if args.cmd == "daemon":
        FactoryDaemon(s, store).run_forever()
    elif args.cmd == "run":
        vid = orch.submit(args.idea, args.format, args.lang)
        print(f"video id: {vid}")
        status = orch.process(vid)
        print(f"status: {status}")
        return 0 if status == "PENDING_APPROVAL" else 1
    elif args.cmd == "submit":
        vid = orch.submit(args.idea, args.format, args.lang)
        print(f"queued {vid} — the daemon will build it and message you on Telegram")
    elif args.cmd == "status":
        if args.video_id:
            v = store.video(args.video_id)
            print(json.dumps({"video": v, "tasks": store.tasks(args.video_id),
                              "events": store.events(args.video_id, 15)}, ensure_ascii=False, indent=2, default=str))
        else:
            for v in store.videos():
                print(f"{v['id']}  {v['status']:<17} {v['title'] or v['idea'][:50]}")
    elif args.cmd == "decide":
        decision = {"publish": "APPROVE", "revise": "REVISE", "reject": "REJECT"}[args.decision]
        platforms = [p for p in args.platforms.split(",") if p]
        if decision == "APPROVE" and not platforms:
            print("--platforms is required for publish (e.g. --platforms youtube,tiktok)")
            return 2
        if decision == "APPROVE":
            ok = input(f"Type YES to publish {args.video_id} to {platforms}: ").strip()
            if ok != "YES":
                print("cancelled")
                return 1
        res = owner_decide(orch, store, s, args.video_id, decision, "cli-owner", args.notes, platforms)
        print(res)
        if res == "approved":
            print(orch.publish(args.video_id))
        elif decision == "REVISE" and res.startswith("revision"):
            print(orch.process(args.video_id))
    elif args.cmd == "learn-draft":
        from factory.capcut.inspect_draft import learn
        print(learn(Path(args.folder), s.root / "effects_library.json"))
    elif args.cmd == "install-draft":
        from factory.capcut.draft_builder import install_portable_draft
        src = Path(args.source)
        tmp = None
        if src.suffix == ".zip":
            tmp = Path(tempfile.mkdtemp())
            with zipfile.ZipFile(src) as z:
                z.extractall(tmp)
            src = next(p for p in tmp.iterdir() if p.is_dir())
        dest = install_portable_draft(src, s.drafts_dir if s.runtime == "windows" else Path(input("drafts dir: ")))
        print(f"installed → {dest}\nOpen CapCut: the draft appears on the home screen.")
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)
    elif args.cmd == "doctor":
        return doctor(s)
    return 0


def doctor(s) -> int:
    ok = True

    def line(good: bool, msg: str) -> None:
        nonlocal ok
        ok &= good
        print(("✅ " if good else "❌ ") + msg)

    print(f"runtime: {s.runtime} · render backend: {s.render_backend}")
    line(bool(shutil.which("ffmpeg")) and bool(shutil.which("ffprobe")), "ffmpeg + ffprobe on PATH")
    for k in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_OWNER_ID"):
        line(bool(s.env(k)), f"{k} set in .env")
    print(("✅ " if s.env("ANTHROPIC_API_KEY") else "⚠️ ") + "ANTHROPIC_API_KEY (optional: real scripts)")
    print(("✅ " if s.env("PEXELS_API_KEY") else "⚠️ ") + "PEXELS_API_KEY (optional: stock footage)")
    try:
        import edge_tts  # noqa: F401
        print("✅ edge-tts installed")
    except ImportError:
        print("⚠️ edge-tts missing → silent timing track")
    if s.runtime == "windows":
        line(s.drafts_dir.exists(), f"CapCut drafts dir: {s.drafts_dir}")
    else:
        print(f"ℹ️ drafts are written to {s.drafts_dir} and zipped (copy to PC: main.py install-draft)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

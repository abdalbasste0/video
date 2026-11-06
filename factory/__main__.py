"""Factory command line.

  python -m factory app                 # the private app (control panel) + runs the factory — the desktop shortcut opens this
  python -m factory serve               # runs permanently: work starts every day at 08:00
  python -m factory run [--now]         # one workday (--now starts immediately)
  python -m factory command "..."       # send an instruction to bot 9 (the manager)
  python -m factory status              # today's status
  python -m factory approve <stage> [n] # approve (research/script/final_review); n = idea number
  python -m factory reject <stage> "notes"
  python -m factory publish [--late]    # manual publish (still requires final approval)
"""
from __future__ import annotations

import argparse
import sys
import time
from datetime import timedelta
from pathlib import Path

from .approval import push_command, record_decision
from .config import WORK_START, settings
from .state import Job, current_job

ROOT_DIR = Path(__file__).resolve().parent.parent

STAGE_ALIASES = {"final": "final_review", "idea": "research", "ideas": "research", "video": "final_review"}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="factory", description="مصنع فيديوهات ستيك مان والغموض والألغاز")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="تشغيل يوم عمل واحد")
    r.add_argument("--now", action="store_true", help="ابدأ فوراً بدل انتظار الساعة 8")
    sub.add_parser("serve", help="تشغيل دائم: يبدأ العمل يومياً الساعة 8 صباحاً")
    ap_app = sub.add_parser("app", help="التطبيق الخاص: لوحة التحكم + تشغيل المصنع")
    ap_app.add_argument("--no-browser", action="store_true", help="لا تفتح المتصفح تلقائياً")
    sub.add_parser("shortcut", help="أنشئ اختصاراً على سطح المكتب")
    c = sub.add_parser("command", help="أرسل تعليمات للبوت التاسع")
    c.add_argument("text")
    sub.add_parser("status")
    a = sub.add_parser("approve")
    a.add_argument("stage")
    a.add_argument("value", nargs="?", default="")
    j = sub.add_parser("reject")
    j.add_argument("stage")
    j.add_argument("note", nargs="?", default="")
    p = sub.add_parser("publish")
    p.add_argument("--late", action="store_true", help="انشر حتى لو تجاوزنا الساعة 13:00")
    p.add_argument("--platforms", default="", help="youtube,tiktok,instagram (الافتراضي: كل المنصات المفعلة)")
    args = ap.parse_args(argv)

    if args.cmd in ("approve", "reject"):
        stage = STAGE_ALIASES.get(args.stage, args.stage)
        job = current_job()
        if args.cmd == "approve":
            record_decision(job, stage, "approved", value=args.value)
        else:
            record_decision(job, stage, "rejected", note=args.note)
        print(f"تم تسجيل القرار على {stage}.")
        return 0

    if args.cmd == "command":
        push_command(args.text)
        print("تم إرسال التعليمات للبوت التاسع (سيقرؤها خلال ثوان إن كان المصنع يعمل).")
        return 0

    if args.cmd == "app":
        err_file = ROOT_DIR / "workspace" / "app-error.txt"
        try:
            err_file.unlink(missing_ok=True)
            from .app.server import serve
            serve(open_browser=not args.no_browser)
        except Exception:
            import traceback
            err_file.parent.mkdir(parents=True, exist_ok=True)
            err_file.write_text(traceback.format_exc(), encoding="utf-8")
            raise
        return 0

    if args.cmd == "shortcut":
        import runpy
        from .config import ROOT
        runpy.run_path(str(ROOT / "scripts" / "install_shortcut.py"), run_name="__main__")
        return 0

    from .bots.manager import Manager

    if args.cmd == "status":
        print(Manager().status_text(current_job()))
        return 0

    if args.cmd == "publish":
        m = Manager()
        m.job = current_job()
        plats = [x.strip() for x in args.platforms.split(",") if x.strip()] or None
        res = m.publish(m.job, allow_late=args.late, platforms=plats)
        print(res or "لم يتم النشر.")
        return 0

    if args.cmd == "run":
        Manager().run_day(start_now=args.now)
        return 0

    if args.cmd == "serve":
        while True:
            Manager().run_day()
            # Wait until shortly before 8:00 tomorrow
            tomorrow = settings.at(WORK_START, settings.now().date() + timedelta(days=1)) - timedelta(minutes=5)
            while settings.now() < tomorrow:
                time.sleep(30)
    return 0


if __name__ == "__main__":
    sys.exit(main())

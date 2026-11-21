"""مصنع الفيديوهات - نقطة التشغيل.

  python run_factory.py                 لوحة التحكم (حاسوب + موبايل) + بوت تيليجرام
  python run_factory.py make "موضوع"    فيديو واحد من سطر الأوامر
  python run_factory.py auto -n 3       المصنع يختار 3 مواضيع بنفسه
  python run_factory.py demo            تجربة كاملة بدون مفتاح API
  python run_factory.py demo --story    تجربة نوع «القصة» (لقطات سريعة + رسوم ستيك مان)
  python run_factory.py plan plan.json  فيديو من سكريبت/ستوري بورد جاهز (العمّال اللي ليهم نتيجة جاهزة بيتخطّوا)
"""
import json
import argparse
import sys
import time

from factory import media
from factory.pipeline import get_factory


def wait(ids):
    f = get_factory()
    last = {}
    while True:
        jobs = [f.jobs[i] for i in ids]
        for j in jobs:
            line = f"{j['status']} · {j.get('current') or ''}"
            if last.get(j["id"]) != line:
                print(f"[{j['id']}] {line}", flush=True)
                last[j["id"]] = line
        if all(j["status"] in ("done", "error") for j in jobs):
            break
        time.sleep(1)
    for j in jobs:
        print(f"\n== {j['id']}: {j['status']}")
        if j.get("error"):
            print("   ", j["error"])
        for p in j.get("publish", []):
            print(f"   {'OK ' if p['ok'] else 'ERR'} {p['connector']}: {p['msg']}")
    return 0 if all(j["status"] == "done" for j in jobs) else 1


def main():
    ap = argparse.ArgumentParser(description="مصنع الفيديوهات")
    sub = ap.add_subparsers(dest="cmd")
    d = sub.add_parser("dashboard")
    d.add_argument("--port", type=int, default=8765)
    d.add_argument("--local-only", action="store_true", help="اقفل الوصول من الموبايل")
    m = sub.add_parser("make")
    m.add_argument("topics", nargs="+")
    a = sub.add_parser("auto")
    a.add_argument("-n", type=int, default=1)
    dm = sub.add_parser("demo")
    dm.add_argument("--story", action="store_true", help="تجربة نوع القصة")
    pl = sub.add_parser("plan")
    pl.add_argument("path")
    args = ap.parse_args()

    if not media.have_ffmpeg():
        sys.exit("❌ ffmpeg مش متسطب. حمّله من https://ffmpeg.org وحطه في PATH.")

    if args.cmd in (None, "dashboard"):
        from dashboard import serve
        serve(host="127.0.0.1" if getattr(args, "local_only", False) else "0.0.0.0", port=getattr(args, "port", 8765))
    elif args.cmd == "make":
        sys.exit(wait([get_factory().submit(t) for t in args.topics]))
    elif args.cmd == "auto":
        sys.exit(wait([get_factory().submit(None) for _ in range(args.n)]))
    elif args.cmd == "plan":
        with open(args.path, encoding="utf-8") as f:
            plan = json.load(f)
        sys.exit(wait([get_factory().submit(plan.get("topic"), plan=plan)]))
    elif args.cmd == "demo" and args.story:
        from factory.demo import STORY_PLAN
        plan = json.loads(json.dumps(STORY_PLAN))
        plan["settings"].setdefault("voice", {})["provider"] = "silent"  # no voice service needed for the demo
        sys.exit(wait([get_factory().submit(plan["topic"], plan=plan)]))
    elif args.cmd == "demo":
        sys.exit(wait([get_factory().submit("ليه الكيبورد مترتب QWERTY؟", demo=True)]))


if __name__ == "__main__":
    main()

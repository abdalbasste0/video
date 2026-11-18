"""Upload every entry of schedule/schedule.json as a private, scheduled YouTube video (skips ones already uploaded)."""
import json
import os

from .youtube import upload, ROOT


def main():
    plan = json.load(open(os.path.join(ROOT, "schedule", "schedule.json")))
    log = os.path.join(ROOT, "schedule", "uploads.jsonl")
    done = set()
    if os.path.exists(log):
        for line in open(log):
            d = json.loads(line)
            done.add((os.path.relpath(d["folder"], ROOT) if os.path.isabs(d["folder"]) else d["folder"], d["short"]))
    for item in plan:
        key = (item["folder"], bool(item.get("short")))
        if key in done:
            print("skip (already uploaded):", key)
            continue
        folder = os.path.join(ROOT, item["folder"])
        if not os.path.exists(os.path.join(folder, "short.mp4" if item.get("short") else "video.mp4")):
            print("missing, render it first:", key)
            continue
        upload(item["folder"], item["publish_at"], bool(item.get("short")))


if __name__ == "__main__":
    main()

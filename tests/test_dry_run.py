"""Full test run with no paid API calls (FACTORY_DRY_RUN=1).

Runs the workday as if it were 08:00 and approves automatically like the owner would, then checks
that a video was produced, passed QA, and was "published" (simulated) only after approval.
"""
import os
import shutil
import tempfile
import threading
import time
from pathlib import Path

os.environ["FACTORY_DRY_RUN"] = "1"
os.environ["FACTORY_FAKE_NOW"] = os.environ.get("FAKE_NOW", "08:00")
os.environ.pop("TELEGRAM_BOT_TOKEN", None)

from factory import config  # noqa: E402

config.settings.workspace = Path(tempfile.mkdtemp(prefix="factory_test_"))
import factory.approval as approval  # noqa: E402
approval.INBOX = config.settings.workspace / "inbox"

from factory.approval import push_command, read_decision, record_decision  # noqa: E402
from factory.bots.manager import Manager  # noqa: E402
from factory.state import Job  # noqa: E402


def owner(job_day_dir_ready: threading.Event, stop: threading.Event):
    """Simulates the owner: chooses idea 2, asks for one script change, then approves the final video."""
    script_round = 0
    while not stop.is_set():
        job = Job()
        st = job.data["stages"]
        for stage, decision in (("research", ("approved", "2", "")),
                                ("script", None),
                                ("final_review", ("approved", "", ""))):
            if st.get(stage, {}).get("approval") == "pending" and not read_decision(job, stage):
                if stage == "script":
                    script_round += 1
                    decision = ("rejected", "", "اجعل الخطاف أقوى") if script_round == 1 else ("approved", "", "")
                record_decision(job, stage, *decision, by="test-owner")
        time.sleep(0.3)


def test_full_day():
    push_command("اليوم أريد قصة غموض")
    m = Manager()
    stop = threading.Event()
    t = threading.Thread(target=owner, args=(threading.Event(), stop), daemon=True)
    t.start()
    m.run_day(start_now=True)
    stop.set()

    job = Job()
    assert job.brief.get("category") == "mystery", job.brief
    from factory.state import history
    assert history()[-1]["urls"]["youtube"].endswith("DRY_RUN")
    assert job.brief.get("script_feedback") == "اجعل الخطاف أقوى"
    assert job.get("chosen_idea")["title"] == job.get("ideas")[1]["title"]
    video = Path(job.get("video")["path"])
    assert video.exists() and video.stat().st_size > 10_000
    assert Path(job.get("video")["thumbnail"]).exists()
    assert job.get("qa_report")["passed"], job.get("qa_report")
    pub = job.get("published")
    assert set(pub) == {"youtube", "tiktok", "instagram"} and all(r["id"] == "DRY_RUN" for r in pub.values()), pub
    assert Path(job.get("video")["vertical"]).exists()
    print("OK:", video, job.get("video"))
    print(m.status_text(job))


def test_publish_requires_approval():
    m = Manager()
    job = Job()
    (job.dir / "approvals" / "final_review.json").unlink(missing_ok=True)
    job.put("published", None)
    try:
        m.publish(job)
    except PermissionError:
        return
    raise AssertionError("published without approval!")


if __name__ == "__main__":
    try:
        test_full_day()
        test_publish_requires_approval()
        print("ALL TESTS PASSED")
    finally:
        if os.environ.get("KEEP") != "1":
            shutil.rmtree(config.settings.workspace, ignore_errors=True)
        else:
            print("workspace:", config.settings.workspace)

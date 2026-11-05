"""The golden rule: nothing is published without the owner's explicit approval.

Run:  python -m pytest -q tests      (or: python tests/test_golden_rule.py)
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from factory.agents.base import AgentContext                      # noqa: E402
from factory.agents.publisher_agent import NotApproved, PublisherAgent, assert_owner_approval  # noqa: E402
from factory.approval_bot import owner_decide                       # noqa: E402
from factory.config import load_settings                            # noqa: E402
from factory.orchestrator import Orchestrator                       # noqa: E402
from factory.project import Project                                 # noqa: E402
from factory.state import Store                                     # noqa: E402

OWNER = "123456789"


def setup():
    os.environ["TELEGRAM_OWNER_ID"] = OWNER
    os.environ["TELEGRAM_BOT_TOKEN"] = ""          # never talk to Telegram in tests
    s = load_settings()
    tmp = Path(tempfile.mkdtemp())
    s.raw["runtime"]["projects_dir"] = str(tmp / "projects")
    store = Store(tmp / "t.db")
    orch = Orchestrator(s, store)
    vid = orch.submit("test idea", "9:16", "en")
    p = Project.open(s.projects_dir, vid)
    p.final_file.write_bytes(b"fake video v1")
    p.write_json("script", "script.json", {"title": "t", "description": "", "hashtags": []})
    return s, store, orch, vid, p


def pending(store, vid):
    store._exec("UPDATE videos SET status='PENDING_APPROVAL' WHERE id=?", (vid,))


def test_publish_refused_without_any_decision():
    s, store, orch, vid, p = setup()
    pending(store, vid)
    try:
        orch.publish(vid)
        raise AssertionError("published without approval!")
    except NotApproved:
        pass
    assert store.video(vid)["status"] == "PENDING_APPROVAL"


def test_status_cannot_jump_to_approved_or_published():
    s, store, orch, vid, p = setup()
    for st in ("APPROVED", "PUBLISHING", "PUBLISHED"):
        try:
            store.set_video_status(vid, st)
            raise AssertionError(f"entered {st} without approval")
        except PermissionError:
            pass


def test_non_owner_approval_is_refused():
    s, store, orch, vid, p = setup()
    pending(store, vid)
    from factory import media
    store.record_decision(vid, "APPROVE", "999", render_sha256=media.sha256(p.final_file), platforms=["youtube"])
    try:
        assert_owner_approval(store, s, vid, p.final_file)
        raise AssertionError("stranger approval accepted")
    except NotApproved:
        pass


def test_changed_file_after_approval_is_refused():
    s, store, orch, vid, p = setup()
    pending(store, vid)
    assert owner_decide(orch, store, s, vid, "APPROVE", OWNER, platforms=["tiktok"]) == "approved"
    p.final_file.write_bytes(b"different video v2")
    try:
        assert_owner_approval(store, s, vid, p.final_file)
        raise AssertionError("approval reused for a different file")
    except NotApproved:
        pass


def test_owner_approval_allows_publish():
    s, store, orch, vid, p = setup()
    pending(store, vid)
    assert owner_decide(orch, store, s, vid, "APPROVE", OWNER, platforms=["tiktok"]) == "approved"
    res = PublisherAgent(AgentContext(s, store, p, store.video(vid))).run()
    assert store.video(vid)["status"] == "PUBLISHED"
    assert "tiktok" in res


def test_reject_and_revise_never_publish():
    s, store, orch, vid, p = setup()
    pending(store, vid)
    owner_decide(orch, store, s, vid, "REJECT", OWNER)
    assert store.video(vid)["status"] == "REJECTED"
    try:
        orch.publish(vid)
        raise AssertionError("rejected video published")
    except NotApproved:
        pass
    s, store, orch, vid, p = setup()
    pending(store, vid)
    owner_decide(orch, store, s, vid, "REVISE", OWNER, notes="make the colors warmer")
    assert store.video(vid)["status"] == "REVISING"


def test_decision_only_when_pending():
    s, store, orch, vid, p = setup()     # status QUEUED
    assert owner_decide(orch, store, s, vid, "APPROVE", OWNER, platforms=["youtube"]) != "approved"


def test_revision_routing_only_to_responsible_agent():
    s, store, orch, vid, p = setup()
    os.environ.pop("ANTHROPIC_API_KEY", None)
    assert orch.route_notes("الألوان باهتة، اجعلها أدفأ") == ["colorist"]
    assert orch.route_notes("music is too loud") == ["sound"]
    assert orch.route_notes("bigger captions please") == ["motion"]
    pending(store, vid)
    for a in ["script", "voice", "assets", "editor", "motion", "colorist", "vfx", "sound", "draft",
              "qa_draft", "render", "qa_export", "approval"]:
        store.set_task(vid, a, "DONE")
    orch.revise(vid, "warmer colors")
    status = {t["agent"]: t["status"] for t in store.tasks(vid)}
    assert status["script"] == status["voice"] == status["assets"] == status["motion"] == "DONE"
    assert status["colorist"] == status["render"] == status["approval"] == "PENDING"
    assert store.video(vid)["meta"]["overrides"]["colorist"]["temperature"] > 0


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("✓", name)

"""Department order and human review gates (uses a throw-away episode id)."""
import shutil

import pytest

from studio import queue
from studio.config import OUTPUT, StudioError

EP = "TEST_GATES"


@pytest.fixture(autouse=True)
def clean():
    shutil.rmtree(OUTPUT / EP, ignore_errors=True)
    yield
    shutil.rmtree(OUTPUT / EP, ignore_errors=True)
    # remove the test row from data/episodes.csv
    import csv
    from studio.config import DATA
    f = DATA / "episodes.csv"
    rows = [r for r in csv.DictReader(open(f, encoding="utf-8")) if r["id"] != EP]
    with open(f, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=queue.CSV_COLS)
        w.writeheader()
        w.writerows(rows)


def _report(dept, result="PASS"):
    p = OUTPUT / EP / "reports" / f"{dept}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(f"| {r['id']} | {r['name']} | {result} | - |" for r in queue.roles_of(dept)), encoding="utf-8")


def test_departments_run_in_order_and_stop_for_review():
    queue.create(EP, "ar")
    with pytest.raises(StudioError):
        queue.mark(EP, "script", "pass")          # Story Room has not passed yet
    for d in ["story_room", "characters", "script", "fact_logic"]:
        _report(d)
        queue.mark(EP, d, "pass")
    st = queue.load(EP)
    assert st["status"] == "needs_review"
    ok, why = queue.can_start(st, "storyboard")
    assert not ok and "approval" in why            # nothing renders until approved
    queue.review(EP, approve=True)
    assert queue.can_start(queue.load(EP), "storyboard")[0]


def test_cannot_pass_with_failed_roles():
    queue.create(EP, "en")
    _report("story_room", "FAIL")
    with pytest.raises(StudioError):
        queue.mark(EP, "story_room", "pass")


def test_reject_sends_script_back():
    queue.create(EP, "en")
    for d in ["story_room", "characters", "script", "fact_logic"]:
        _report(d)
        queue.mark(EP, d, "pass")
    st = queue.review(EP, reject="ending is too obvious")
    assert st["status"] == "rejected" and st["departments"]["script"]["status"] == "pending"

"""Tests: helpers 7/8 join a late bot, and owner replies are parsed correctly."""
import os
import tempfile
import threading
import time
from datetime import timedelta
from pathlib import Path

os.environ["FACTORY_DRY_RUN"] = "1"
from factory import config  # noqa: E402

config.settings.workspace = Path(tempfile.mkdtemp(prefix="factory_test_"))

from factory.approval import parse_reply  # noqa: E402
from factory.bots.base import ProductionBot  # noqa: E402
from factory.bots.manager import Manager  # noqa: E402
from factory.state import Job  # noqa: E402


class SlowBot(ProductionBot):
    name = "slow_bot"
    stage = "media"

    def plan(self, job):
        return [{"n": i} for i in range(9)]

    def work(self, job, unit):
        time.sleep(0.3)
        return threading.current_thread().name


def test_helpers_join_when_late():
    m, job, bot = Manager(), Job(), SlowBot()
    t = threading.Thread(target=bot.run, args=(job,), name="slow_bot")
    t.start()
    time.sleep(0.1)
    now = config.settings.now()
    # The stage started 10 minutes ago and its deadline is in 1 minute → it is clearly late
    m._supervise(job, bot, now - timedelta(minutes=10), now + timedelta(minutes=1), force=False)
    t.join()
    workers = set(bot.board.results.values())
    assert {"slow_bot", "bot7_helper", "bot8_helper"} <= workers, workers


def test_no_helpers_when_on_time():
    m, job, bot = Manager(), Job(), SlowBot()
    t = threading.Thread(target=bot.run, args=(job,), name="slow_bot")
    t.start()
    time.sleep(0.1)
    now = config.settings.now()
    m._supervise(job, bot, now, now + timedelta(hours=1), force=False)
    t.join()
    assert set(bot.board.results.values()) == {"slow_bot"}


def test_parse_reply():
    assert parse_reply("موافق 2") == ("approved", "2", "")
    assert parse_reply("3") == ("approved", "3", "")
    assert parse_reply("رفض: البداية ضعيفة")[0:3:2] == ("rejected", "البداية ضعيفة")
    assert parse_reply("انشر") == ("approved", "", "")
    assert parse_reply("كيف الحال؟") is None


def test_keyword_commands():
    from factory.bots.manager import _keyword_command as k
    assert k("توقف").action == "pause"
    assert k("استمر").action == "resume"
    assert k("استئناف").action == "resume"
    # Words like "توقف" ("stop") inside a normal question must not pause the factory
    assert k("لماذا توقف المصنع من الليلة الماضية؟").action != "pause"
    assert k("ابدأ الآن").action == "start_now"


if __name__ == "__main__":
    test_keyword_commands()
    test_helpers_join_when_late()
    test_no_helpers_when_on_time()
    test_parse_reply()
    print("ALL TESTS PASSED")

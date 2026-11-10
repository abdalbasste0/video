"""
Runs one department for an episode.

Step 1-2 of the build plan: departments are not wired yet. Each department will
be run by its head agent (.claude/agents/<department>.md) through `claude -p`,
followed by automatic checks. This file is where that happens (build step 3).
"""
from __future__ import annotations

from .config import StudioError

BUILT: dict = {}  # department key -> function(state) ; filled in during build step 3


def run_department(st: dict, dept: str):
    fn = BUILT.get(dept)
    if not fn:
        raise StudioError(
            f"Department '{dept}' is not built yet (it comes in build step 3).\n"
            f"Episode {st['id']} is saved with language '{st['lang']}' - nothing was lost.\n"
            f"Try the rig test now:  python make.py demo --lang {st['lang']}")
    fn(st)

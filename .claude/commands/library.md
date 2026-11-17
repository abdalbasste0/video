---
description: Run the GitHub skills library now (normally part of the Sunday meeting).
argument-hint: [focus, e.g. "better hooks" or an employee id]
---

Call the `skills-librarian` agent (Jood) with this focus: **$ARGUMENTS** (if empty: the problems in the latest `company/meetings/*.md`).
When she's done, show the owner her proposals in Arabic (one line each: skill, for whom, source, risk) and how to approve: `/approve skill:<agent>/<name>`.
Then `python3 tools/company.py office`, commit and push.

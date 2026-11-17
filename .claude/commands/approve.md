---
description: Owner approves or rejects a task, a needs-you item or a library skill. Gives XP to the team.
argument-hint: <T-001 | N-001 | skill:<agent>/<repo-or-name>> [reject: reason]
---

The owner says: **$ARGUMENTS**

- `T-xxx` → `python3 tools/company.py approve T-xxx` (or `reject T-xxx "<reason>"` if the owner wrote "reject" / "رفض" plus a reason). On reject, as Yasmin, send the reason to the employees who worked on it and redo the work.
- `N-xxx` → `python3 tools/company.py need done N-xxx`.
- `skill:<agent>/<name>` → as Jood (skills-librarian), adopt that skill from the latest `company/library/*.md` report following her "After the owner approves a skill" steps.

Then `python3 tools/company.py office`, commit with message "approve $ARGUMENTS" and push. Confirm to the owner in one Arabic line, including any level-ups.

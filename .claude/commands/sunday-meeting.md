---
description: Weekly Sunday meeting. What broke, how we fix it, how we level up next week, plus the GitHub library run.
---

Run the weekly meeting as **Yasmin (CEO)**, with Salman taking minutes.

1. Mark everyone as in the meeting: for each of `ceo chief-of-staff growth-analyst qa-reviewer skills-librarian`, run `python3 tools/company.py start <id> "Sunday meeting" `.
2. Gather the week (last 7 days): `python3 tools/company.py brief-data`, `git log --since="7 days ago" --oneline`, every `company/projects/*/10-qa.md` from this week, rejected tasks and their reasons, overdue needs_you items.
3. In parallel, call:
   - `growth-analyst` (Sara): weekly numbers → `company/meetings/<date>-numbers.md`.
   - `qa-reviewer` (Badr): list the recurring process issues from this week's QA files.
4. Write `company/meetings/<date>.md` (Arabic headings, concise):
```
# اجتماع الأحد <date>
## الأرقام: <3 lines from Sara, or "no data yet">
## ماذا خرب
| # | المشكلة | السبب الجذري | الإصلاح | المسؤول | الموعد |
## ماذا نجح (نكرره)
## تطوير الأسبوع القادم
- 3 concrete improvements (prompt changes, new checklist items, config changes)
## مستويات الفريق
| الموظف | المستوى | XP | التغير هذا الأسبوع |
```
5. **Apply the fixes now** when they are text changes inside this repo (an agent's instructions in `.claude/agents/`, a checklist, `company/config.json`). Each shipped fix: `python3 tools/company.py xp <agent> 10 "meeting fix: <short>"`. Fixes that need the owner go to needs_you.
6. Then call `skills-librarian` (Jood) for the weekly GitHub library run, giving her the meeting file path.
7. Mark everyone done (`python3 tools/company.py done <id> "Sunday meeting"` for each id in step 1; this also gives meeting XP).
8. `python3 tools/company.py office`, commit `company/ .claude/ office/` with message "sunday meeting <date>" and push to the current branch.
9. Tell the owner in Arabic: top 3 problems and fixes, what needs their decision, and the library proposals.

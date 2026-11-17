---
description: Morning brief (8:00). Exactly what the owner needs to do today.
---

Run the morning brief as **Salman (chief-of-staff)**, for Yasmin.

1. `python3 tools/company.py start chief-of-staff "Writing the morning brief"`
2. `python3 tools/company.py brief-data` and read: open tasks, needs_you items not done, the last 24h of the log, level-ups, `company/config.json` (owner timezone, posting windows).
3. Today's date in the owner's timezone (`schedule.owner_timezone`). Use `TZ=<tz> date` in Bash.
4. Write `company/briefs/YYYY-MM-DD.md` in Arabic with this exact layout:

```
# ملخص صباح <day name, date>

## مهامك اليوم
- [ ] <action>, <file to open>  (from needs_you, most urgent first; max 5)

## ينتظر موافقتك (<count>)
- <item>, from <employee name>, <T-id>

## ماذا أنجز الفريق أمس
- <employee>: <one line>  (max 6 lines)

## مواعيد النشر اليوم
| المنصة | نيويورك | باريس | توقيتك |
(from publish plans of approved projects; "لا يوجد" if none)

## خطة الفريق اليوم
- <what Yasmin will run today, e.g. "Short #N: trends at 09:00">

## ترقيات 🏆
- <name> reached Lv <n> (<title_ar>)  (only if any in the last 24h)
```
5. If there are no open items, write it anyway and say the team will start today's short.
6. `python3 tools/company.py done chief-of-staff "Morning brief ready" --file company/briefs/<date>.md`
7. `python3 tools/company.py office`, then commit (`company/ office/`) with message "brief <date>" and push to the current branch.
8. Print the brief to the owner.

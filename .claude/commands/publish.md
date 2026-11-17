---
description: Schedule an approved project on YouTube, TikTok, Instagram and Facebook through the connected scheduler.
argument-hint: <project-folder-name>
---

Project: **$ARGUMENTS** (folder `company/projects/$ARGUMENTS/`).

1. Check the project's task is `approved` (`python3 tools/company.py task list`). If it isn't, stop and tell the owner to run `/approve <T-id>` first.
2. `python3 tools/company.py start publisher "Scheduling $ARGUMENTS"`
3. Read `07-publish-plan.md` and `10-qa.md` (must say PASS).
4. Publishing needs the video files at a public URL and a connected scheduler. Use the Metricool connector if it is connected (look it up with ToolSearch "metricool"): `getBrandSettings` to confirm the YouTube, TikTok, Instagram and Facebook accounts are linked, then `createScheduledPost` per platform with the times from the plan. If the files are not hosted yet, or the connector or an account is missing, don't work around it: add a needs_you item saying exactly what to connect or upload, and give the owner the ready-to-paste caption per platform instead.
5. `python3 tools/company.py done publisher "Scheduled $ARGUMENTS" --file company/projects/$ARGUMENTS/07-publish-plan.md`, append the scheduled times and post links to the plan, `python3 tools/company.py office`, commit and push.
6. Tell the owner in Arabic what was scheduled where and when (New York / Paris / owner time).

---
description: Show the team status and refresh the live office page.
---

1. `python3 tools/company.py status` and show it to the owner as a short Arabic table (name, role, level, working / idle, current task).
2. `python3 tools/company.py office` to rebuild `office/dist/index.html`.
3. If this session has the Artifact tool and the office was published before (URL in `company/office_url.txt`), republish `office/dist/index.html` to that URL. Otherwise tell the owner they can open `office/dist/index.html` in a browser, or run `python3 -m http.server -d . 8080` and open http://localhost:8080/office/ for the live version that refreshes every 5 seconds.

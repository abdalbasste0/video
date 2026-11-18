#!/usr/bin/env bash
# Render several story files one after another: scripts/render_queue.sh <story.json>...
cd "$(dirname "$0")/.."
for f in "$@"; do
  python3 -m studio.render "$f" --vertical 2>&1 | grep -E "wrote|Error|Traceback"
done

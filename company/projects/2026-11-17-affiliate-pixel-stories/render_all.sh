#!/bin/bash
# Render all 10 stories (16:9 + 9:16). Usage: bash render_all.sh [id ...]
cd "$(dirname "$0")/../../.."
P=company/projects/2026-11-17-affiliate-pixel-stories
ids=${@:-elevenlabs fireflies lovable descript kit webflow heygen hubspot synthesia speechify}
for id in $ids; do
  vo=""; [ -f $P/audio/$id.mp3 ] && vo="--voiceover $P/audio/$id.mp3"
  vs=""; [ -f $P/audio/${id}_short.mp3 ] && vs="--voiceover-vertical $P/audio/${id}_short.mp3"
  python3 tools/pixel_story/build.py $P/stories/$id.json $P/renders/$id $vo $vs 2>&1 | grep -E "OUT|Error|error" || echo "FAILED $id"
done

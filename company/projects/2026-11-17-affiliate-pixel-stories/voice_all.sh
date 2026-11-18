#!/bin/bash
# Natural Sofia voice (Chatterbox, Voicebox engine) for all 10 stories, then render.
# Needs CHATTERBOX_DIR and PY (python with onnxruntime, tokenizers, soundfile).
cd "$(dirname "$0")/../../.."
P=company/projects/2026-11-17-affiliate-pixel-stories
for id in ${@:-webflow kit hubspot fireflies elevenlabs lovable heygen synthesia speechify descript}; do
  $PY -I tools/pixel_story/voice_chatterbox.py $P/stories/$id.json $P/renders/$id 2>/dev/null \
  && python3 tools/pixel_story/build.py $P/renders/$id/voiced_story.json $P/renders/$id --voiceover $P/renders/$id/vo_full.wav --voiceover-vertical $P/renders/$id/vo_short.wav 2>&1 | grep -E "OUT|rror" \
  || echo "FAILED $id"
done

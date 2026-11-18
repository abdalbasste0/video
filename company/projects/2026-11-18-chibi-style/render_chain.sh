#!/bin/bash
# Render each chibi video as soon as its Chatterbox voice is ready. Needs WHISPER_DIR.
cd "$(dirname "$0")/../../.."
V=company/projects/2026-11-17-affiliate-pixel-stories/renders
C=company/projects/2026-11-18-chibi-style
for id in ${@:-kit hubspot fireflies elevenlabs lovable heygen synthesia speechify descript}; do
  until python3 -c "import json,os,sys;d=json.load(open('$V/$id/voiced_story.json'));sys.exit(0 if 'chatterbox' in d.get('voice',{}).get('engine','') and os.path.getmtime('$V/$id/vo_short.wav')>=os.path.getmtime('$V/$id/voiced_story.json')-5 else 1)" 2>/dev/null; do sleep 30; done
  python3 tools/chibi/build.py $C/chibi/$id.chibi.json $V/$id $C/renders/$id 2>&1 | grep -E "OUT|rror" || echo "FAILED $id"
done

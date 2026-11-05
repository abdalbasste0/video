#!/data/data/com.termux/files/usr/bin/bash
# Home-screen button: type an idea → queued → you get it on Telegram for approval.
cd "$HOME/video" || exit 1
IDEA=$(termux-dialog text -t "💡 فكرة الفيديو / Video idea" | python -c "import sys,json;print(json.load(sys.stdin).get('text',''))")
[ -z "$IDEA" ] && exit 0
FMT=$(termux-dialog radio -t "Format" -v "9:16 (Shorts/Reels/TikTok),16:9 (YouTube)" | python -c "import sys,json;t=json.load(sys.stdin).get('text','');print('16:9' if t.startswith('16') else '9:16')")
python main.py submit "$IDEA" --format "$FMT"
bash "$HOME/video/phone/start_forever.sh" >/dev/null 2>&1 &
termux-toast "✅ Queued — you'll get it on Telegram"

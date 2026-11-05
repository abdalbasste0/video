#!/data/data/com.termux/files/usr/bin/bash
cd "$HOME/video" || exit 1
python main.py status
echo; echo "Heartbeat: $(cat heartbeat.txt 2>/dev/null || echo 'not running')"
tail -n 5 logs/watchdog.log 2>/dev/null
read -r -p "Press Enter to close"

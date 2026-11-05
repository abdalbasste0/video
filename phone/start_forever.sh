#!/data/data/com.termux/files/usr/bin/bash
# Keeps the factory alive: wake-lock, auto-restart on crash, restart on hang (stale heartbeat).
APP="$HOME/video"
cd "$APP" || exit 1
mkdir -p logs
PIDFILE="$APP/logs/watchdog.pid"
if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  echo "Video Factory is already running (pid $(cat "$PIDFILE"))."
  exit 0
fi
echo $$ > "$PIDFILE"
command -v termux-wake-lock >/dev/null && termux-wake-lock
command -v termux-notification >/dev/null && termux-notification --id vf --ongoing \
  --title "🎬 Video Factory" --content "Running — waiting for ideas on Telegram" \
  --button1 "Stop" --button1-action "bash $APP/phone/stop.sh"
export AIOHTTP_NO_EXTENSIONS=1 MULTIDICT_NO_EXTENSIONS=1 YARL_NO_EXTENSIONS=1 FROZENLIST_NO_EXTENSIONS=1
trap 'kill $CHILD 2>/dev/null; rm -f "$PIDFILE"; exit 0' TERM INT

while true; do
  echo "[$(date)] starting daemon" >> logs/watchdog.log
  python main.py daemon >> logs/daemon.log 2>&1 &
  CHILD=$!
  echo $CHILD > logs/daemon.pid
  while kill -0 $CHILD 2>/dev/null; do
    sleep 60
    # heartbeat is written every 15 s; older than 5 min = hung → restart
    if [ -f heartbeat.txt ] && [ $(( $(date +%s) - $(stat -c %Y heartbeat.txt) )) -gt 300 ]; then
      echo "[$(date)] heartbeat stale → restarting" >> logs/watchdog.log
      kill $CHILD; sleep 5; kill -9 $CHILD 2>/dev/null
    fi
  done
  echo "[$(date)] daemon exited → restart in 10 s" >> logs/watchdog.log
  sleep 10
done

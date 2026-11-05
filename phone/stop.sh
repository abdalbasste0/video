#!/data/data/com.termux/files/usr/bin/bash
APP="$HOME/video"
[ -f "$APP/logs/watchdog.pid" ] && kill "$(cat "$APP/logs/watchdog.pid")" 2>/dev/null
[ -f "$APP/logs/daemon.pid" ] && kill "$(cat "$APP/logs/daemon.pid")" 2>/dev/null
rm -f "$APP/logs/watchdog.pid"
command -v termux-notification-remove >/dev/null && termux-notification-remove vf
command -v termux-wake-unlock >/dev/null && termux-wake-unlock
echo "Video Factory stopped. (Pending videos stay pending — nothing is published.)"

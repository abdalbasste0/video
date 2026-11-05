#!/data/data/com.termux/files/usr/bin/bash
# Home-screen button: start the always-on factory in the background.
nohup bash "$HOME/video/phone/start_forever.sh" >/dev/null 2>&1 &
command -v termux-toast >/dev/null && termux-toast "🎬 Video Factory started"

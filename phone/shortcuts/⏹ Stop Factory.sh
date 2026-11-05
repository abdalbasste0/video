#!/data/data/com.termux/files/usr/bin/bash
bash "$HOME/video/phone/stop.sh"
command -v termux-toast >/dev/null && termux-toast "⏹ Video Factory stopped"

#!/data/data/com.termux/files/usr/bin/bash
# Termux:Boot → starts the factory automatically after the phone reboots.
termux-wake-lock
sleep 20   # let the network come up
bash "$HOME/video/phone/start_forever.sh" >/dev/null 2>&1 &

#!/bin/bash
# Make an email-size copy (< 9.5 MB) of one video: 720p (or 720x1280 vertical), bitrate from duration.
# usage: bash tools/chibi/email_copy.sh IN.mp4 OUT.mp4
set -e
d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$1")
w=$(ffprobe -v error -select_streams v:0 -show_entries stream=width -of csv=p=0 "$1")
vb=$(python3 -c "print(int(min(2500e3, 9.2e6*8/$d - 64e3)/1000))")
[ "$w" -gt 1100 ] && sc="scale=1280:720" || sc="scale=720:1280"
ffmpeg -y -hide_banner -loglevel error -i "$1" -vf "$sc:flags=lanczos" -c:v libx264 -preset medium -b:v ${vb}k -maxrate $((vb*3/2))k -bufsize $((vb*3))k \
  -pix_fmt yuv420p -c:a aac -b:a 64k -ac 1 -movflags +faststart "$2"

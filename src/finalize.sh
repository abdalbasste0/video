#!/bin/bash
# Mux soundtrack, burn subtitles, export final 1080p MP4s.
set -e
cd /home/user/video
ffmpeg -y -v error -i build/video_silent.mp4 -i build/soundtrack.wav \
  -vf "subtitles=build/subs.ass" -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -movflags +faststart -shortest out/vanished_at_sea_1080p.mp4
ffmpeg -y -v error -i build/video_silent.mp4 -i build/soundtrack.wav \
  -c:v copy -c:a aac -b:a 192k -movflags +faststart -shortest out/vanished_at_sea_1080p_nosubs.mp4

#!/bin/bash
# Compress a product's 16:9 + 9:16 videos so both fit in one email (< 24 MB total).
# usage: bash tools/chibi/deliver.sh RENDER_DIR OUT_DIR NAME
set -e
R=$1; O=$2; N=$3; mkdir -p $O
dl=$(ffprobe -v error -show_entries format=duration -of csv=p=0 $R/landscape_16x9.mp4)
dv=$(ffprobe -v error -show_entries format=duration -of csv=p=0 $R/vertical_9x16.mp4)
# 23 MB budget shared by total seconds, minus 96 kb/s audio
vb=$(python3 -c "print(int((23e6*8/($dl+$dv) - 96e3)/1000))")
for k in landscape_16x9 vertical_9x16; do
  ffmpeg -y -hide_banner -loglevel error -i $R/$k.mp4 -c:v libx264 -preset slow -b:v ${vb}k -maxrate $((vb*2))k -bufsize $((vb*4))k \
    -pix_fmt yuv420p -c:a aac -b:a 96k -movflags +faststart $O/${N}_${k}.mp4
done
du -ch $O/${N}_*.mp4 | tail -1

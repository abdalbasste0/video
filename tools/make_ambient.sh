#!/usr/bin/env bash
# Generates an original, royalty-free soft ambient loop (Am - F - C - G pads) into assets/music/.
# Usage: bash tools/make_ambient.sh
set -e
OUT="$(dirname "$0")/../assets/music/soft-ambient-pad.mp3"
chord() { # $1..$3 = frequencies, 8 seconds, soft attack/release
  echo "0.18*sin(2*PI*$1*t)+0.14*sin(2*PI*$2*t)+0.12*sin(2*PI*$3*t)+0.05*sin(2*PI*$1*2.003*t)"
}
EXPR_A=$(chord 220.00 261.63 329.63)   # Am
EXPR_F=$(chord 174.61 220.00 261.63)   # F
EXPR_C=$(chord 196.00 261.63 329.63)   # C/G
EXPR_G=$(chord 196.00 246.94 293.66)   # G
TMP=$(mktemp -d)
i=0
for E in "$EXPR_A" "$EXPR_F" "$EXPR_C" "$EXPR_G"; do
  ffmpeg -v error -y -f lavfi -i "aevalsrc='$E':s=44100:d=8" -af "afade=t=in:d=1.5,afade=t=out:st=6.2:d=1.8,tremolo=f=0.25:d=0.25" "$TMP/c$i.wav"
  i=$((i+1))
done
printf "file '%s'\n" "$TMP"/c0.wav "$TMP"/c1.wav "$TMP"/c2.wav "$TMP"/c3.wav > "$TMP/list.txt"
ffmpeg -v error -y -f concat -safe 0 -i "$TMP/list.txt" -af "lowpass=f=1800,aecho=0.8:0.7:120|260:0.25|0.18,volume=0.9,aformat=channel_layouts=stereo" -b:a 160k "$OUT"
rm -rf "$TMP"
echo "wrote $OUT"

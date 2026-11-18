#!/usr/bin/env bash
# Installs dependencies and downloads the Kokoro voice model (~350 MB).
set -e
cd "$(dirname "$0")"
pip install -q -r requirements.txt
command -v ffmpeg >/dev/null || apt-get install -y -q ffmpeg
python3 -c "import skia" 2>/dev/null || apt-get install -y -q libegl1 libgl1
mkdir -p models
B=https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0
[ -f models/kokoro-v1.0.onnx ] || curl -sSL -o models/kokoro-v1.0.onnx $B/kokoro-v1.0.onnx
[ -f models/voices-v1.0.bin ] || curl -sSL -o models/voices-v1.0.bin $B/voices-v1.0.bin
echo "ready"

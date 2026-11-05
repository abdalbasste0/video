#!/bin/bash
# ============================================================
#  Video Factory - one file for Mac
#  First run: installs everything + creates the desktop icon.
#  After that: updates the project and opens the app.
# ============================================================
REPO="https://github.com/abdalbasste0/video.git"
BRANCH="claude/automated-story-video-factory-uvvyxr"
DIR="$HOME/VideoFactory"

command -v git >/dev/null || { echo "Installing developer tools (git)..."; xcode-select --install; echo "Run this file again when it finishes."; read -r; exit; }
command -v python3 >/dev/null || { echo "Install Python from python.org, then run this file again."; open "https://www.python.org/downloads/"; read -r; exit; }
if ! command -v ffmpeg >/dev/null; then
  if command -v brew >/dev/null; then brew install ffmpeg; else
    echo "Install Homebrew from brew.sh, then run this file again."; open "https://brew.sh"; read -r; exit; fi
fi

if [ ! -d "$DIR/.git" ]; then
  echo "Downloading the project..."
  git clone --branch "$BRANCH" "$REPO" "$DIR" || { echo "Download failed."; read -r; exit 1; }
  cd "$DIR" && python3 -m pip install --upgrade -r requirements.txt && python3 -m factory shortcut
else
  cd "$DIR" && git pull --ff-only && python3 -m pip install -q -r requirements.txt
fi
echo "Opening the Video Factory app..."
python3 -m factory app

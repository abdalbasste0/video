#!/bin/bash
# ============================================================
#  Video Factory - one file for Mac
#  First run: installs everything + creates the desktop icon.
#  After that: updates the project and opens the app.
# ============================================================
REPO="https://github.com/abdalbasste0/video.git"
BRANCH="claude/automated-story-video-factory-uvvyxr"
DIR="$HOME/VideoFactory"

command -v git >/dev/null || { echo "جارٍ تثبيت أدوات المطور (git)..."; xcode-select --install; echo "افتح هذا الملف مرة ثانية بعد انتهاء التثبيت."; read -r; exit; }
command -v python3 >/dev/null || { echo "ثبّت Python من موقع python.org ثم افتح هذا الملف مرة ثانية."; open "https://www.python.org/downloads/"; read -r; exit; }
if ! command -v ffmpeg >/dev/null; then
  if command -v brew >/dev/null; then brew install ffmpeg; else
    echo "ثبّت Homebrew من موقع brew.sh ثم افتح هذا الملف مرة ثانية."; open "https://brew.sh"; read -r; exit; fi
fi

if [ ! -d "$DIR/.git" ]; then
  echo "جارٍ تحميل المشروع..."
  git clone --branch "$BRANCH" "$REPO" "$DIR" || { echo "فشل التحميل. تأكد من تسجيل الدخول إلى GitHub."; read -r; exit 1; }
  cd "$DIR" && python3 -m pip install --upgrade -r requirements.txt && python3 -m factory shortcut
else
  cd "$DIR" && git pull --ff-only && python3 -m pip install -q -r requirements.txt
fi
echo "جارٍ فتح تطبيق مصنع الفيديو..."
python3 -m factory app

@echo off
REM ============================================================
REM  Video Factory - one file for Windows
REM  First run: installs everything + creates the desktop icon.
REM  After that: updates the project and opens the app.
REM ============================================================
setlocal
set "REPO=https://github.com/abdalbasste0/video.git"
set "BRANCH=claude/automated-story-video-factory-uvvyxr"
set "DIR=%USERPROFILE%\VideoFactory"
title مصنع الفيديو

set MISSING=0
where git >nul 2>nul || (echo [*] جارٍ تثبيت Git... & winget install -e --id Git.Git --accept-package-agreements --accept-source-agreements & set MISSING=1)
where python >nul 2>nul || (echo [*] جارٍ تثبيت Python... & winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements & set MISSING=1)
where ffmpeg >nul 2>nul || (echo [*] جارٍ تثبيت FFmpeg... & winget install -e --id Gyan.FFmpeg --accept-package-agreements --accept-source-agreements & set MISSING=1)
if "%MISSING%"=="1" (
  echo.
  echo [!] تم تثبيت البرامج المطلوبة. أغلق هذه النافذة وافتح الملف مرة ثانية.
  pause
  exit /b
)

if not exist "%DIR%\.git" (
  echo [*] جارٍ تحميل المشروع...
  git clone --branch "%BRANCH%" "%REPO%" "%DIR%" || (echo [x] فشل التحميل. تأكد من تسجيل الدخول إلى GitHub. & pause & exit /b 1)
  cd /d "%DIR%"
  python -m pip install --upgrade -r requirements.txt || (echo [x] فشل تثبيت المكتبات. & pause & exit /b 1)
  python -m factory shortcut
) else (
  cd /d "%DIR%"
  echo [*] جارٍ التحقق من التحديثات...
  git pull --ff-only
  python -m pip install -q -r requirements.txt
)

echo [*] جارٍ فتح تطبيق مصنع الفيديو...
start "" pythonw -m factory app
exit /b

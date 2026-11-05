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
title Video Factory

set MISSING=0
where git >nul 2>nul || (echo [*] Installing Git... & winget install -e --id Git.Git --accept-package-agreements --accept-source-agreements & set MISSING=1)
where python >nul 2>nul || (echo [*] Installing Python... & winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements & set MISSING=1)
where ffmpeg >nul 2>nul || (echo [*] Installing FFmpeg... & winget install -e --id Gyan.FFmpeg --accept-package-agreements --accept-source-agreements & set MISSING=1)
if "%MISSING%"=="1" (
  echo.
  echo [!] Required programs were installed. Close this window and double-click this file again.
  pause
  exit /b
)

if not exist "%DIR%\.git" (
  echo [*] Downloading the project...
  git clone --branch "%BRANCH%" "%REPO%" "%DIR%" || (echo [x] Download failed. Make sure you are signed in to GitHub. & pause & exit /b 1)
  cd /d "%DIR%"
  python -m pip install --upgrade -r requirements.txt || (echo [x] Failed to install the libraries. & pause & exit /b 1)
  python -m factory shortcut
) else (
  cd /d "%DIR%"
  echo [*] Checking for updates...
  git pull --ff-only
  python -m pip install -q -r requirements.txt
)

echo [*] Opening the Video Factory app...
start "" pythonw -m factory app
exit /b

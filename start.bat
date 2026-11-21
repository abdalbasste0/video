@echo off
REM Video Factory launcher for Windows: double-click this file.
cd /d "%~dp0"
title Video Factory

REM ---- find Python (the "py" launcher first, then "python") ----
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (
  where python >nul 2>nul && python -c "import sys" >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo.
  echo [X] Python is not installed.
  echo     Open PowerShell and run:   winget install Python.Python.3.12
  echo     Or download it from https://www.python.org/downloads/  ^(tick "Add python.exe to PATH"^)
  echo     Then close this window and double-click start.bat again.
  pause
  exit /b 1
)

REM ---- ffmpeg is needed to build the videos ----
where ffmpeg >nul 2>nul
if errorlevel 1 (
  echo.
  echo [X] ffmpeg is not installed.
  echo     Open PowerShell and run:   winget install Gyan.FFmpeg
  echo     Then RESTART the computer ^(or sign out and in^) and double-click start.bat again.
  pause
  exit /b 1
)

REM ---- private Python environment + libraries (first run takes a few minutes) ----
if not exist ".venv\Scripts\python.exe" (
  echo Creating the Python environment...
  %PY% -m venv .venv
  if errorlevel 1 ( echo [X] Could not create the environment. & pause & exit /b 1 )
)
echo Installing / checking libraries...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r requirements.txt
if errorlevel 1 (
  echo [X] Installing the libraries failed. Check your internet connection and try again.
  pause
  exit /b 1
)

echo.
echo ==============================================
echo   Video Factory is starting...
echo   Dashboard:  http://localhost:8765
echo   Keep this window open while you work.
echo ==============================================
start "" http://localhost:8765
".venv\Scripts\python.exe" run_factory.py
pause

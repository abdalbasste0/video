@echo off
cd /d "%~dp0\.."
set /p IDEA="Video idea: "
python main.py submit "%IDEA%"
pause

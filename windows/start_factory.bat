@echo off
REM Always-on Video Factory for Windows: restarts automatically if it ever exits.
cd /d "%~dp0\.."
if not exist logs mkdir logs
:loop
echo [%date% %time%] starting daemon >> logs\watchdog.log
python main.py daemon >> logs\daemon.log 2>&1
echo [%date% %time%] daemon exited, restarting in 10s >> logs\watchdog.log
timeout /t 10 /nobreak > nul
goto loop

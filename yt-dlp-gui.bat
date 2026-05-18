@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "PATH=%PATH%;C:\yt-dlp;C:\Users\MadSrei\.deno\bin"
cd /d "%SCRIPT_DIR%"
python main.py
if errorlevel 1 (
    echo.
    echo Error: Failed to start the application.
    echo Make sure Python is installed and in PATH.
    pause
)

@echo off
setlocal
set "SCRIPT_DIR=%~dp0"

:: Check for portable Python first
if exist "%SCRIPT_DIR%portable_env\python.exe" (
    set "PYTHON=%SCRIPT_DIR%portable_env\python.exe"
    set "PATH=%SCRIPT_DIR%portable_env\bin;%SCRIPT_DIR%portable_env;%PATH%"
) else (
    set "PYTHON=python"
    set "PATH=%PATH%;C:\yt-dlp;%USERPROFILE%\.deno\bin"
)

cd /d "%SCRIPT_DIR%"
%PYTHON% main.py
if errorlevel 1 (
    echo.
    echo Error: Failed to start the application.
    if not exist "%SCRIPT_DIR%portable_env\python.exe" (
        echo Python not found. Run setup_portable.py to install a portable environment.
    )
    pause
)

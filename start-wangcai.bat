@echo off
REM WangCai Toolkit - One-Click Startup
REM This .bat launches the PowerShell script with execution policy bypassed

set "SCRIPT_DIR=%~dp0"
powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%SCRIPT_DIR%start-wangcai.ps1"

REM If the script exits immediately, keep the window open to show errors
if errorlevel 1 (
    echo.
    echo Script exited with error. Press any key to close...
    pause >nul
)

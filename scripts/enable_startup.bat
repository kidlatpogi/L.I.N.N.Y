@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0\.."

echo ================================================
echo    Enabling L.I.N.N.Y. for Windows Startup
echo ================================================
echo.

python -c "from linny.system.startup import StartupManager; print('[OK] Startup Registry Enabled' if StartupManager.enable_startup() else '[ERROR] Failed to enable startup')"

echo.
pause
endlocal

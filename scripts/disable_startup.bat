@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0\.."

echo ================================================
echo    Disabling L.I.N.N.Y. Windows Startup
echo ================================================
echo.

python -c "from linny.system.startup import StartupManager; print('[OK] Startup Registry Disabled' if StartupManager.disable_startup() else '[ERROR] Failed to disable startup')"

echo.
pause
endlocal

@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo ================================================
echo    Disabling L.I.N.N.Y. Windows Startup
echo ================================================
echo.

REM Remove registry entry
python -c "from linny.system.startup import StartupManager; StartupManager.disable_startup()"

REM Remove from startup folder if any old files exist
set "StartupFolder=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
if exist "%StartupFolder%\linny*.bat" del "%StartupFolder%\linny*.bat" /q >nul 2>&1
if exist "%StartupFolder%\*LINNY*.bat" del "%StartupFolder%\*LINNY*.bat" /q >nul 2>&1

echo [OK] Startup registration successfully removed.
echo.
pause
endlocal

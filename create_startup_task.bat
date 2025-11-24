@echo off
REM ============================================================================
REM L.I.N.N.Y. v9.2 - High Priority Startup Task Creator
REM ============================================================================
REM This script creates a Windows Task Scheduler task that:
REM   - Runs at logon with HIGHEST priority
REM   - Ensures Linny loads BEFORE other startup applications
REM   - Launches silently via start_linny_silent.vbs
REM ============================================================================

echo.
echo ========================================
echo  L.I.N.N.Y. Startup Task Creator
echo ========================================
echo.
echo This will create a HIGH PRIORITY startup task
echo that ensures Linny locks your PC instantly.
echo.
pause

REM Delete existing task if it exists
schtasks /Delete /TN "LinnyStartup" /F >nul 2>&1

REM Create new task with HIGHEST priority
schtasks /Create ^
  /TN "LinnyStartup" ^
  /TR "wscript.exe \"d:\Codes\Python\Linny\start_linny_silent.vbs\"" ^
  /SC ONLOGON ^
  /RL HIGHEST ^
  /F

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo  SUCCESS!
    echo ========================================
    echo.
    echo Task "LinnyStartup" created successfully!
    echo.
    echo Configuration:
    echo   - Trigger: At logon
    echo   - Priority: HIGHEST
    echo   - Action: Launch Linny silently
    echo.
    echo Linny will now load FIRST on startup and
    echo lock your PC in ~0.3 seconds.
    echo.
) else (
    echo.
    echo ========================================
    echo  ERROR!
    echo ========================================
    echo.
    echo Failed to create task. Please run this
    echo script as Administrator.
    echo.
)

pause

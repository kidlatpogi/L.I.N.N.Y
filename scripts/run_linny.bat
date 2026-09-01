@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0\.."

echo Starting L.I.N.N.Y. Voice Assistant...
python -m linny.main %*
endlocal

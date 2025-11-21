@echo off
REM L.I.N.N.Y. 3.0 - Headless Startup Script
REM This script starts L.I.N.N.Y. in headless mode with fake lock feature

REM Hide this CMD window
if not DEFINED IS_MINIMIZED set IS_MINIMIZED=1 && start "" /min "%~dpnx0" %* && exit

cd /d "d:\Codes\Python\Linny"
start /min pythonw.exe linny_app.py --startup

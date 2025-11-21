Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c ""cd /d d:\Codes\Python\Linny && pythonw.exe linny_app.py --startup""", 0, False
Set WshShell = Nothing

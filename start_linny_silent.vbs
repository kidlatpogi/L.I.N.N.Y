' L.I.N.N.Y. v9.2 - High Priority Silent Launcher
' Launches Linny with HIGH process priority using PowerShell
Set WshShell = CreateObject("WScript.Shell")

' Use PowerShell to set process priority to High
WshShell.Run "powershell.exe -WindowStyle Hidden -Command ""Start-Process -FilePath 'pythonw.exe' -ArgumentList 'd:\Codes\Python\Linny\linny_app.py --startup' -WindowStyle Hidden -Priority High""", 0, False

Set WshShell = Nothing

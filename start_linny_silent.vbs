' ============================================================================
' L.I.N.N.Y. v9.4 - Silent Startup Launcher
' ============================================================================
' This VBScript launches Linny silently (no console window) with high priority
' Designed for Windows Task Scheduler startup tasks
' ============================================================================

Set WshShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Define paths
strScriptPath = objFSO.GetParentFolderName(WScript.ScriptFullName)
strPythonScript = strScriptPath & "\linny_app.py"

' Check if Python script exists
If Not objFSO.FileExists(strPythonScript) Then
    MsgBox "Error: linny_app.py not found at " & strPythonScript, vbCritical, "L.I.N.N.Y. Startup Error"
    WScript.Quit 1
End If

' Launch Python script silently with --startup flag
' WindowStyle 0 = Hidden window
' WaitOnReturn False = Don't wait for completion
strCommand = "pythonw.exe """ & strPythonScript & """ --startup"
WshShell.Run strCommand, 0, False

' Optional: Set process priority to HIGH (requires additional steps)
' Note: Priority is set within linny_app.py using psutil

WScript.Quit 0

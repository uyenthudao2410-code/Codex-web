Option Explicit

Dim shell, fileSystem, powershellPath, supervisorPath, command, exitCode
Set shell = CreateObject("WScript.Shell")
Set fileSystem = CreateObject("Scripting.FileSystemObject")

powershellPath = fileSystem.BuildPath(shell.ExpandEnvironmentStrings("%SystemRoot%"), "System32\WindowsPowerShell\v1.0\powershell.exe")
supervisorPath = fileSystem.BuildPath(fileSystem.GetParentFolderName(WScript.ScriptFullName), "recovery-supervisor.ps1")
command = """" & powershellPath & """ -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File """ & supervisorPath & """ -Action Run"

exitCode = shell.Run(command, 0, True)
WScript.Quit exitCode

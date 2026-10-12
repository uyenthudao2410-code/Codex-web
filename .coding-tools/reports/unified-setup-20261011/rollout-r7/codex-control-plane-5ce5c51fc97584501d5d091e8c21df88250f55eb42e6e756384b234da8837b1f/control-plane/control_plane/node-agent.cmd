@echo off
setlocal DisableDelayedExpansion

rem Installed control-plane node entrypoint. The caller only supplies the
rem subcommand/config arguments; this file fixes Python, Electron, app root,
rem and packaged mode to the same signed installation tree.
set "ADAPTER_ROOT=%~dp0"
for %%I in ("%ADAPTER_ROOT%..") do set "RUNTIME_RESOURCES=%%~fI"
for %%I in ("%RUNTIME_RESOURCES%\..") do set "RUNTIME_CONTENTS=%%~fI"
for %%I in ("%RUNTIME_CONTENTS%\..") do set "INSTALL_ROOT=%%~fI"
set "PYTHON_EXE=%RUNTIME_RESOURCES%\native-python\python.exe"
set "ELECTRON_EXE=%INSTALL_ROOT%\Coding Tools MCP.exe"

if not exist "%PYTHON_EXE%" (
  echo CONTROL_PLANE_NODE_PYTHON_MISSING 1>&2
  exit /b 87
)
if not exist "%ELECTRON_EXE%" (
  echo CONTROL_PLANE_NODE_ELECTRON_MISSING 1>&2
  exit /b 87
)

"%PYTHON_EXE%" -I "%ADAPTER_ROOT%node_agent.py" %* --project-root "%INSTALL_ROOT%" --node "%ELECTRON_EXE%" --runtime-mode packaged
exit /b %ERRORLEVEL%

@echo off
setlocal EnableExtensions
title Coding Tools MCP - Connector Bootstrap Identity Fix

echo ============================================================
echo Coding Tools MCP - Connector Bootstrap Identity Fix
echo ============================================================
echo.

set "REPO=E:\Github\Tools-Codex-web"
set "BRANCH=fix/activation-self-recovery-20260828"
set "PATCHER=%TEMP%\connector-bootstrap-identity-local-fix.py"

if not exist "%REPO%\package.json" (
  echo [ERROR] Repository not found: %REPO%
  goto :fail
)

cd /d "%REPO%"
if errorlevel 1 goto :fail

where git.exe >nul 2>nul
if errorlevel 1 (
  echo [ERROR] git.exe not found in PATH.
  goto :fail
)
where python.exe >nul 2>nul
if errorlevel 1 (
  echo [ERROR] python.exe not found in PATH.
  goto :fail
)
where npm.cmd >nul 2>nul
if errorlevel 1 (
  echo [ERROR] npm.cmd not found in PATH.
  goto :fail
)

echo [1/4] Fetching exact recovery candidate...
git fetch origin "%BRANCH%"
if errorlevel 1 goto :fail

echo.
echo [2/4] Materializing identity patcher...
git show FETCH_HEAD:scripts/connector-bootstrap-identity-local-fix.py > "%PATCHER%"
if errorlevel 1 goto :fail
python -m py_compile "%PATCHER%"
if errorlevel 1 (
  echo [ERROR] Recovery patcher syntax check failed.
  goto :fail
)

echo.
echo [3/4] Applying narrow identity fix and focused proof...
python "%PATCHER%"
if errorlevel 1 (
  echo.
  echo [ERROR] Identity fix proof failed. Target scope was rolled back.
  goto :pause_fail
)

echo.
echo [4/4] Loading proved source with repository-native refresh...
call npm run dev:refresh
if errorlevel 1 (
  echo.
  echo [ERROR] dev:refresh failed after identity proof PASS.
  echo The proved source changes were intentionally retained.
  goto :pause_fail
)

echo.
call npm run dev:status
set "STATUS_RC=%ERRORLEVEL%"

echo.
echo ============================================================
if "%STATUS_RC%"=="0" (
  echo [SUCCESS] CONNECTOR_BOOTSTRAP_IDENTITY_FIX_LOADED
) else (
  echo [WARN] Refresh succeeded but dev:status returned %STATUS_RC%.
)
echo ============================================================
echo Return to ChatGPT for live workspace/admission verification.
echo.
pause
exit /b %STATUS_RC%

:fail
echo.
echo [ERROR] Wrapper failed before a proved source refresh.
:pause_fail
echo.
echo Do NOT run git reset or git clean.
pause
exit /b 1

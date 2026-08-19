@echo off
setlocal
set "REPO=E:\Github\Tools-Codex-web"
set "OUT=%REPO%\tests\p4_eval_pack\p4_readiness_diagnostic.txt"

cd /d "%REPO%"
if errorlevel 1 (
  echo [P4-DIAG] ERROR: cannot enter repo: %REPO%
  pause
  exit /b 1
)

> "%OUT%" echo ==================== P4 READINESS DIAGNOSTIC ====================
>> "%OUT%" echo Timestamp: %date% %time%
>> "%OUT%" echo Repo: %REPO%
>> "%OUT%" echo.

>> "%OUT%" echo ==================== CANONICAL READINESS ====================
python resources\coding-tools-mcp\scripts\report_p4_readiness.py --workspace . >> "%OUT%" 2>&1
>> "%OUT%" echo [exit_code=%errorlevel%]
>> "%OUT%" echo.

>> "%OUT%" echo ==================== CURRENT LEDGER BASELINE ====================
python resources\coding-tools-mcp\scripts\report_current_ledger_baseline.py --workspace . >> "%OUT%" 2>&1
>> "%OUT%" echo [exit_code=%errorlevel%]
>> "%OUT%" echo.

>> "%OUT%" echo ==================== REWORK BASELINE ====================
python resources\coding-tools-mcp\scripts\report_rework_baseline.py --workspace . >> "%OUT%" 2>&1
>> "%OUT%" echo [exit_code=%errorlevel%]
>> "%OUT%" echo.

>> "%OUT%" echo ==================== CURRENT-CONFIG EVAL REPORT ====================
if exist tests\p4_eval_pack\p4_eval_current_config_report.json (
  type tests\p4_eval_pack\p4_eval_current_config_report.json >> "%OUT%"
) else (
  echo [missing] tests\p4_eval_pack\p4_eval_current_config_report.json >> "%OUT%"
)
>> "%OUT%" echo.

echo.
echo [P4-DIAG] Wrote:
echo %OUT%
echo.
type "%OUT%"
echo.
echo [P4-DIAG] Done. Copy the output or send p4_readiness_diagnostic.txt to ChatGPT.
pause
endlocal

@echo off
setlocal
cd /d E:\Github\Tools-Codex-web
if errorlevel 1 (
  echo [ERROR] Cannot open E:\Github\Tools-Codex-web
  pause
  exit /b 1
)

echo [P4] Running current-config evaluation...
python tests\p4_eval_pack\run_p4_eval_current_config.py --repo-root "E:\Github\Tools-Codex-web" --require-reporter
set RC=%ERRORLEVEL%

echo.
if %RC%==0 (
  echo [P4] PASS - report: E:\Github\Tools-Codex-web\tests\p4_eval_pack\p4_eval_current_config_report.json
) else (
  echo [P4] FAIL - exit code %RC%
)

echo.
pause
exit /b %RC%

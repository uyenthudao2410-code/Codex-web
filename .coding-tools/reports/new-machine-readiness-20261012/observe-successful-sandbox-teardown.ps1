$ErrorActionPreference = 'Stop'
$taskReceipt = [ordered]@{ operation='observe_successful_sandbox_teardown'; observed_at=[DateTimeOffset]::UtcNow.ToString('o'); mutated=$false }
try {
  $taskRaw = @(& "$env:SystemRoot\System32\hcsdiag.exe" list -raw 2>&1)
  if ($LASTEXITCODE -ne 0) { throw 'HCS_CENSUS_FAILED' }
  $taskReceipt.compute_systems = (($taskRaw -join "`n") | ConvertFrom-Json)
  $taskProcess = Get-CimInstance Win32_Process -Filter 'ProcessId=41744'
  $taskReceipt.process = if ($null -ne $taskProcess) { [ordered]@{ pid=$taskProcess.ProcessId; name=$taskProcess.Name; creation_date=$taskProcess.CreationDate; command_line=$taskProcess.CommandLine; parent_pid=$taskProcess.ParentProcessId } } else { $null }
  $taskReceipt.ok=$true
} catch { $taskReceipt.ok=$false; $taskReceipt.code=$_.Exception.Message }
$taskReceipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath 'E:\DEV\Codex-web\.coding-tools\reports\new-machine-readiness-20261012\successful-sandbox-teardown-observation.json' -Encoding UTF8

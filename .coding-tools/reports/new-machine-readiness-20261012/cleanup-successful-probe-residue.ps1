$ErrorActionPreference = 'Stop'
$taskVmId = 'b96e61fb-9f42-4a74-8361-aa02c95ed242'
$taskPid = 41744
$taskStartUtc = ([DateTimeOffset]'2026-10-12T09:27:17.220+07:00').UtcDateTime
$taskReceipt = [ordered]@{ operation='cleanup_exact_successful_probe_residue'; observed_at=[DateTimeOffset]::UtcNow.ToString('o'); vm_id=$taskVmId; pid=$taskPid; ok=$false; mutated=$false }
try {
  $taskProcess = Get-Process -Id $taskPid -ErrorAction SilentlyContinue
  if ($null -eq $taskProcess) { $taskReceipt.ok=$true; $taskReceipt.state='OWNED_PROCESS_ALREADY_EXITED' }
  else {
    if ($taskProcess.ProcessName -ne 'vmmemWindowsSandbox' -or [math]::Abs(($taskProcess.StartTime.ToUniversalTime()-$taskStartUtc).TotalMilliseconds) -gt 2) { throw 'OWNED_PROCESS_IDENTITY_CHANGED' }
    $taskRaw = @(& "$env:SystemRoot\System32\hcsdiag.exe" list -raw 2>&1)
    if ($LASTEXITCODE -ne 0) { throw 'HCS_CENSUS_FAILED' }
    $taskSystems = (($taskRaw -join "`n") | ConvertFrom-Json).value
    $taskTarget = @($taskSystems | Where-Object { $_.Id -eq $taskVmId })
    if ($taskTarget.Count -ne 1 -or $taskTarget[0].Owner -ne 'WindowsSandbox' -or $taskTarget[0].State -ne 'Running') { throw 'OWNED_RUNNING_VM_NOT_VERIFIED' }
    $taskEvent = Get-WinEvent -FilterHashtable @{ LogName='System'; ProviderName='Microsoft-Windows-Hyper-V-VmSwitch'; StartTime=$taskStartUtc.ToLocalTime().AddSeconds(-1); EndTime=$taskStartUtc.ToLocalTime().AddSeconds(10) } | Where-Object { $_.ToXml() -match [regex]::Escape($taskVmId) }
    if (@($taskEvent).Count -lt 1) { throw 'OWNED_VM_START_EVENT_NOT_VERIFIED' }
    $taskFresh = Get-Process -Id $taskPid -ErrorAction Stop
    if ($taskFresh.ProcessName -ne 'vmmemWindowsSandbox' -or [math]::Abs(($taskFresh.StartTime.ToUniversalTime()-$taskStartUtc).TotalMilliseconds) -gt 2) { throw 'OWNED_PROCESS_IDENTITY_CHANGED' }
    $taskKill = @(& "$env:SystemRoot\System32\hcsdiag.exe" kill $taskVmId 2>&1)
    if ($LASTEXITCODE -ne 0) { throw 'EXACT_VM_SHUTDOWN_FAILED' }
    $taskReceipt.mutated=$true
    $taskDeadline = [DateTimeOffset]::UtcNow.AddSeconds(45)
    do { Start-Sleep -Milliseconds 500; $taskProcess = Get-Process -Id $taskPid -ErrorAction SilentlyContinue } while ($null -ne $taskProcess -and [DateTimeOffset]::UtcNow -lt $taskDeadline)
    if ($null -ne $taskProcess) { throw 'OWNED_PROCESS_EXIT_NOT_OBSERVED' }
    $taskReceipt.ok=$true; $taskReceipt.state='EXACT_OWNED_VM_STOPPED'
  }
} catch { $taskReceipt.error_code=$_.Exception.Message }
$taskReceipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath 'E:\DEV\Codex-web\.coding-tools\reports\new-machine-readiness-20261012\successful-probe-residue-cleanup-receipt.json' -Encoding UTF8

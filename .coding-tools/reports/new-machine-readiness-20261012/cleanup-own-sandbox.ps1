[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$taskReportRoot = 'E:\DEV\Codex-web\.coding-tools\reports\new-machine-readiness-20261012'
$taskVmId = 'DD55131F-FC1E-479E-8300-E8979D0555EF'
$taskVmProcessId = 37240
$taskVmStartedAtUtc = ([DateTimeOffset]'2026-10-12T02:07:07.745Z').UtcDateTime
$taskReceipt = [ordered]@{ operation='cleanup_owned_failed_sandbox_probe'; vm_id=$taskVmId; observed_at=[DateTimeOffset]::UtcNow.ToString('o'); mutated=$false; ok=$false }
try {
  $taskPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
  if (-not $taskPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'WINDOWS_ELEVATION_REQUIRED' }
  $taskProcess = Get-Process -Id $taskVmProcessId -ErrorAction SilentlyContinue
  if ($null -eq $taskProcess) {
    $taskReceipt.ok=$true; $taskReceipt.state='OWNED_PROCESS_ALREADY_EXITED'
  } else {
    if ($taskProcess.ProcessName -ne 'vmmemWindowsSandbox' -or [math]::Abs(($taskProcess.StartTime.ToUniversalTime()-$taskVmStartedAtUtc).TotalMilliseconds) -gt 1000) { throw 'OWNED_PROCESS_IDENTITY_CHANGED' }
    $taskList = @(& "$env:SystemRoot\System32\hcsdiag.exe" list 2>&1)
    if ($LASTEXITCODE -ne 0) { throw 'ELEVATED_HCS_LIST_FAILED' }
    $taskReceipt.hcs_target_listed = (($taskList -join "`n") -match [regex]::Escape($taskVmId))
    if (-not $taskReceipt.hcs_target_listed) {
      $taskReceipt.state='EXACT_VM_NOT_LISTED_NO_EFFECT'
      $taskReceipt.hcs_list = @($taskList | ForEach-Object { [string]$_ })
    } else {
      $taskKill = @(& "$env:SystemRoot\System32\hcsdiag.exe" kill $taskVmId 2>&1)
      if ($LASTEXITCODE -ne 0) { throw 'EXACT_VM_SHUTDOWN_FAILED' }
      $taskReceipt.mutated=$true
      $taskDeadline = [DateTimeOffset]::UtcNow.AddSeconds(45)
      do {
        Start-Sleep -Milliseconds 500
        $taskProcess = Get-Process -Id $taskVmProcessId -ErrorAction SilentlyContinue
      } while ($null -ne $taskProcess -and [DateTimeOffset]::UtcNow -lt $taskDeadline)
      if ($null -ne $taskProcess) { throw 'OWNED_VM_EXIT_NOT_OBSERVED' }
      $taskReceipt.ok=$true; $taskReceipt.state='EXACT_OWNED_VM_STOPPED'
    }
  }
} catch {
  $taskReceipt.error_code = $_.Exception.Message
} finally {
  $taskReceipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $taskReportRoot 'owned-sandbox-cleanup-receipt.json') -Encoding UTF8
}

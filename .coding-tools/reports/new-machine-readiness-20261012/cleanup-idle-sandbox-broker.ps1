[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$taskReportRoot = 'E:\DEV\Codex-web\.coding-tools\reports\new-machine-readiness-20261012'
$taskBrokerPid = 40676
$taskBrokerStartedAtUtc = ([DateTimeOffset]'2026-10-12T09:16:56.275423+07:00').UtcDateTime
$taskBrokerPath = 'C:\Program Files\WindowsApps\MicrosoftWindows.WindowsSandbox_0.8.107.0_x64__cw5n1h2txyewy\WindowsSandboxServer.exe'
$taskReceipt = [ordered]@{ operation='cleanup_exact_idle_sandbox_broker'; observed_at=[DateTimeOffset]::UtcNow.ToString('o'); pid=$taskBrokerPid; mutated=$false; ok=$false }
try {
  $taskPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
  if (-not $taskPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'WINDOWS_ELEVATION_REQUIRED' }
  $taskProcess = Get-Process -Id $taskBrokerPid -ErrorAction SilentlyContinue
  if ($null -eq $taskProcess) {
    $taskReceipt.ok=$true; $taskReceipt.state='EXACT_BROKER_ALREADY_EXITED'
  } else {
    if ($taskProcess.ProcessName -ne 'WindowsSandboxServer' -or $taskProcess.Path -ne $taskBrokerPath -or [math]::Abs(($taskProcess.StartTime.ToUniversalTime()-$taskBrokerStartedAtUtc).TotalMilliseconds) -gt 1) { throw 'BROKER_PROCESS_IDENTITY_CHANGED' }
    $taskSessionsRaw = @(& 'C:\Users\Admin\AppData\Local\Microsoft\WindowsApps\wsb.exe' list --raw 2>&1)
    if ($LASTEXITCODE -ne 0) { throw 'SANDBOX_SESSION_CENSUS_FAILED' }
    $taskSessions = ($taskSessionsRaw -join "`n") | ConvertFrom-Json
    if ($null -eq $taskSessions.PSObject.Properties['WindowsSandboxEnvironments']) { throw 'SANDBOX_SESSION_CENSUS_UNRECOGNIZED' }
    $taskReceipt.active_sessions = @($taskSessions.WindowsSandboxEnvironments).Count
    if ($taskReceipt.active_sessions -ne 0) { throw 'SANDBOX_SESSION_IS_ACTIVE' }
    $taskHcsRaw = @(& "$env:SystemRoot\System32\hcsdiag.exe" list 2>&1)
    if ($LASTEXITCODE -ne 0) { throw 'ELEVATED_HCS_CENSUS_FAILED' }
    $taskReceipt.hcs_census = @($taskHcsRaw | ForEach-Object { [string]$_ })
    $taskHcsLines = @($taskHcsRaw | ForEach-Object { ([string]$_).Trim() } | Where-Object { $_ })
    $taskGuidPattern = '[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
    $taskTemplatePattern = '^VM,\s*SavedAsTemplate,\s*' + $taskGuidPattern + ',\s*CmService$'
    $taskReceipt.saved_templates = @($taskHcsLines | Where-Object { $_ -match $taskTemplatePattern }).Count
    $taskUnknownLines = @($taskHcsLines | Where-Object { $_ -notmatch ('^' + $taskGuidPattern + '$') -and $_ -notmatch $taskTemplatePattern })
    $taskIdentityLines = @($taskHcsLines | Where-Object { $_ -match ('^' + $taskGuidPattern + '$') })
    if ($taskUnknownLines.Count -ne 0 -or $taskIdentityLines.Count -ne $taskReceipt.saved_templates) { throw 'COMPUTE_SYSTEM_IS_ACTIVE_OR_UNRECOGNIZED' }
    $taskReceipt.active_compute_systems = 0
    $taskOther = @(Get-Process -Name 'WindowsSandbox','WindowsSandboxClient','vmmemWindowsSandbox','WindowsSandboxRemoteSession','WindowsSandboxRemoteSessionClient' -ErrorAction SilentlyContinue)
    if ($taskOther.Count -ne 0) { throw 'OTHER_SANDBOX_PROCESS_IS_ACTIVE' }
    $taskFresh = Get-Process -Id $taskBrokerPid -ErrorAction Stop
    if ($taskFresh.ProcessName -ne 'WindowsSandboxServer' -or $taskFresh.Path -ne $taskBrokerPath -or [math]::Abs(($taskFresh.StartTime.ToUniversalTime()-$taskBrokerStartedAtUtc).TotalMilliseconds) -gt 1) { throw 'BROKER_PROCESS_IDENTITY_CHANGED' }
    Stop-Process -Id $taskBrokerPid -ErrorAction Stop
    $taskReceipt.mutated=$true
    Wait-Process -Id $taskBrokerPid -Timeout 15 -ErrorAction SilentlyContinue
    if ($null -ne (Get-Process -Id $taskBrokerPid -ErrorAction SilentlyContinue)) { throw 'BROKER_EXIT_NOT_OBSERVED' }
    $taskReceipt.ok=$true; $taskReceipt.state='EXACT_IDLE_BROKER_STOPPED'
  }
} catch {
  $taskReceipt.error_code = $_.Exception.Message
} finally {
  $taskReceipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $taskReportRoot 'idle-sandbox-broker-cleanup-receipt.json') -Encoding UTF8
}

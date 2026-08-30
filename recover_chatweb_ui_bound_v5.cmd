@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
set "RECOVERY_SELF=%~f0"
set "RECOVERY_LOG=%TEMP%\recover_chatweb_ui_bound_v5.log"

echo ============================================================
echo ChatWeb UI-Bound Connector Recovery V5
echo ============================================================
echo.
echo Uses the official Recovery Host full-clean refresh path.
echo UI profile workspace remains the source of truth.
echo No repository path, checkout path, contract SHA, MCP protocol, tool list, or MCP secret is hard-coded.
echo.

powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command "$p=$env:RECOVERY_SELF; $t=[IO.File]::ReadAllText($p); $m=('#'+'__POWERSHELL_PAYLOAD__'); $i=$t.IndexOf($m,[StringComparison]::Ordinal); if($i -lt 0){exit 90}; $s=$t.Substring($i+$m.Length); & ([ScriptBlock]::Create($s)); exit $global:LASTEXITCODE"
set "RC=%ERRORLEVEL%"

if not "%RC%"=="0" (
  echo.
  echo ============================================================
  echo [FAILED] UI_BOUND_CONNECTOR_RECOVERY_NOT_COMPLETE rc=%RC%
  echo ============================================================
  if exist "%RECOVERY_LOG%" (
    echo Log: %RECOVERY_LOG%
    echo.
    type "%RECOVERY_LOG%"
  )
  echo.
  echo Press any key to close this window.
  pause >nul
  exit /b %RC%
)

echo.
echo ============================================================
echo [SUCCESS] UI_BOUND_CONNECTOR_RECOVERY_COMPLETE
echo ============================================================
exit /b 0
#__POWERSHELL_PAYLOAD__

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$global:LASTEXITCODE = 1

$logFile = [string]$env:RECOVERY_LOG
if ([string]::IsNullOrWhiteSpace($logFile)) {
  $logFile = Join-Path $env:TEMP 'recover_chatweb_ui_bound_v5.log'
}
try { Set-Content -LiteralPath $logFile -Value '' -Encoding UTF8 } catch {}

function Write-Marker {
  param(
    [Parameter(Mandatory=$true)][string]$Name,
    [hashtable]$Fields = @{}
  )
  $parts = @($Name)
  foreach ($key in $Fields.Keys) {
    $value = [string]$Fields[$key]
    if ([string]::IsNullOrWhiteSpace($value)) { continue }
    $safe = ($value -replace '\s+', '_')
    if ($safe.Length -gt 220) { $safe = $safe.Substring(0,220) }
    $parts += "$key=$safe"
  }
  $line = ($parts -join ' ')
  Write-Host $line
  try { Add-Content -LiteralPath $logFile -Value $line -Encoding UTF8 } catch {}
}

function Fail-Recovery {
  param(
    [Parameter(Mandatory=$true)][string]$Code,
    [Parameter(Mandatory=$true)][string]$Message
  )
  $ex = New-Object System.InvalidOperationException("$Code|$Message")
  throw $ex
}


function Get-EpochDurableState {
  param($Epoch)
  if ($null -eq $Epoch) { return '' }
  # Recovery Host IPC exposes the coordinator's durable state as
  # `epoch_state`; its top-level `state` is a projection (for example
  # READY/UPDATE_INCOMPLETE).  The raw activation-epoch.json store instead
  # exposes the durable state as top-level `state`.  Prefer the explicit
  # durable `epoch_state`, then the top-level store state.  Only use nested
  # verification observations as a legacy fallback, and never let a stale
  # nested observation mask an explicit durable FAILED/READY/etc. state.
  $normalizeState = {
    param($Value)
    return (([string]$Value).Trim().ToUpperInvariant() -replace '[ -]+','_')
  }
  $projected = & $normalizeState $Epoch.state
  $durable = & $normalizeState $Epoch.epoch_state
  $knownDurable = @('PREPARING','ADMISSION_CLOSED','FROZEN','STOPPING','HANDOFF','STARTING','VERIFYING','READY_COMMITTED','READY','FAILED')
  $terminalDurable = @('READY','FAILED')
  # Raw store records carry durable state at top level.  Explicit terminal
  # states must outrank any stale nested/projection observation so admission
  # can never be reopened or retried from obsolete evidence.
  if ($terminalDurable -contains $projected) { return $projected }
  # Recovery Host IPC uses UPDATE_INCOMPLETE as the top-level projection and
  # exposes the durable coordinator state separately as epoch_state.
  if (($projected -eq '' -or $projected -eq 'UPDATE_INCOMPLETE') `
    -and ($knownDurable -contains $durable)) { return $durable }
  if (($projected -eq '' -or $projected -eq 'UPDATE_INCOMPLETE') `
    -and -not [string]::IsNullOrWhiteSpace($durable)) {
    Fail-Recovery 'ACTIVATION_EPOCH_STATE_INVALID' "Activation epoch state is not recognized. state=$projected epoch_state=$durable"
  }
  # A raw durable record may expose the same state in both fields.  Any
  # non-terminal disagreement is ambiguous authority and must stop recovery;
  # choosing either side could adopt or replace the wrong activation epoch.
  if ($knownDurable -contains $projected) {
    if (-not [string]::IsNullOrWhiteSpace($durable) `
      -and (-not ($knownDurable -contains $durable) -or $durable -ne $projected)) {
      Fail-Recovery 'ACTIVATION_EPOCH_STATE_CONTRADICTORY' "Activation epoch state is contradictory. state=$projected epoch_state=$durable"
    }
    return $projected
  }
  $nested = @(
    [string]$Epoch.verification.runtime.activationEpoch.epoch_state,
    [string]$Epoch.verification.activation_epoch.epoch_state,
    [string]$Epoch.activationEpoch.epoch_state
  )
  foreach ($candidate in $nested) {
    $normalized = & $normalizeState $candidate
    if ($knownDurable -contains $normalized) { return $normalized }
  }
  if ($projected -eq 'UPDATE_INCOMPLETE') { return '' }
  if ($projected -eq 'NONE' -and [string]::IsNullOrWhiteSpace($durable)) { return 'NONE' }
  if (-not [string]::IsNullOrWhiteSpace($projected) -or -not [string]::IsNullOrWhiteSpace($durable)) {
    Fail-Recovery 'ACTIVATION_EPOCH_STATE_INVALID' "Activation epoch state is not recognized. state=$projected epoch_state=$durable"
  }
  return $projected
}

function Normalize-Workspace {
  param([string]$Value)
  if ([string]::IsNullOrWhiteSpace($Value)) { return '' }
  try {
    $expanded = [Environment]::ExpandEnvironmentVariables($Value.Trim())
    # Windows PowerShell 5.1 runs on .NET Framework, where
    # Path.IsPathFullyQualified() is unavailable.  Require either an explicit
    # drive root or a complete UNC share before GetFullPath() so values such as
    # E:., C:, . and \folder can never inherit the process current directory.
    $driveQualified = $expanded -match '^[A-Za-z]:[\\/]'
    $uncQualified = $expanded -match '^[\\/]{2}[^\\/]+[\\/]+[^\\/]+(?:[\\/]|$)'
    if (-not ($driveQualified -or $uncQualified)) { return '' }
    $full = [IO.Path]::GetFullPath($expanded)
    $root = [IO.Path]::GetPathRoot($full)
    if ([string]::Equals($full, $root, [StringComparison]::OrdinalIgnoreCase)) {
      return $root.ToLowerInvariant()
    }
    return $full.TrimEnd([char]'\',[char]'/').ToLowerInvariant()
  } catch {
    return ''
  }
}

function Read-JsonFile {
  param(
    [Parameter(Mandatory=$true)][string]$Path,
    [Parameter(Mandatory=$true)][string]$Code
  )
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
    Fail-Recovery $Code "Missing file: $Path"
  }
  try {
    return (Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json)
  } catch {
    Fail-Recovery $Code "Invalid JSON: $Path"
  }
}

function Try-ReadDescriptor {
  param([Parameter(Mandatory=$true)][string]$Path)
  try {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    $value = Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json
    if ([int]$value.version -ne 1 -or [string]$value.host -ne '127.0.0.1' `
      -or [string]$value.owner -ne 'recovery-host') { return $null }
    if ([int]$value.port -lt 1 -or [int]$value.port -gt 65535) { return $null }
    if ([string]::IsNullOrWhiteSpace([string]$value.token) -or ([string]$value.token).Length -lt 32) { return $null }
    if ([int]$value.owner_pid -le 0 -or [string]$value.instance_id -notmatch '^[A-Za-z0-9][A-Za-z0-9_-]{15,127}$') { return $null }
    if ([string]$value.runtime_mode -notin @('development','packaged')) { return $null }
    if ([string]$value.installation_id -notmatch '^[0-9a-fA-F]{64}$') { return $null }
    $descriptorToken = Normalize-ProcessStartToken $value.owner_process_start_token
    if ([string]::IsNullOrWhiteSpace($descriptorToken)) { return $null }
    $observedToken = Get-ProcessStartToken ([int]$value.owner_pid)
    if ([string]::IsNullOrWhiteSpace($observedToken) -or $observedToken -ne $descriptorToken) { return $null }
    $value.installation_id = ([string]$value.installation_id).ToLowerInvariant()
    $value.runtime_mode = ([string]$value.runtime_mode).ToLowerInvariant()
    $value.owner_process_start_token = $descriptorToken
    return $value
  } catch {
    return $null
  }
}

function Normalize-ProcessStartToken {
  param([object]$Value)
  $raw = ([string]$Value).Trim()
  if ($raw -notmatch '^[0-9]{1,32}$') { return '' }
  try {
    # FILETIME is persisted as a decimal string.  UInt64 canonicalization
    # rejects zero/overflow and makes leading-zero aliases fail closed.
    $number = [UInt64]::Parse($raw)
    if ($number -eq 0) { return '' }
    return $number.ToString()
  } catch {
    return ''
  }
}

function Get-ProcessStartToken {
  param([Parameter(Mandatory=$true)][int]$Pid)
  try {
    $process = Get-Process -Id $Pid -ErrorAction Stop
    $creation = $process.StartTime.ToUniversalTime().ToFileTimeUtc()
    if ($creation -le 0) { return '' }
    # Match electron/services/processIdentity.js: retain microsecond precision.
    $creation = $creation - ($creation % 10)
    return (Normalize-ProcessStartToken $creation)
  } catch {
    return ''
  }
}

function Get-ExpectedInstallationIdentity {
  param([Parameter(Mandatory=$true)][string]$Checkout)
  try {
    $nodeCommand = Get-Command node.exe -ErrorAction Stop
    $node = [string]$nodeCommand.Source
    if ([string]::IsNullOrWhiteSpace($node)) { $node = [string]$nodeCommand.Path }
    if ([string]::IsNullOrWhiteSpace($node)) { throw 'node.exe path unavailable' }
  } catch {
    Fail-Recovery 'NODE_RUNTIME_UNAVAILABLE' 'Node.js is required to verify the current Recovery Host installation identity.'
  }
  $identityScript = "const {createDevelopmentPaths}=require('./scripts/dev-ui-lifecycle'); const paths=createDevelopmentPaths({appRoot:process.cwd()}); process.stdout.write(JSON.stringify(paths.runtimeIdentity()));"
  $pushed = $false
  $savedErrorActionPreference = $ErrorActionPreference
  try {
    Push-Location -LiteralPath $Checkout
    $pushed = $true
    $ErrorActionPreference = 'Continue'
    $output = @(& $node '-e' $identityScript 2>$null | ForEach-Object { [string]$_ })
    $exitCode = [int]$LASTEXITCODE
  } catch {
    Fail-Recovery 'RUNTIME_IDENTITY_UNAVAILABLE' 'The current checkout installation identity could not be resolved.'
  } finally {
    $ErrorActionPreference = $savedErrorActionPreference
    if ($pushed) { try { Pop-Location } catch {} }
  }
  if ($exitCode -ne 0 -or $output.Count -eq 0) {
    Fail-Recovery 'RUNTIME_IDENTITY_UNAVAILABLE' 'The current checkout installation identity could not be resolved.'
  }
  try { $identity = (($output -join '').Trim() | ConvertFrom-Json) } catch {
    Fail-Recovery 'RUNTIME_IDENTITY_INVALID' 'The current checkout returned invalid installation identity JSON.'
  }
  if ([int]$identity.version -ne 1 `
    -or [string]$identity.mode -notin @('development','packaged') `
    -or [string]$identity.installation_id -notmatch '^[0-9a-fA-F]{64}$') {
    Fail-Recovery 'RUNTIME_IDENTITY_INVALID' 'The current checkout installation identity is invalid.'
  }
  return [pscustomobject]@{
    version = 1
    runtime_mode = ([string]$identity.mode).ToLowerInvariant()
    installation_id = ([string]$identity.installation_id).ToLowerInvariant()
  }
}

function Assert-DescriptorExpectedInstallation {
  param(
    [Parameter(Mandatory=$true)]$Descriptor,
    [Parameter(Mandatory=$true)]$ExpectedIdentity,
    [string]$ExpectedEpochId = ''
  )
  if ([string]$Descriptor.installation_id -ne [string]$ExpectedIdentity.installation_id `
    -or [string]$Descriptor.runtime_mode -ne [string]$ExpectedIdentity.runtime_mode) {
    Fail-Recovery 'RECOVERY_HOST_INSTALLATION_MISMATCH' 'Recovery Host descriptor belongs to another installation or runtime mode.'
  }
  if (-not [string]::IsNullOrWhiteSpace($ExpectedEpochId) `
    -and [string]$Descriptor.activation_epoch_id -ne $ExpectedEpochId) {
    Fail-Recovery 'ACTIVATION_EPOCH_ID_MISMATCH' 'Recovery Host descriptor is not bound to the expected activation epoch.'
  }
  return $Descriptor
}

function Assert-DescriptorPinned {
  param(
    [Parameter(Mandatory=$true)]$Observed,
    [Parameter(Mandatory=$true)]$Pinned,
    [string]$ExpectedEpochId = ''
  )
  if ($null -eq $Observed -or $null -eq $Pinned) {
    Fail-Recovery 'RECOVERY_DESCRIPTOR_CHANGED' 'Recovery Host descriptor identity is not pinned.'
  }
  # The endpoint and bearer are part of the authenticated descriptor tuple.
  # Keep them in the in-memory pin and compare them on every reread; never
  # include either value in an error marker or other operator-facing output.
  # A same-PID/instance descriptor rewrite must not redirect a request to a
  # different listener or accept a token from an unrelated host.
  $portMatches = ([int]$Observed.port -eq [int]$Pinned.port)
  $tokenMatches = [String]::Equals(
    [string]$Observed.token,
    [string]$Pinned.token,
    [StringComparison]::Ordinal
  )
  $same = ([int]$Observed.owner_pid -eq [int]$Pinned.owner_pid) `
    -and ([string]$Observed.instance_id -eq [string]$Pinned.instance_id) `
    -and ([string]$Observed.owner_process_start_token -eq [string]$Pinned.owner_process_start_token) `
    -and ([string]$Observed.installation_id -eq [string]$Pinned.installation_id) `
    -and ([string]$Observed.runtime_mode -eq [string]$Pinned.runtime_mode) `
    -and ([string]$Observed.owner -eq [string]$Pinned.owner) `
    -and ([string]$Observed.host -eq [string]$Pinned.host) `
    -and $portMatches `
    -and $tokenMatches
  if (-not $same) {
    # Do not include bearer tokens in diagnostics.  Identity mismatch is enough
    # to reject a possible descriptor replacement/PID-reuse race.
    Fail-Recovery 'RECOVERY_DESCRIPTOR_CHANGED' 'Recovery Host descriptor identity changed during recovery.'
  }
  if (-not [string]::IsNullOrWhiteSpace($ExpectedEpochId) `
    -and [string]$Observed.activation_epoch_id -ne $ExpectedEpochId) {
    Fail-Recovery 'ACTIVATION_EPOCH_ID_MISMATCH' 'Recovery Host descriptor is not bound to the expected activation epoch.'
  }
  return $Observed
}

function Read-PinnedDescriptor {
  param(
    [Parameter(Mandatory=$true)][string]$Path,
    [Parameter(Mandatory=$true)]$Pinned,
    [string]$ExpectedEpochId = ''
  )
  # Atomic descriptor writes can leave a sub-millisecond rename gap.  Allow a
  # short bounded retry for that transport artifact, but never adopt a new
  # identity after the pinned owner fails to reappear.
  for ($attempt = 0; $attempt -lt 3; $attempt++) {
    $fresh = Try-ReadDescriptor $Path
    if ($null -ne $fresh) {
      return (Assert-DescriptorPinned $fresh $Pinned $ExpectedEpochId)
    }
    if ($attempt -lt 2) { Start-Sleep -Milliseconds 50 }
  }
  Fail-Recovery 'RECOVERY_DESCRIPTOR_CHANGED' 'Pinned Recovery Host descriptor disappeared or failed process-identity verification.'
}

function Read-HttpErrorBody {
  param($ErrorRecord)
  try {
    $details = [string]$ErrorRecord.ErrorDetails.Message
    if (-not [string]::IsNullOrWhiteSpace($details)) { return $details }
  } catch {}
  try {
    $Exception = if ($null -ne $ErrorRecord.Exception) { $ErrorRecord.Exception } else { $ErrorRecord }
    $response = $Exception.Response
    if ($null -eq $response) { return $null }
    $stream = $response.GetResponseStream()
    if ($null -eq $stream) { return $null }
    $reader = New-Object IO.StreamReader($stream)
    try { return $reader.ReadToEnd() }
    finally { $reader.Dispose(); $stream.Dispose() }
  } catch {
    return $null
  }
}

function Invoke-RecoveryAction {
  param(
    [Parameter(Mandatory=$true)]$Descriptor,
    [Parameter(Mandatory=$true)][string]$Action,
    [object[]]$Args = @(),
    [int]$TimeoutSec = 95,
    [object]$PinnedDescriptor = $null,
    [string]$DescriptorPath = '',
    [string]$ExpectedEpochId = ''
  )
  if (-not [string]::IsNullOrWhiteSpace($DescriptorPath)) {
    if ($null -eq $PinnedDescriptor) {
      Fail-Recovery 'RECOVERY_DESCRIPTOR_UNPINNED' 'Refusing an IPC action without a pinned Recovery Host identity.'
    }
    # The descriptor is atomically reread immediately before every authenticated
    # request.  Never continue with a PID/port/token tuple captured earlier.
    $Descriptor = Read-PinnedDescriptor $DescriptorPath $PinnedDescriptor $ExpectedEpochId
  } elseif ($null -ne $PinnedDescriptor) {
    [void](Assert-DescriptorPinned $Descriptor $PinnedDescriptor $ExpectedEpochId)
  }
  $port = [int]$Descriptor.port
  $token = [string]$Descriptor.token
  $uri = "http://127.0.0.1:$port/v1/call"
  $headers = @{ Authorization = "Bearer $token" }
  $body = @{ action = $Action; args = $Args } | ConvertTo-Json -Depth 20 -Compress
  try {
    $response = Invoke-RestMethod -Method Post -Uri $uri -Headers $headers -ContentType 'application/json' -Body $body -TimeoutSec $TimeoutSec
  } catch {
    # Windows PowerShell commonly consumes the response stream and keeps a
    # structured HTTP error body only in ErrorDetails.Message.  Parse that
    # authoritative body before classifying the transport as unreachable.
    $raw = Read-HttpErrorBody $_
    if (-not [string]::IsNullOrWhiteSpace($raw)) {
      try {
        $parsed = $raw | ConvertFrom-Json
        $code = [string]$parsed.error.code
        $message = [string]$parsed.error.message
        if (-not [string]::IsNullOrWhiteSpace($code)) {
          Fail-Recovery $code $message
        }
      } catch [System.InvalidOperationException] {
        throw
      } catch {}
    }
    $nativeCode = [string]$_.Exception.GetType().Name
    Fail-Recovery 'RECOVERY_IPC_UNREACHABLE' "Recovery Host IPC call failed ($nativeCode): $Action"
  }
  if ($null -eq $response -or $response.ok -ne $true) {
    $code = if ($null -ne $response) { [string]$response.error.code } else { 'RECOVERY_IPC_INVALID_RESPONSE' }
    $message = if ($null -ne $response) { [string]$response.error.message } else { 'Recovery Host returned no response.' }
    if ([string]::IsNullOrWhiteSpace($code)) { $code = 'RECOVERY_IPC_INVALID_RESPONSE' }
    Fail-Recovery $code $message
  }
  if (-not [string]::IsNullOrWhiteSpace($DescriptorPath)) {
    # Confirm that the authenticated response still belongs to the same pinned
    # owner.  A replacement during a request is never adopted implicitly.
    [void](Read-PinnedDescriptor $DescriptorPath $PinnedDescriptor $ExpectedEpochId)
  }
  return $response.data
}

function Invoke-CurrentCheckoutRefresh {
  param(
    [Parameter(Mandatory=$true)][string]$WrapperPath,
    [Parameter(Mandatory=$true)][string]$Workspace
  )
  $checkout = [IO.Path]::GetFullPath((Split-Path -Parent $WrapperPath))
  $lifecycle = Join-Path $checkout 'scripts\dev-ui-lifecycle.js'
  if (-not (Test-Path -LiteralPath $lifecycle -PathType Leaf)) {
    Fail-Recovery 'DEV_UI_LIFECYCLE_UNAVAILABLE' "Current-checkout lifecycle is missing: $lifecycle"
  }
  try {
    $nodeCommand = Get-Command node.exe -ErrorAction Stop
    $node = [string]$nodeCommand.Source
    if ([string]::IsNullOrWhiteSpace($node)) { $node = [string]$nodeCommand.Path }
    if ([string]::IsNullOrWhiteSpace($node)) { throw 'node.exe path unavailable' }
  } catch {
    Fail-Recovery 'NODE_RUNTIME_UNAVAILABLE' 'Node.js is required to run the current-checkout Recovery Host lifecycle.'
  }

  Write-Marker 'FULL_CLEAN_REFRESH_LIFECYCLE_BEGIN' @{
    source = 'current_checkout'
    workspace = $Workspace
  }
  $locationPushed = $false
  $savedErrorActionPreference = $ErrorActionPreference
  try {
    # Invoke the executable with PowerShell's call operator.  Unlike
    # Start-Process -ArgumentList on Windows PowerShell 5.1, this preserves a
    # checkout path containing spaces as one argv item without hand-built
    # quoting or shell interpretation.
    Push-Location -LiteralPath $checkout
    $locationPushed = $true
    # Native stderr is represented as a terminating RemoteException when the
    # caller has `$ErrorActionPreference = 'Stop'`, even after `2>&1`.  Keep
    # the native stream in the captured output so the lifecycle's structured
    # DEV_UI ERROR code can be classified below, then restore the caller's
    # preference before returning.
    $ErrorActionPreference = 'Continue'
    $output = @(& $node $lifecycle 'refresh' 2>&1 | ForEach-Object { [string]$_ })
    $exitCode = [int]$LASTEXITCODE
  } catch {
    Fail-Recovery 'DEV_UI_REFRESH_START_FAILED' "Current-checkout lifecycle could not start: $($_.Exception.GetType().Name)"
  } finally {
    $ErrorActionPreference = $savedErrorActionPreference
    if ($locationPushed) {
      try { Pop-Location } catch {}
    }
  }
  foreach ($line in $output) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    Write-Host $line
    try { Add-Content -LiteralPath $logFile -Value $line -Encoding UTF8 } catch {}
  }
  if ($exitCode -ne 0) {
    $errorLine = $output | Where-Object { $_ -match '^DEV_UI ERROR code=([^ ]+) message=(.*)$' } | Select-Object -Last 1
    if (-not [string]::IsNullOrWhiteSpace([string]$errorLine) -and $errorLine -match '^DEV_UI ERROR code=([^ ]+) message=(.*)$') {
      Fail-Recovery ([string]$matches[1]) ([string]$matches[2])
    }
    Fail-Recovery 'DEV_UI_REFRESH_FAILED' "Current-checkout lifecycle exited with code $exitCode."
  }
  Write-Marker 'FULL_CLEAN_REFRESH_LIFECYCLE_PASS' @{ source = 'current_checkout' }
}

function Try-ReadActivationRecord {
  param([Parameter(Mandatory=$true)][string]$Path)
  try {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    $value = Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json
    return $value.current
  } catch {
    return $null
  }
}

function Get-NowUnixMs {
  return [int64]([DateTimeOffset]::UtcNow - [DateTimeOffset]'1970-01-01T00:00:00Z').TotalMilliseconds
}

function Parse-RecoveryException {
  param($Exception)
  $raw = [string]$Exception.Message
  if ($raw -match '^([^|]+)\|(.*)$') {
    return @{ code = $matches[1]; message = $matches[2] }
  }
  return @{ code = 'RECOVERY_FAILED'; message = $raw }
}

function Get-SnapshotStatus {
  param($Snapshot)
  if ($null -ne $Snapshot.status) { return $Snapshot.status }
  return $Snapshot
}

function Get-SnapshotWorkspace {
  param($Snapshot)
  $candidates = @(
    [string]$Snapshot.workspace,
    [string]$Snapshot.status.workspace,
    [string]$Snapshot.device.workspace
  )
  foreach ($candidate in $candidates) {
    if (-not [string]::IsNullOrWhiteSpace($candidate)) { return $candidate }
  }
  return ''
}

function Get-ToolContractSha {
  param($Snapshot)
  $values = @(
    [string]$Snapshot.toolContract.sha256,
    [string]$Snapshot.status.toolContract.sha256,
    [string]$Snapshot.recoveryHost.runtime.tool_contract.sha256
  )
  foreach ($value in $values) {
    if ($value -match '^[0-9a-fA-F]{64}$') { return $value.ToLowerInvariant() }
  }
  return ''
}

function Test-RefreshEpochRecord {
  param($Epoch)
  if ($null -eq $Epoch) { return $false }
  $intent = $Epoch.request_intent
  if ($null -eq $intent) { return $false }
  $intentMode = ([string]$intent.mode).Trim().ToLowerInvariant()
  $recordMode = ([string]$Epoch.mode).Trim().ToLowerInvariant()
  $intentRefresh = $intent.metadata.refresh -eq $true
  $recordRefresh = $Epoch.metadata.refresh -eq $true
  $intentHasCheckpoint = $null -ne $intent.source_checkpoint `
    -and -not [string]::IsNullOrWhiteSpace([string]$intent.source_checkpoint)
  $recordHasCheckpoint = $null -ne $Epoch.source_checkpoint `
    -and -not [string]::IsNullOrWhiteSpace([string]$Epoch.source_checkpoint)
  return $intentMode -eq 'full_clean_activation' `
    -and $recordMode -eq $intentMode `
    -and $intentRefresh -and $recordRefresh `
    -and -not $intentHasCheckpoint -and -not $recordHasCheckpoint
}

function Test-ConnectorTimestamp {
  param([string]$Value)
  if ([string]::IsNullOrWhiteSpace($Value)) { return $false }
  try {
    $parsed = [DateTimeOffset]::Parse($Value, [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::RoundtripKind)
    return $parsed -gt [DateTimeOffset]'1970-01-01T00:00:00Z'
  } catch {
    return $false
  }
}

function Test-EpochSnapshotBinding {
  param(
    [Parameter(Mandatory=$true)]$Snapshot,
    [Parameter(Mandatory=$true)]$Epoch
  )
  $expectedEpochId = [string]$Epoch.activation_epoch_id
  $expectedOperationId = [string]$Epoch.operation_id
  if ([string]::IsNullOrWhiteSpace($expectedEpochId) -or [string]::IsNullOrWhiteSpace($expectedOperationId)) { return $false }
  $status = Get-SnapshotStatus $Snapshot
  $epochValues = @(
    [string]$status.activationEpoch.activation_epoch_id,
    [string]$Snapshot.activationEpoch.activation_epoch_id,
    [string]$Snapshot.recoveryHost.activation_epoch.activation_epoch_id
  ) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
  $operationValues = @(
    [string]$status.activationEpoch.operation_id,
    [string]$Snapshot.activationEpoch.operation_id,
    [string]$Snapshot.recoveryHost.activation_epoch.operation_id
  ) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
  return $epochValues.Count -gt 0 -and $operationValues.Count -gt 0 `
    -and ($epochValues | Where-Object { $_ -ne $expectedEpochId }).Count -eq 0 `
    -and ($operationValues | Where-Object { $_ -ne $expectedOperationId }).Count -eq 0
}

function Test-ConnectorReadySnapshot {
  param([Parameter(Mandatory=$true)]$Snapshot)
  $status = Get-SnapshotStatus $Snapshot
  if ($status.connectorRefreshRequired -ne $false -or $status.connectorAcknowledgementPending -ne $false) { return $false }
  $currentSha = Get-ToolContractSha $Snapshot
  $ackSha = [string]$status.connectorContractAcknowledgedSha256
  if ($currentSha -notmatch '^[0-9a-fA-F]{64}$' -or [string]::IsNullOrWhiteSpace($ackSha) `
    -or $ackSha.ToLowerInvariant() -ne $currentSha.ToLowerInvariant()) { return $false }
  if ([string]$status.connectorContractState -eq 'CURRENT_ACKNOWLEDGED') {
    return [string]$status.connectorFreshnessMode -eq 'current_process_discovery' `
      -and $status.connectorRediscovered -eq $true `
      -and (Test-ConnectorTimestamp ([string]$status.connectorRediscoveredAt))
  }
  if ([string]$status.connectorContractState -eq 'CURRENT_COMPATIBLE_ACKNOWLEDGED') {
    return [string]$status.connectorFreshnessMode -eq 'compatible_activation_bootstrap' `
      -and $status.connectorRediscovered -ne $true `
      -and $status.connectorCompatibilityAcknowledged -eq $true `
      -and (Test-ConnectorTimestamp ([string]$status.connectorCompatibilityAcknowledgedAt))
  }
  return $false
}

function Assert-WorkspaceMatch {
  param(
    [Parameter(Mandatory=$true)]$Snapshot,
    [Parameter(Mandatory=$true)][string]$ExpectedNormalized,
    [Parameter(Mandatory=$true)][string]$ExpectedRaw,
    [Parameter(Mandatory=$true)][string]$Code
  )
  $observedRaw = Get-SnapshotWorkspace $Snapshot
  $observed = Normalize-Workspace $observedRaw
  if ([string]::IsNullOrWhiteSpace($observed) -or $observed -ne $ExpectedNormalized) {
    Fail-Recovery $Code "UI workspace and runtime workspace differ. ui=$ExpectedRaw runtime=$observedRaw"
  }
  return $observedRaw
}

function Assert-UiProfileWorkspaceStable {
  param(
    [Parameter(Mandatory=$true)][string]$SettingsPath,
    [Parameter(Mandatory=$true)][string]$ExpectedNormalized,
    [Parameter(Mandatory=$true)][string]$ExpectedRaw
  )
  # Workspace authority belongs to the live UI profile, not to the process
  # current directory or to a value captured by an older runtime snapshot.
  # Re-read the atomically-written settings file before every polling phase so
  # a concurrent UI workspace switch cannot let this wrapper acknowledge the
  # previous workspace and report a false success.
  $currentSettings = Read-JsonFile $SettingsPath 'SETTINGS_UNAVAILABLE'
  $currentRaw = [string]$currentSettings.workspace
  $currentNormalized = Normalize-Workspace $currentRaw
  if ([string]::IsNullOrWhiteSpace($currentNormalized) -or $currentNormalized -ne $ExpectedNormalized) {
    Fail-Recovery 'UI_WORKSPACE_CHANGED' "UI profile workspace changed during recovery. expected=$ExpectedRaw current=$currentRaw"
  }
  return $currentRaw
}

try {
  if ([string]::IsNullOrWhiteSpace([string]$env:APPDATA)) {
    Fail-Recovery 'APPDATA_UNAVAILABLE' 'APPDATA is unavailable.'
  }

  $profile = Join-Path $env:APPDATA 'web-mcp-assistant'
  $settingsPath = Join-Path $profile 'settings.json'
  $descriptorPath = Join-Path $profile 'recovery-host.json'
  $settings = Read-JsonFile $settingsPath 'SETTINGS_UNAVAILABLE'
  $uiWorkspaceRaw = [string]$settings.workspace
  $uiWorkspace = Normalize-Workspace $uiWorkspaceRaw
  if ([string]::IsNullOrWhiteSpace($uiWorkspace)) {
    Fail-Recovery 'UI_WORKSPACE_UNBOUND' 'The UI profile does not contain a valid bound workspace.'
  }
  if (-not (Test-Path -LiteralPath $uiWorkspace -PathType Container)) {
    Fail-Recovery 'UI_WORKSPACE_MISSING' "The UI-bound workspace does not exist: $uiWorkspaceRaw"
  }

  $checkoutPath = [IO.Path]::GetFullPath((Split-Path -Parent $env:RECOVERY_SELF))
  $expectedInstallation = Get-ExpectedInstallationIdentity $checkoutPath

  Write-Marker 'UI_BOUND_WORKSPACE' @{ workspace = $uiWorkspaceRaw }
  $activationEpochPath = Join-Path $profile 'activation-epoch.json'
  $beforeEpoch = Try-ReadActivationRecord $activationEpochPath
  if ($null -eq $beforeEpoch) { $beforeEpoch = [pscustomobject]@{} }
  $oldEpochId = [string]$beforeEpoch.activation_epoch_id
  $oldEpochState = Get-EpochDurableState $beforeEpoch
  $oldProjectionState = [string]$beforeEpoch.state
  $oldOperationId = [string]$beforeEpoch.operation_id
  $oldEpochError = [string]$beforeEpoch.error.code
  $oldExpiry = 0L
  try { $oldExpiry = [int64]$beforeEpoch.expires_at_unix_ms } catch { $oldExpiry = 0L }
  $oldExpired = $oldExpiry -gt 0 -and $oldExpiry -le (Get-NowUnixMs)
  Write-Marker 'ACTIVATION_EPOCH_BEFORE' @{
    epoch = $oldEpochId
    epoch_state = $oldEpochState
    projection_state = $oldProjectionState
    operation = $oldOperationId
    error = $oldEpochError
  }

  $activeEpochStates = @('PREPARING','ADMISSION_CLOSED','STOPPING','FROZEN','HANDOFF','STARTING','VERIFYING','READY_COMMITTED')
  $epochPresent = -not [string]::IsNullOrWhiteSpace($oldEpochId)
  $oldAdmissionOpen = ($beforeEpoch.admission_open -eq $true) `
    -or ([string]$beforeEpoch.admission_state).ToUpperInvariant() -eq 'OPEN'
  $oldReadyOpen = $oldEpochState -eq 'READY' -and $oldAdmissionOpen
  $oldActiveRefresh = $activeEpochStates -contains $oldEpochState
  if ($oldActiveRefresh -and -not (Test-RefreshEpochRecord $beforeEpoch)) {
    Fail-Recovery 'ACTIVATION_EPOCH_CONFLICT' 'An active non-refresh activation epoch owns the runtime; refusing to adopt it as the V5 process refresh.'
  }
  # A terminal READY/open record remains the current authority even if an old
  # nested projection still carries an expiry/error observation.  Refresh is
  # only considered when the record is not already durably admitted.
  $needsRefresh = (-not $oldReadyOpen) -and (
    ($oldEpochError -eq 'ACTIVATION_REQUEST_EXPIRED') `
    -or ($oldEpochState -eq 'FAILED') `
    -or $oldExpired `
    -or (-not $epochPresent) `
    -or ($oldEpochState -eq 'NONE')
  )
  if ($oldReadyOpen) {
    Write-Marker 'ACTIVATION_EPOCH_ALREADY_CURRENT' @{ epoch = $oldEpochId; epoch_state = $oldEpochState; admission = 'open' }
  } elseif ($activeEpochStates -contains $oldEpochState -and -not $needsRefresh) {
    Write-Marker 'ACTIVATION_EPOCH_IN_PROGRESS' @{ epoch = $oldEpochId; epoch_state = $oldEpochState; operation = $oldOperationId }
  } elseif (-not $needsRefresh) {
    Fail-Recovery 'ACTIVATION_EPOCH_STATE_UNEXPECTED' "Refusing to restart because the current durable activation state is not safely classified: $oldEpochState"
  } else {
    Write-Marker 'FULL_CLEAN_REFRESH_BEGIN' @{ workspace = $uiWorkspaceRaw; old_epoch = $oldEpochId; old_state = $oldEpochState }
    # Never send full-clean activation to whatever Recovery Host happens to be
    # loaded already: it may still contain stale coordinator source.  The
    # repository-supported lifecycle authenticates the exact old owner, loads
    # this wrapper's current checkout, and lets that host create the epoch.
    Invoke-CurrentCheckoutRefresh $env:RECOVERY_SELF $uiWorkspaceRaw
  }

  $expectedEpochId = if ($needsRefresh) { '' } else { [string]$oldEpochId }
  if ($needsRefresh) {
    $afterRefresh = Try-ReadActivationRecord $activationEpochPath
    if ($null -ne $afterRefresh) {
      $afterRefreshId = [string]$afterRefresh.activation_epoch_id
      if (-not [string]::IsNullOrWhiteSpace($afterRefreshId) -and $afterRefreshId -ne $oldEpochId) {
        $expectedEpochId = $afterRefreshId
      }
    }
  }

  $bootstrapDeadline = [DateTime]::UtcNow.AddMinutes(10)
  $lastBootstrapNotice = [DateTime]::MinValue
  $connectorReadyObserved = $false
  $lastEpoch = $null
  $lastSnapshot = $null
  $pinnedDescriptor = $null

  while ([DateTime]::UtcNow -lt $bootstrapDeadline) {
    [void](Assert-UiProfileWorkspaceStable $settingsPath $uiWorkspace $uiWorkspaceRaw)
    if ($null -ne $pinnedDescriptor) {
      $descriptor = Read-PinnedDescriptor $descriptorPath $pinnedDescriptor $expectedEpochId
    } else {
      $descriptor = Try-ReadDescriptor $descriptorPath
    }
    if ($null -eq $descriptor) {
      Start-Sleep -Milliseconds 750
      continue
    }
    if ($null -eq $pinnedDescriptor) {
      [void](Assert-DescriptorExpectedInstallation $descriptor $expectedInstallation $expectedEpochId)
      $pinnedDescriptor = $descriptor
      Write-Marker 'RECOVERY_HOST_PINNED' @{
        instance = [string]$descriptor.instance_id
        pid = [string]$descriptor.owner_pid
        runtime_mode = [string]$descriptor.runtime_mode
        installation_id = [string]$descriptor.installation_id
      }
    } else {
      [void](Assert-DescriptorPinned $descriptor $pinnedDescriptor $expectedEpochId)
    }
    try {
      $lastEpoch = Invoke-RecoveryAction $descriptor 'runtime.activation_epoch_status' @() 20 $pinnedDescriptor $descriptorPath $expectedEpochId
      $lastSnapshot = Invoke-RecoveryAction $descriptor 'runtime.lightweight_snapshot' @() 20 $pinnedDescriptor $descriptorPath $expectedEpochId
      [void](Assert-WorkspaceMatch $lastSnapshot $uiWorkspace $uiWorkspaceRaw 'UI_WORKSPACE_CHANGED')
      $lastEpochId = [string]$lastEpoch.activation_epoch_id
      if (-not [string]::IsNullOrWhiteSpace($expectedEpochId) -and $lastEpochId -ne $expectedEpochId) {
        Start-Sleep -Milliseconds 750
        continue
      }
      if ([string]::IsNullOrWhiteSpace($expectedEpochId) -and -not [string]::IsNullOrWhiteSpace($lastEpochId) -and $lastEpochId -ne $oldEpochId) {
        $expectedEpochId = $lastEpochId
      }
      if (-not (Test-EpochSnapshotBinding $lastSnapshot $lastEpoch)) {
        # Keep admission closed while the host's cached runtime projection
        # catches up to the durable epoch/operation receipt.
        Start-Sleep -Milliseconds 250
        continue
      }
      $epochError = [string]$lastEpoch.error.code
      if ($epochError -eq 'ACTIVATION_REQUEST_EXPIRED') {
        Fail-Recovery 'ACTIVATION_REQUEST_EXPIRED' 'The new activation epoch expired before connector bootstrap completed.'
      }
      if ((Get-EpochDurableState $lastEpoch) -eq 'FAILED') {
        $failCode = if ([string]::IsNullOrWhiteSpace($epochError)) { 'ACTIVATION_FAILED' } else { $epochError }
        Fail-Recovery $failCode ([string]$lastEpoch.error.message)
      }

      [void](Assert-UiProfileWorkspaceStable $settingsPath $uiWorkspace $uiWorkspaceRaw)
      $snapshotStatus = Get-SnapshotStatus $lastSnapshot
      $connectorState = [string]$snapshotStatus.connectorContractState
      if (Test-ConnectorReadySnapshot $lastSnapshot `
        -and (Get-EpochDurableState $lastEpoch) -eq 'READY' `
        -and ($lastEpoch.admission_open -eq $true -or [string]$lastEpoch.admission_state -eq 'OPEN')) {
        $connectorReadyObserved = $true
        Write-Marker 'CURRENT_CONNECTOR_READY_OBSERVED' @{
          epoch = [string]$lastEpoch.activation_epoch_id
          connector_state = $connectorState
          acknowledged_sha = [string]$snapshotStatus.connectorContractAcknowledgedSha256
          rediscovered_at = [string]$snapshotStatus.connectorRediscoveredAt
          compatibility_at = [string]$snapshotStatus.connectorCompatibilityAcknowledgedAt
        }
        break
      }
      if ($connectorState -in @('CHANGED_NEEDS_DISCOVERY','CHANGED_DISCOVERED_NEEDS_ACK','CHANGED_COMPATIBLE_NEEDS_ACK','UNCHANGED_COMPATIBLE_NEEDS_ACK')) {
        if (([DateTime]::UtcNow - $lastBootstrapNotice).TotalSeconds -ge 10) {
          Write-Marker 'CHATWEB_BOOTSTRAP_REQUIRED' @{
            epoch = [string]$lastEpoch.activation_epoch_id
            action = 'call_Coding-VP_workspace_context_from_this_chat'
            workspace = $uiWorkspaceRaw
          }
          $lastBootstrapNotice = [DateTime]::UtcNow
        }
      }
    } catch {
      $parsed = Parse-RecoveryException $_.Exception
      if ([string]$parsed.code -in @('RECOVERY_IPC_UNREACHABLE','RECOVERY_BOOTSTRAP_IN_PROGRESS')) {
        Start-Sleep -Milliseconds 750
        continue
      }
      throw
    }
    Start-Sleep -Seconds 1
  }

  if (-not $connectorReadyObserved) {
    Fail-Recovery 'CHATWEB_BOOTSTRAP_TIMEOUT' 'The current activation epoch is waiting for current ChatWeb connector evidence and acknowledgement.'
  }

  $readyDeadline = [DateTime]::UtcNow.AddSeconds(90)
  while ([DateTime]::UtcNow -lt $readyDeadline) {
    Start-Sleep -Milliseconds 750
    [void](Assert-UiProfileWorkspaceStable $settingsPath $uiWorkspace $uiWorkspaceRaw)
    if ($null -eq $pinnedDescriptor) {
      $descriptor = Try-ReadDescriptor $descriptorPath
      if ($null -eq $descriptor) { continue }
      [void](Assert-DescriptorExpectedInstallation $descriptor $expectedInstallation $expectedEpochId)
      $pinnedDescriptor = $descriptor
      Write-Marker 'RECOVERY_HOST_PINNED' @{
        instance = [string]$descriptor.instance_id
        pid = [string]$descriptor.owner_pid
        runtime_mode = [string]$descriptor.runtime_mode
        installation_id = [string]$descriptor.installation_id
      }
    } else {
      $descriptor = Read-PinnedDescriptor $descriptorPath $pinnedDescriptor $expectedEpochId
    }
    try {
      $lastEpoch = Invoke-RecoveryAction $descriptor 'runtime.activation_epoch_status' @() 20 $pinnedDescriptor $descriptorPath $expectedEpochId
      $lastSnapshot = Invoke-RecoveryAction $descriptor 'runtime.lightweight_snapshot' @() 20 $pinnedDescriptor $descriptorPath $expectedEpochId
      $finalWorkspaceRaw = Assert-WorkspaceMatch $lastSnapshot $uiWorkspace $uiWorkspaceRaw 'UI_WORKSPACE_CHANGED'
      if (-not [string]::IsNullOrWhiteSpace($expectedEpochId) -and [string]$lastEpoch.activation_epoch_id -ne $expectedEpochId) {
        continue
      }
      if (-not (Test-EpochSnapshotBinding $lastSnapshot $lastEpoch)) {
        continue
      }
      $status = Get-SnapshotStatus $lastSnapshot
      $state = Get-EpochDurableState $lastEpoch
      $epochError = [string]$lastEpoch.error.code
      if ($epochError -eq 'ACTIVATION_REQUEST_EXPIRED') {
        Fail-Recovery 'ACTIVATION_REQUEST_EXPIRED' 'Activation expired after connector acknowledgement.'
      }
      if ($state -eq 'FAILED') {
        $failCode = if ([string]::IsNullOrWhiteSpace($epochError)) { 'ACTIVATION_FAILED' } else { $epochError }
        Fail-Recovery $failCode ([string]$lastEpoch.error.message)
      }
      $fullyReady = ($status.fullyReady -eq $true -or $lastSnapshot.fullyReady -eq $true)
      $refreshRequired = ($status.connectorRefreshRequired -eq $true -or $lastSnapshot.connectorRefreshRequired -eq $true)
      $admissionOpen = $lastEpoch.admission_open -eq $true -or [string]$lastEpoch.admission_state -eq 'OPEN'
      $connectorReady = Test-ConnectorReadySnapshot $lastSnapshot
      if ($state -eq 'READY' -and $admissionOpen -and $fullyReady -and $connectorReady -and -not $refreshRequired) {
        [void](Assert-UiProfileWorkspaceStable $settingsPath $uiWorkspace $uiWorkspaceRaw)
        Write-Marker 'ACTIVATION_READY' @{
          workspace = $finalWorkspaceRaw
          epoch = [string]$lastEpoch.activation_epoch_id
          admission = 'open'
          fully_ready = 'true'
          contract_sha = (Get-ToolContractSha $lastSnapshot)
          pid = [string]$descriptor.owner_pid
          instance = [string]$descriptor.instance_id
        }
        Write-Marker 'UI_BOUND_CONNECTOR_RECOVERY_COMPLETE' @{ workspace = $finalWorkspaceRaw; epoch = [string]$lastEpoch.activation_epoch_id }
        $global:LASTEXITCODE = 0
        return
      }
    } catch {
      $parsed = Parse-RecoveryException $_.Exception
      if ([string]$parsed.code -in @('RECOVERY_IPC_UNREACHABLE','RECOVERY_BOOTSTRAP_IN_PROGRESS')) { continue }
      throw
    }
  }

  Fail-Recovery 'ACTIVATION_READY_TIMEOUT' 'Connector acknowledgement succeeded but the activation did not reach READY/open admission.'
} catch {
  $parsed = Parse-RecoveryException $_.Exception
  Write-Marker 'UI_BOUND_CONNECTOR_RECOVERY_FAILED' @{ code = [string]$parsed.code; message = [string]$parsed.message }
  $global:LASTEXITCODE = 1
}

param(
    [switch]$ExecuteConfirmedIsolatedIdleCanary,
    [Parameter(Mandatory = $true)][string]$ReadyPinsPath,
    [Parameter(Mandatory = $true)][string]$ParityProofPath,
    [Parameter(Mandatory = $true)][string]$IsolatedPolicyReceiptPath,
    [Parameter(Mandatory = $true)][string]$PythonPath,
    [Parameter(Mandatory = $true)][guid]$AttemptId
)
$ErrorActionPreference = 'Stop'
if (-not $ExecuteConfirmedIsolatedIdleCanary) { throw 'EXPLICIT_ISOLATED_IDLE_EXECUTION_REQUIRED' }
$attemptText = $AttemptId.ToString('N')
$pins = Get-Content -LiteralPath $ReadyPinsPath -Raw | ConvertFrom-Json
$isolated = Get-Content -LiteralPath $IsolatedPolicyReceiptPath -Raw | ConvertFrom-Json
$parity = Get-Content -LiteralPath $ParityProofPath -Raw | ConvertFrom-Json
$expectedR4Candidate = 'E:\DEV\Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-parallel-r4-timefix\win-unpacked'
if ([IO.Path]::GetFullPath($parity.candidate) -ne $expectedR4Candidate) { throw 'EXACT_R4_IDLE_CANDIDATE_REQUIRED' }
$paritySha = (Get-FileHash -LiteralPath $ParityProofPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($pins.schema_version -ne 1 -or $pins.purpose -ne 'isolated-idle' -or $pins.targets.Count -ne 2 -or $isolated.ok -ne $true -or
    $pins.supervisor_instance_id -notmatch '^[a-f0-9]{24}$' -or $pins.native_pid -le 1 -or
    $pins.native_process_start_token -notmatch '^[0-9]{16,20}$' -or
    $isolated.operation -ne 'isolated-idle-policy-isolate' -or $isolated.activation_epoch_id -ne $pins.activation_epoch -or
    $isolated.parity_sha256 -ne $paritySha -or $isolated.candidate -ne $parity.candidate -or
    $isolated.after.execution_mode -ne 'isolated' -or $isolated.other_scope_unchanged -ne $true) { throw 'EXACT_ISOLATED_POLICY_AND_READY_PINS_REQUIRED' }
$codex = @($pins.targets | Where-Object { $_.workspace_label -eq 'Codex-web' })
if ($codex.Count -ne 1 -or $codex[0].workspace_id -ne $isolated.after.workspace_id -or
    $codex[0].workspace_generation -ne $isolated.after.workspace_generation -or
    $codex[0].execution_mode -ne 'isolated' -or
    $codex[0].exec_policy_sha256 -ne $isolated.after.policy_sha256) { throw 'EXACT_CODEX_POLICY_SCOPE_REQUIRED' }
$autocad = @($pins.targets | Where-Object { $_.workspace_label -eq 'Autocad' })
if ($autocad.Count -ne 1 -or $autocad[0].execution_mode -ne 'native_first') { throw 'EXACT_AUTOCAD_NATIVE_POLICY_REQUIRED' }
$pins | Add-Member -NotePropertyName isolated_idle_approved -NotePropertyValue $true -Force
$receiptPath = Join-Path $PSScriptRoot ('isolated-idle-remote-' + $attemptText + '.ndjson')
$samplePath = Join-Path $PSScriptRoot ('isolated-idle-observation-' + $attemptText + '.json')
$readyPath = Join-Path $PSScriptRoot ('isolated-idle-ready-' + $attemptText + '.json')
$reviewedPinsPath = Join-Path $PSScriptRoot ('isolated-idle-pins-' + $attemptText + '.json')
$observerOutput = Join-Path $PSScriptRoot ('isolated-idle-observer-' + $attemptText + '.ndjson')
$observerError = Join-Path $PSScriptRoot ('isolated-idle-observer-' + $attemptText + '.stderr')
foreach ($file in @($receiptPath, $samplePath, $readyPath, $reviewedPinsPath, $observerOutput, $observerError)) {
    if (Test-Path -LiteralPath $file) { throw 'ATTEMPT_EVIDENCE_EXISTS_DO_NOT_REDISPATCH' }
}
$utf8 = [Text.UTF8Encoding]::new($false)
[IO.File]::WriteAllText($reviewedPinsPath, ($pins | ConvertTo-Json -Depth 20) + [Environment]::NewLine, $utf8)
$sources = [ordered]@{}
foreach ($name in @('run-native-first-canary.py', 'run-parallel-overlap-canary.py', 'run-isolated-idle-canary-timefix.py', 'observe-isolated-idle.py')) {
    $file = Join-Path $PSScriptRoot $name
    $sources[$name] = @{ sha256 = (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant(); bytes = [IO.File]::ReadAllBytes($file) }
}
$base64 = [Convert]::ToBase64String($sources['run-native-first-canary.py'].bytes)
$overlap64 = [Convert]::ToBase64String($sources['run-parallel-overlap-canary.py'].bytes)
$runner64 = [Convert]::ToBase64String($sources['run-isolated-idle-canary-timefix.py'].bytes)
$pinsBytes = [IO.File]::ReadAllBytes($reviewedPinsPath)
$pins64 = [Convert]::ToBase64String($pinsBytes)
$pinsSha = (Get-FileHash -LiteralPath $reviewedPinsPath -Algorithm SHA256).Hash.ToLowerInvariant()
$remoteSource = @"
import base64, types
_BASE_CANARY = types.ModuleType('reviewed_native_canary')
exec(compile(base64.b64decode('$base64'), 'reviewed-run-native-first-canary.py', 'exec'), _BASE_CANARY.__dict__)
_OVERLAP_CANARY = types.ModuleType('reviewed_parallel_canary')
_OVERLAP_CANARY._BASE_CANARY = _BASE_CANARY
exec(compile(base64.b64decode('$overlap64'), 'reviewed-run-parallel-overlap-canary.py', 'exec'), _OVERLAP_CANARY.__dict__)
_REVIEWED_PINS_BYTES = base64.b64decode('$pins64')
exec(compile(base64.b64decode('$runner64'), 'reviewed-run-isolated-idle-canary-timefix.py', 'exec'))
"@
function Quote-NativeArgument([string]$value) {
    if ($value.Contains('"') -or $value.Contains([char]10) -or $value.Contains([char]13)) { throw 'UNSAFE_PROCESS_ARGUMENT' }
    return '"' + $value + '"'
}
$observerArgs = @('-B', (Join-Path $PSScriptRoot 'observe-isolated-idle.py'), '--pins', $reviewedPinsPath,
    '--parity-proof', ([IO.Path]::GetFullPath($ParityProofPath)), '--remote-receipt', $receiptPath,
    '--ready-signal', $readyPath, '--output', $samplePath)
$nativeArguments = ($observerArgs | ForEach-Object { Quote-NativeArgument $_ }) -join ' '
$observer = Start-Process -FilePath ([IO.Path]::GetFullPath($PythonPath)) -ArgumentList $nativeArguments -WindowStyle Hidden -PassThru -RedirectStandardOutput $observerOutput -RedirectStandardError $observerError
$readyDeadline = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() + 15000
while (-not (Test-Path -LiteralPath $readyPath)) {
    if ($observer.HasExited -or [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() -ge $readyDeadline) { throw 'READONLY_OBSERVER_NOT_READY_NO_ACTION_DISPATCHED' }
    Start-Sleep -Milliseconds 200
}
$sshArgs = @('-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5', '-o', 'StrictHostKeyChecking=yes', 'svhome@100.116.112.22',
    'python3', '-B', '-', '--attempt-id', $attemptText, '--reviewed-pins-sha256', $pinsSha,
    '--credential-file', '/home/svhome/.config/codex-control-plane/ubuntu-root-mcp-authorization', '--execute-confirmed-isolated-idle-canary')
$remoteExit = 1
try {
    $remoteSource | & ssh.exe @sshArgs | Tee-Object -FilePath $receiptPath
    $remoteExit = $LASTEXITCODE
    while (-not $observer.HasExited) { Start-Sleep -Milliseconds 500; $observer.Refresh() }
} finally {
    # Never stop a VM, runtime or uncertain original action from this wrapper.
    $receipt = [ordered]@{ operation = 'isolated_idle_canary_wrapper'; observed_at_ms = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();
        attempt_id = $attemptText; remote_exit_code = $remoteExit; observer_exited = $observer.HasExited;
        observer_exit_code = $(if ($observer.HasExited) { $observer.ExitCode } else { $null });
        remote_receipt_path = $receiptPath; observation_path = $samplePath; policy_receipt_path = [IO.Path]::GetFullPath($IsolatedPolicyReceiptPath);
        pins_sha256 = $pinsSha; source_sha256 = @{}; lifecycle_stop_dispatched = $false; restoration_remaining = $true }
    foreach ($name in $sources.Keys) { $receipt.source_sha256[$name] = $sources[$name].sha256 }
    $summaryPath = Join-Path $PSScriptRoot ('isolated-idle-wrapper-' + $attemptText + '.json')
    [IO.File]::WriteAllText($summaryPath, ($receipt | ConvertTo-Json -Depth 10) + [Environment]::NewLine, $utf8)
    Write-Output (ConvertTo-Json -Compress @{ operation = $receipt.operation; remote_exit_code = $remoteExit; report_path = $summaryPath; restoration_remaining = $true })
}
if ($remoteExit -ne 0 -or -not $observer.HasExited -or $observer.ExitCode -ne 0) { exit 1 }
exit 0

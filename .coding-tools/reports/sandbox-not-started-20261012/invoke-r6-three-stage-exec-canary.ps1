# Root-reviewed stage dispatch only. Reuse the same CanaryId for all stages.
# Cold -> warm within 60s. Warm remains alive to renew while root stops owned VM.
param(
    [Parameter(Mandatory = $true)][switch]$ExecuteConfirmedReadyPilot,
    [Parameter(Mandatory = $true)][ValidateSet('cold', 'warm', 'after_stop', 'close')][string]$Stage,
    [Parameter(Mandatory = $true)][guid]$CanaryId,
    [Parameter(Mandatory = $true)][string]$ReviewedHelperSha256,
    [Parameter(Mandatory = $true)][string]$BindingId,
    [Parameter(Mandatory = $true)][string]$WorkspaceGeneration,
    [Parameter(Mandatory = $true)][string]$PilotDecisionId,
    [Parameter(Mandatory = $true)][string]$ActivationEpoch,
    [Parameter(Mandatory = $true)][string]$ProcessInstanceId,
    [Parameter(Mandatory = $true)][string]$ServerInstanceId,
    [Parameter(Mandatory = $true)][string]$LocalToolContractSha256,
    [Parameter(Mandatory = $true)][string]$FacadeContractSha256,
    [Parameter(Mandatory = $true)][int]$ServicePid,
    [int]$WarmHoldSeconds = 600,
    [switch]$ConfirmedSupportedOwnedSandboxStop,
    [string]$StoppedSandboxId,
    [string]$SupportedStopReceiptSha256
)
$ErrorActionPreference = 'Stop'
if (-not $ExecuteConfirmedReadyPilot) { throw 'EXPLICIT_REVIEWED_STAGE_EXECUTION_REQUIRED' }
$reportDirectory = 'E:\DEV\Codex-web\.coding-tools\reports\sandbox-not-started-20261012'
$scriptPath = Join-Path $reportDirectory 'run-r6-three-stage-exec-canary.py'
if ($ReviewedHelperSha256 -notmatch '^[a-f0-9]{64}$' -or (Get-FileHash -LiteralPath $scriptPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ReviewedHelperSha256) { throw 'EXACT_REVIEWED_HELPER_SHA_REQUIRED' }
foreach ($identityValue in @($BindingId, $WorkspaceGeneration, $PilotDecisionId, $ActivationEpoch, $ProcessInstanceId, $ServerInstanceId)) {
    if ($identityValue -notmatch '^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$') { throw 'REMOTE_IDENTITY_ARGUMENT_INVALID' }
}
foreach ($digestValue in @($LocalToolContractSha256, $FacadeContractSha256)) {
    if ($digestValue -notmatch '^[a-f0-9]{64}$') { throw 'REMOTE_DIGEST_ARGUMENT_INVALID' }
}
if ($ServicePid -lt 2 -or $WarmHoldSeconds -lt 0 -or $WarmHoldSeconds -gt 900) { throw 'REMOTE_NUMERIC_ARGUMENT_INVALID' }
if ($Stage -eq 'after_stop' -and (-not $ConfirmedSupportedOwnedSandboxStop -or $StoppedSandboxId -notmatch '^wsb:[a-z0-9]{8}$' -or $SupportedStopReceiptSha256 -notmatch '^[a-f0-9]{64}$')) { throw 'ACTUAL_ROOT_VERIFIED_SUPPORTED_STOP_REQUIRED' }
$canaryText = $CanaryId.ToString('N')
$receiptPath = Join-Path $reportDirectory ('r6-three-stage-' + $canaryText + '-' + $Stage + '.ndjson')
# The protected local reservation prevents a second dispatch with this stage.
# If transport is lost, inspect the durable original handles with observe-only.
$receiptStream = [System.IO.File]::Open($receiptPath, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write)
$writer = [System.IO.StreamWriter]::new($receiptStream, [System.Text.UTF8Encoding]::new($false))
$writer.AutoFlush = $true
$sshArguments = @(
    '-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5', '-o', 'StrictHostKeyChecking=yes',
    'svhome@100.116.112.22', 'python3', '-B', '-',
    '--binding-id', $BindingId,
    '--new-generation', $WorkspaceGeneration,
    '--pilot-decision-id', $PilotDecisionId,
    '--activation-epoch', $ActivationEpoch,
    '--process-instance-id', $ProcessInstanceId,
    '--server-instance-id', $ServerInstanceId,
    '--local-tool-contract-sha256', $LocalToolContractSha256,
    '--facade-schema-version', '32', '--facade-contract-sha256', $FacadeContractSha256,
    '--service-pid', $ServicePid.ToString(), '--canary-id', $canaryText,
    '--credential-file', '/home/svhome/.config/codex-control-plane/ubuntu-root-mcp-authorization',
    '--stage', $Stage, '--hold-after-warm-seconds', $WarmHoldSeconds.ToString(),
    '--execute-confirmed-ready-pilot'
)
if ($Stage -eq 'after_stop') {
    $sshArguments += @('--confirmed-supported-owned-sandbox-stop', '--stopped-sandbox-id', $StoppedSandboxId, '--supported-stop-receipt-sha256', $SupportedStopReceiptSha256)
}
try {
    Get-Content -LiteralPath $scriptPath -Raw | & ssh.exe @sshArguments | ForEach-Object {
        $writer.WriteLine($_)
        Write-Output $_
    }
    $sshExitCode = $LASTEXITCODE
    $wrapperReceipt = ConvertTo-Json -Compress @{ operation = 'r6_three_stage_exec_canary_ssh'; exit_code = $sshExitCode; canary_id = $canaryText; stage = $Stage; helper_sha256 = $ReviewedHelperSha256 }
    $writer.WriteLine($wrapperReceipt)
    Write-Output $wrapperReceipt
} finally {
    $writer.Dispose()
}
exit $sshExitCode

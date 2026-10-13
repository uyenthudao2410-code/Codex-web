# Prepare-only until the root controller reviews and supplies fresh live identity.
# The canonical service credential is read on svhome; its bytes never leave it.
param(
    [Parameter(Mandatory = $true)][switch]$ExecuteConfirmedReadyPilot,
    [Parameter(Mandatory = $true)][string]$BindingId,
    [Parameter(Mandatory = $true)][string]$WorkspaceGeneration,
    [Parameter(Mandatory = $true)][string]$PilotDecisionId,
    [Parameter(Mandatory = $true)][string]$ActivationEpoch,
    [Parameter(Mandatory = $true)][string]$ProcessInstanceId,
    [Parameter(Mandatory = $true)][string]$ServerInstanceId,
    [Parameter(Mandatory = $true)][string]$LocalToolContractSha256,
    [Parameter(Mandatory = $true)][int]$FacadeSchemaVersion,
    [Parameter(Mandatory = $true)][string]$FacadeContractSha256,
    [Parameter(Mandatory = $true)][int]$ServicePid,
    [Parameter(Mandatory = $true)][guid]$AttemptId
)
$ErrorActionPreference = 'Stop'
if (-not $ExecuteConfirmedReadyPilot) { throw 'EXPLICIT_CANARY_EXECUTION_REQUIRED' }
foreach ($identityValue in @($BindingId, $WorkspaceGeneration, $PilotDecisionId, $ActivationEpoch, $ProcessInstanceId, $ServerInstanceId)) {
    if ($identityValue -notmatch '^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$') { throw 'REMOTE_IDENTITY_ARGUMENT_INVALID' }
}
foreach ($digestValue in @($LocalToolContractSha256, $FacadeContractSha256)) {
    if ($digestValue -notmatch '^[a-f0-9]{64}$') { throw 'REMOTE_DIGEST_ARGUMENT_INVALID' }
}
if ($ServicePid -lt 2 -or $FacadeSchemaVersion -lt 32) { throw 'REMOTE_SERVICE_ARGUMENT_INVALID' }
$reportDirectory = 'E:\DEV\Codex-web\.coding-tools\reports\shared-write-exec-20261012'
$scriptPath = Join-Path $reportDirectory 'run-shared-write-exec-canary.py'
$attemptText = $AttemptId.ToString('N')
$receiptPath = Join-Path $reportDirectory ('shared-write-exec-receipt-' + $attemptText + '.ndjson')
$targetPath = Join-Path $reportDirectory 'shared-write-proof.txt'
if (Test-Path -LiteralPath $receiptPath) { throw 'LOCAL_CANARY_RECEIPT_ALREADY_EXISTS_DO_NOT_REDISPATCH' }
if (Test-Path -LiteralPath $targetPath) { throw 'SCRATCH_TARGET_ALREADY_EXISTS_DO_NOT_OVERWRITE' }
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
    '--facade-schema-version', $FacadeSchemaVersion.ToString(),
    '--facade-contract-sha256', $FacadeContractSha256,
    '--service-pid', $ServicePid.ToString(),
    '--attempt-id', $attemptText,
    '--credential-file', '/home/svhome/.config/codex-control-plane/ubuntu-root-mcp-authorization',
    '--execute-confirmed-ready-pilot'
)
Get-Content -LiteralPath $scriptPath -Raw | & ssh.exe @sshArguments | Tee-Object -FilePath $receiptPath
$sshExitCode = $LASTEXITCODE
Write-Output (ConvertTo-Json -Compress @{ operation = 'shared_write_exec_canary_ssh'; exit_code = $sshExitCode; attempt_id = $attemptText })
exit $sshExitCode

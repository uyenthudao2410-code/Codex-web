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
foreach ($identityValue in @($BindingId, $WorkspaceGeneration, $PilotDecisionId, $ActivationEpoch)) {
    if ($identityValue -notmatch '^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$') { throw 'REMOTE_IDENTITY_ARGUMENT_INVALID' }
}
foreach ($identityValue in @($ProcessInstanceId, $ServerInstanceId)) {
    if ($identityValue -notmatch '^[A-Za-z0-9_-]{1,128}$') { throw 'REMOTE_RUNTIME_IDENTITY_ARGUMENT_INVALID' }
}
foreach ($digestValue in @($LocalToolContractSha256, $FacadeContractSha256)) {
    if ($digestValue -notmatch '^[a-f0-9]{64}$') { throw 'REMOTE_DIGEST_ARGUMENT_INVALID' }
}
if ($ServicePid -lt 2 -or $FacadeSchemaVersion -lt 32) { throw 'REMOTE_SERVICE_ARGUMENT_INVALID' }
if ($WorkspaceGeneration -ne 'generation_03f9c04f1b14414fa4bfa7d91cc8ea7a') { throw 'AUTOCAD_GENERATION_CHANGED' }
$reportDirectory = 'E:\DEV\Codex-web\.coding-tools\reports\folder-access-20261012-r9\canary'
$scriptPath = Join-Path $reportDirectory 'run-autocad-exec-only-canary-r9d.py'
if ((Get-FileHash -LiteralPath $scriptPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne '9d1903d588fddcd6c979c4c4f3e868c7156219c924717d8e6d502a1778ceb4d6') { throw 'REVIEWED_CANARY_SCRIPT_CHANGED' }
$attemptText = $AttemptId.ToString('N')
$receiptPath = Join-Path $reportDirectory ('autocad-exec-only-receipt-r9d-' + $attemptText + '.ndjson')
$targetPath = 'E:\DEV\Autocad\mcp-access-smoke-20261012-r9d.txt'
if (Test-Path -LiteralPath $receiptPath) { throw 'LOCAL_CANARY_RECEIPT_ALREADY_EXISTS_DO_NOT_REDISPATCH' }
if (-not (Test-Path -LiteralPath $targetPath)) { throw 'EXISTING_VERIFIED_R9D_FILE_REQUIRED' }
if ((Get-FileHash -LiteralPath $targetPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne '3a42ea5c3e68101db07001a265b9fb4fcbbc0021ed965139dcf10ea99ba73023') { throw 'EXISTING_VERIFIED_R9D_FILE_CHANGED' }
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
Write-Output (ConvertTo-Json -Compress @{ operation = 'autocad_exec_only_canary_ssh'; exit_code = $sshExitCode; attempt_id = $attemptText })
exit $sshExitCode

# Execute only after the original partial receipt has been reviewed.  This
# wrapper never supplies an original action id and refuses a reused receipt.
param(
    [Parameter(Mandatory = $true)][switch]$ExecuteConfirmedContinuation,
    [Parameter(Mandatory = $true)][string]$ReadyPinsPath,
    [Parameter(Mandatory = $true)][string]$FailedReceiptPath,
    [Parameter(Mandatory = $true)][string]$FailedReceiptSha256,
    [Parameter(Mandatory = $true)][guid]$AttemptId
)
$ErrorActionPreference = 'Stop'
if (-not $ExecuteConfirmedContinuation) { throw 'EXPLICIT_CONTINUATION_EXECUTION_REQUIRED' }
$root = 'E:\DEV\Codex-web'
$here = $PSScriptRoot
$scriptPath = Join-Path $here 'run-native-exec-continuation.py'
$basePath = Join-Path $here 'run-native-first-canary.py'
$receiptPath = Join-Path $here ('continuation-receipt-' + $AttemptId.ToString('N') + '.ndjson')
if (Test-Path -LiteralPath $receiptPath) { throw 'ATTEMPT_RECEIPT_EXISTS_DO_NOT_REDISPATCH' }
$failed = [IO.Path]::GetFullPath($FailedReceiptPath)
if (-not $failed.StartsWith(([IO.Path]::GetFullPath($here) + '\'), [StringComparison]::OrdinalIgnoreCase) -or
    -not (Test-Path -LiteralPath $failed)) { throw 'FAILED_RECEIPT_MUST_BE_R4_EVIDENCE' }
$failedHash = (Get-FileHash -LiteralPath $failed -Algorithm SHA256).Hash.ToLowerInvariant()
if ($failedHash -ne $FailedReceiptSha256.ToLowerInvariant()) { throw 'FAILED_RECEIPT_HASH_MISMATCH' }
$pins = Get-Content -LiteralPath $ReadyPinsPath -Raw | ConvertFrom-Json
foreach ($field in @('principal_id','grant_id','device_id','workspace_id','binding_id','workspace_generation','pilot_decision_id','activation_epoch','process_instance_id','server_instance_id')) {
    if ([string]$pins.$field -notmatch '^[A-Za-z0-9_-][A-Za-z0-9_-]{0,127}$') { throw 'REMOTE_IDENTITY_ARGUMENT_INVALID' }
}
foreach ($field in @('local_tool_contract_sha256','facade_contract_sha256','serving_mcp_facade_sha256','serving_node_agent_sha256')) {
    if ([string]$pins.$field -notmatch '^[a-f0-9]{64}$') { throw 'REMOTE_DIGEST_ARGUMENT_INVALID' }
}
if ($pins.service_pid -lt 2 -or $pins.facade_schema_version -lt 32 -or $pins.activation_verified -ne $true -or
    $pins.workspace_label -ne 'Codex-web' -or $pins.trusted_build_explicitly_approved -ne $true) { throw 'EXACT_READY_CONTINUATION_PINS_REQUIRED' }
$fixture = [IO.Path]::GetFullPath((Join-Path $root 'tests\fixtures\native-first-canary'))
if (Test-Path -LiteralPath (Join-Path $fixture 'build-artifact.txt')) { throw 'BUILD_ARTIFACT_EXISTS_DO_NOT_REDISPATCH' }
$baseHash = (Get-FileHash -LiteralPath $basePath -Algorithm SHA256).Hash.ToLowerInvariant()
$expectedBaseHash = '3b3c6cc3dee35d37a76a0237bab9a653766db30ba82caa95c09ef85311b84c66'
if ($baseHash -ne $expectedBaseHash) { throw 'REVIEWED_BASE_HARNESS_CHANGED' }
$attempt = $AttemptId.ToString('N')
$pinsBytes = [IO.File]::ReadAllBytes([IO.Path]::GetFullPath($ReadyPinsPath))
$scriptBytes = [IO.File]::ReadAllBytes($scriptPath)
$baseBytes = [IO.File]::ReadAllBytes($basePath)
$failedBytes = [IO.File]::ReadAllBytes($failed)
$remoteSource = @"
import base64, types
_BASE_CANARY = types.ModuleType('reviewed_native_canary')
exec(compile(base64.b64decode('$([Convert]::ToBase64String($baseBytes))'), 'reviewed-run-native-first-canary.py', 'exec'), _BASE_CANARY.__dict__)
_FAILED_RECEIPT_BYTES = base64.b64decode('$([Convert]::ToBase64String($failedBytes))')
_REVIEWED_PINS_BYTES = base64.b64decode('$([Convert]::ToBase64String($pinsBytes))')
exec(compile(base64.b64decode('$([Convert]::ToBase64String($scriptBytes))'), 'run-native-exec-continuation.py', 'exec'))
"@
$ssh = @('-T','-o','BatchMode=yes','-o','ConnectTimeout=5','-o','StrictHostKeyChecking=yes','svhome@100.116.112.22','python3','-B','-',
    ('--principal-id=' + [string]$pins.principal_id),('--grant-id=' + [string]$pins.grant_id),('--device-id=' + [string]$pins.device_id),
    ('--workspace-id=' + [string]$pins.workspace_id),('--binding-id=' + [string]$pins.binding_id),('--workspace-generation=' + [string]$pins.workspace_generation),
    ('--pilot-decision-id=' + [string]$pins.pilot_decision_id),('--activation-epoch=' + [string]$pins.activation_epoch),('--process-instance-id=' + [string]$pins.process_instance_id),
    ('--server-instance-id=' + [string]$pins.server_instance_id),('--local-tool-contract-sha256=' + [string]$pins.local_tool_contract_sha256),
    ('--facade-contract-sha256=' + [string]$pins.facade_contract_sha256),('--serving-mcp-facade-sha256=' + [string]$pins.serving_mcp_facade_sha256),
    ('--serving-node-agent-sha256=' + [string]$pins.serving_node_agent_sha256),('--facade-schema-version=' + [string]$pins.facade_schema_version),
    ('--service-pid=' + [string]$pins.service_pid),'--failed-receipt','embedded-failed-receipt',('--failed-receipt-sha256=' + $FailedReceiptSha256.ToLowerInvariant()),
    '--attempt-id',$attempt,'--credential-file','/home/svhome/.config/codex-control-plane/ubuntu-root-mcp-authorization',
    '--trusted-build-explicitly-approved','--execute-confirmed-continuation')
$remoteSource | & ssh.exe @ssh | Tee-Object -FilePath $receiptPath
if ($LASTEXITCODE -ne 0) { throw 'CONTINUATION_FAILED_INSPECT_RECEIPT' }
Write-Output (ConvertTo-Json -Compress @{operation='native_exec_continuation_ssh';attempt_id=$attempt;receipt_path=$receiptPath;failed_receipt_sha256=$FailedReceiptSha256.ToLowerInvariant()})

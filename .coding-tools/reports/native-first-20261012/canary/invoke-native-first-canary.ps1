# Execute only after reviewed fresh activation pins. Credential stays on Ubuntu.
param(
    [Parameter(Mandatory = $true)][switch]$ExecuteConfirmedReadyPilot,
    [Parameter(Mandatory = $true)][string]$ReadyPinsPath,
    [Parameter(Mandatory = $true)][guid]$AttemptId,
    [switch]$IncludeApprovedBuild
)
$ErrorActionPreference = 'Stop'
if (-not $ExecuteConfirmedReadyPilot) { throw 'EXPLICIT_CANARY_EXECUTION_REQUIRED' }
$reportDirectory = $PSScriptRoot
$repository = 'E:\DEV\Codex-web'
$scriptPath = Join-Path $reportDirectory 'run-native-first-canary.py'
$manifestPath = Join-Path $reportDirectory 'fixture-preparation.json'
$attemptText = $AttemptId.ToString('N')
$receiptPath = Join-Path $reportDirectory ('shared-mcp-receipt-' + $attemptText + '.ndjson')
$censusPath = Join-Path $reportDirectory ('sandbox-census-' + $attemptText + '.json')
if ((Test-Path -LiteralPath $receiptPath) -or (Test-Path -LiteralPath $censusPath)) { throw 'ATTEMPT_RECEIPT_EXISTS_DO_NOT_REDISPATCH' }
$pins = Get-Content -LiteralPath $ReadyPinsPath -Raw | ConvertFrom-Json
$identityFields = @('principal_id', 'grant_id', 'device_id', 'workspace_id', 'binding_id', 'workspace_generation', 'pilot_decision_id', 'activation_epoch', 'process_instance_id', 'server_instance_id')
$digestFields = @('local_tool_contract_sha256', 'facade_contract_sha256', 'serving_mcp_facade_sha256', 'serving_node_agent_sha256')
foreach ($field in $identityFields) {
    if ($pins.$field -notmatch '^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$') { throw 'REMOTE_IDENTITY_ARGUMENT_INVALID' }
}
foreach ($field in $digestFields) {
    if ($pins.$field -notmatch '^[a-f0-9]{64}$') { throw 'REMOTE_DIGEST_ARGUMENT_INVALID' }
}
if ($pins.service_pid -lt 2 -or $pins.facade_schema_version -lt 32) { throw 'REMOTE_SERVICE_ARGUMENT_INVALID' }
if ($pins.activation_verified -ne $true -or $pins.workspace_label -ne 'Codex-web') { throw 'EXACT_CODEX_WORKSPACE_ACTIVATION_REQUIRED' }
if ($IncludeApprovedBuild -and $pins.trusted_build_explicitly_approved -ne $true) { throw 'EXACT_TRUSTED_BUILD_APPROVAL_REQUIRED' }
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if ($manifest.prepared -ne $true -or $manifest.fixture -ne 'tests/fixtures/native-first-canary' -or $manifest.files.Count -ne 101) { throw 'FIXTURE_PREPARATION_NOT_VERIFIED' }
if ((Get-FileHash -LiteralPath $scriptPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $manifest.harness_sha256) { throw 'PREPARED_HARNESS_CHANGED' }
$fixtureRoot = [IO.Path]::GetFullPath((Join-Path $repository 'tests\fixtures\native-first-canary'))
if (((Get-Item -LiteralPath $fixtureRoot).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'FIXTURE_DIRECTORY_REPARSE_POINT_DENIED' }
if (Test-Path -LiteralPath (Join-Path $fixtureRoot 'build-artifact.txt')) { throw 'BUILD_ARTIFACT_EXISTS_DO_NOT_REDISPATCH' }
foreach ($record in $manifest.files) {
    if ($record.path -notmatch '^tests/fixtures/native-first-canary/(file-[0-9]{3}\.txt|trusted-build\.js)$') { throw 'FIXTURE_MANIFEST_PATH_INVALID' }
    $localPath = [IO.Path]::GetFullPath((Join-Path $repository $record.path))
    if (-not $localPath.StartsWith($fixtureRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'FIXTURE_PATH_OUTSIDE_TARGET' }
    $info = Get-Item -LiteralPath $localPath
    if (($info.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $info.Length -ne $record.size_bytes -or (Get-FileHash -LiteralPath $localPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $record.sha256) { throw 'SEED_FILE_CHANGED' }
}
function Get-SandboxCensus {
    $items = @(Get-Process | Where-Object { $_.ProcessName -match '^(WindowsSandbox.*|vmmem.*)$' } | ForEach-Object {
        @{ process_name = $_.ProcessName; pid = $_.Id; working_set_bytes = $_.WorkingSet64; private_memory_bytes = $_.PrivateMemorySize64 }
    })
    return @{ observed_at_ms = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds(); process_count = $items.Count; processes = $items; command_lines_collected = $false }
}
$sshArguments = @('-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5', '-o', 'StrictHostKeyChecking=yes', 'svhome@100.116.112.22', 'python3', '-B', '-')
foreach ($field in @($identityFields + $digestFields)) {
    $sshArguments += @('--' + $field.Replace('_', '-'), [string]$pins.$field)
}
$sshArguments += @('--facade-schema-version', [string]$pins.facade_schema_version, '--service-pid', [string]$pins.service_pid, '--attempt-id', $attemptText, '--credential-file', '/home/svhome/.config/codex-control-plane/ubuntu-root-mcp-authorization', '--execute-confirmed-ready-pilot')
if ($IncludeApprovedBuild) { $sshArguments += '--include-approved-build' }
$before = Get-SandboxCensus
$exitCode = 1
try {
    Get-Content -LiteralPath $scriptPath -Raw | & ssh.exe @sshArguments | Tee-Object -FilePath $receiptPath
    $exitCode = $LASTEXITCODE
} finally {
    $after = Get-SandboxCensus
    $census = @{ operation = 'native_first_windows_sandbox_census'; attempt_id = $attemptText; before = $before; after = $after; ssh_exit_code = $exitCode; limitation = 'Two process samples cannot exclude transient VM startup; native routing receipts are the execution backend evidence.' }
    $census | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $censusPath -Encoding UTF8
    Write-Output (ConvertTo-Json -Compress @{ operation = 'native_first_canary_ssh'; attempt_id = $attemptText; exit_code = $exitCode; census_path = $censusPath; receipt_path = $receiptPath })
}
exit $exitCode

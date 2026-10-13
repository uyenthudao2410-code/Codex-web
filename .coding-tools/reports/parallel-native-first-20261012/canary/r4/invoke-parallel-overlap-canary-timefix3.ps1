# Source/pins are passed in memory. The service credential remains on Ubuntu.
param(
    [Parameter(Mandatory = $true)][switch]$ExecuteConfirmedReadyTwoRootCanary,
    [Parameter(Mandatory = $true)][string]$ReadyPinsPath,
    [Parameter(Mandatory = $true)][string]$FixtureManifestPath,
    [Parameter(Mandatory = $true)][guid]$AttemptId
)
$ErrorActionPreference = 'Stop'
if (-not $ExecuteConfirmedReadyTwoRootCanary) { throw 'EXPLICIT_TWO_ROOT_CANARY_EXECUTION_REQUIRED' }
$attemptText = $AttemptId.ToString('N')
$receiptPath = Join-Path $PSScriptRoot ('parallel-overlap-receipt-' + $attemptText + '.ndjson')
$censusPath = Join-Path $PSScriptRoot ('parallel-overlap-census-' + $attemptText + '.json')
if ((Test-Path -LiteralPath $receiptPath) -or (Test-Path -LiteralPath $censusPath)) { throw 'ATTEMPT_RECEIPT_EXISTS_DO_NOT_REDISPATCH' }
$pinsBytes = [IO.File]::ReadAllBytes([IO.Path]::GetFullPath($ReadyPinsPath))
if ($pinsBytes.Length -gt 32768) { throw 'REVIEWED_PINS_TOO_LARGE' }
$pins = [Text.Encoding]::UTF8.GetString($pinsBytes).TrimStart([char]0xFEFF) | ConvertFrom-Json
$manifest = Get-Content -LiteralPath $FixtureManifestPath -Raw | ConvertFrom-Json
if ($manifest.prepared -ne $true -or $manifest.targets.Count -ne 2 -or $pins.targets.Count -ne 2) { throw 'TWO_ROOT_FIXTURE_PREPARATION_REQUIRED' }
$labels = @('Codex-web', 'Autocad')
if ((($pins.targets.workspace_label | Sort-Object) -join ',') -ne (($labels | Sort-Object) -join ',')) { throw 'EXACT_TWO_AUTHORIZED_TARGETS_REQUIRED' }
foreach ($name in @('run-native-first-canary-timefix2.py', 'run-parallel-overlap-canary-timefix3.py')) {
    if ((Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $name) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $manifest.source_sha256.$name) { throw 'PREPARED_CANARY_SOURCE_CHANGED' }
}
foreach ($target in $pins.targets) {
    $prepared = @($manifest.targets | Where-Object { $_.workspace_label -eq $target.workspace_label })
    if ($prepared.Count -ne 1 -or $prepared[0].fixture -ne 'tests/fixtures/parallel-native-overlap-20261012' -or $prepared[0].files.Count -ne 2) { throw 'EXACT_TARGET_FIXTURE_NOT_PREPARED' }
    if ($target.activation_verified -ne $true -or $target.native_fixture_explicitly_approved -ne $true -or $target.native_source_sha256 -ne $prepared[0].native_source_sha256) { throw 'EXACT_TARGET_NATIVE_SOURCE_APPROVAL_REQUIRED' }
    $repositoryRoot = [IO.Path]::GetFullPath([string]$prepared[0].repository_root)
    $gitRoot = (& git -C $repositoryRoot rev-parse --show-toplevel).Trim()
    if ($LASTEXITCODE -ne 0 -or [IO.Path]::GetFullPath($gitRoot) -ne $repositoryRoot) { throw 'REPOSITORY_ROOT_MISMATCH' }
    if ((& git -C $repositoryRoot rev-parse HEAD).Trim() -ne $prepared[0].git_head) { throw 'PREPARED_REPOSITORY_HEAD_CHANGED' }
    $fixtureRoot = [IO.Path]::GetFullPath((Join-Path $repositoryRoot $prepared[0].fixture))
    $currentPath = $fixtureRoot
    while ($currentPath.Length -ge $repositoryRoot.Length) {
        if (((Get-Item -LiteralPath $currentPath).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'FIXTURE_REPARSE_ANCESTOR_DENIED' }
        if ($currentPath -eq $repositoryRoot) { break }
        $currentPath = [IO.Path]::GetDirectoryName($currentPath)
    }
    foreach ($record in $prepared[0].files) {
        if ($record.path -notmatch '^tests/fixtures/parallel-native-overlap-20261012/(probe\.txt|hold\.cjs)$') { throw 'FIXTURE_MANIFEST_PATH_INVALID' }
        $localPath = [IO.Path]::GetFullPath((Join-Path $repositoryRoot $record.path))
        if (-not $localPath.StartsWith($fixtureRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'FIXTURE_PATH_OUTSIDE_TARGET' }
        $info = Get-Item -LiteralPath $localPath
        if (($info.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $info.Length -ne $record.size_bytes -or (Get-FileHash -LiteralPath $localPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $record.sha256) { throw 'SEED_FILE_CHANGED' }
    }
}
$baseBytes = [IO.File]::ReadAllBytes((Join-Path $PSScriptRoot 'run-native-first-canary-timefix2.py'))
$runnerBytes = [IO.File]::ReadAllBytes((Join-Path $PSScriptRoot 'run-parallel-overlap-canary-timefix3.py'))
$base64 = [Convert]::ToBase64String($baseBytes)
$runner64 = [Convert]::ToBase64String($runnerBytes)
$pins64 = [Convert]::ToBase64String($pinsBytes)
$pinsSha = (Get-FileHash -LiteralPath $ReadyPinsPath -Algorithm SHA256).Hash.ToLowerInvariant()
$remoteSource = @"
import base64, types
_BASE_CANARY = types.ModuleType('reviewed_native_canary')
exec(compile(base64.b64decode('$base64'), 'reviewed-run-native-first-canary-timefix2.py', 'exec'), _BASE_CANARY.__dict__)
_REVIEWED_PINS_BYTES = base64.b64decode('$pins64')
exec(compile(base64.b64decode('$runner64'), 'reviewed-run-parallel-overlap-canary-timefix3.py', 'exec'))
"@
function Get-SandboxCensus {
    $items = @(Get-Process | Where-Object { $_.ProcessName -match '^(WindowsSandbox.*|vmmem.*)$' } | ForEach-Object {
        @{ process_name = $_.ProcessName; pid = $_.Id; working_set_bytes = $_.WorkingSet64; private_memory_bytes = $_.PrivateMemorySize64 }
    })
    return @{ observed_at_ms = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds(); process_count = $items.Count; processes = $items; command_lines_collected = $false }
}
$sshArguments = @('-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5', '-o', 'StrictHostKeyChecking=yes', 'svhome@100.116.112.22', 'python3', '-B', '-', '--attempt-id', $attemptText, '--reviewed-pins-sha256', $pinsSha, '--credential-file', '/home/svhome/.config/codex-control-plane/ubuntu-root-mcp-authorization', '--execute-confirmed-ready-two-root-canary')
$before = Get-SandboxCensus
$exitCode = 1
try {
    $remoteSource | & ssh.exe @sshArguments | Tee-Object -FilePath $receiptPath
    $exitCode = $LASTEXITCODE
} finally {
    $after = Get-SandboxCensus
    @{ operation = 'parallel_overlap_windows_sandbox_census'; attempt_id = $attemptText; before = $before; after = $after; ssh_exit_code = $exitCode; limitation = 'Two process samples cannot exclude transient VM startup; exact native receipts and overlapping same-node script intervals are the backend/overlap evidence.' } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $censusPath -Encoding UTF8
    Write-Output (ConvertTo-Json -Compress @{ operation = 'parallel_overlap_canary_ssh'; attempt_id = $attemptText; exit_code = $exitCode; receipt_path = $receiptPath; census_path = $censusPath })
}
exit $exitCode

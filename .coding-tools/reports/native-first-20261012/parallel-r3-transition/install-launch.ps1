param(
    [ValidateSet('InstallSupervisor', 'LaunchUi')][string]$Operation,
    [string]$RetirementReceiptPath,
    [string]$InstallReceiptPath,
    [string]$ParityProofPath,
    [string]$SmokeProofPath,
    [switch]$Apply
)
$ErrorActionPreference = 'Stop'
if ($env:PYTHONDONTWRITEBYTECODE -ne '1') { throw 'PYTHONDONTWRITEBYTECODE=1 must be inherited for the immutable package handoff.' }
$OldCandidate = 'E:\DEV\Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-parallel-native-1012-r2\win-unpacked'
$NewCandidate = 'E:\DEV\Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-parallel-native-1012-r3\win-unpacked'
$NewExe = Join-Path $NewCandidate 'Coding Tools MCP.exe'
$ExpectedOldPid = 35428
$ExpectedOldStartToken = '134362815903498960'
$ExpectedOldInstance = 'a233b450199c09cd3118fb4ca2d7068b'
$ExpectedOldInstallation = '1f61bc22f8a5b5c999710b319733ce8983f2ab6ab90ee6f7ab447f615b3facbb'
function Read-BoundedReceipt([string]$ReceiptPath) {
    if (-not [IO.Path]::IsPathRooted($ReceiptPath)) { throw 'An absolute evidence receipt is required.' }
    $ResolvedReceiptPath = [IO.Path]::GetFullPath($ReceiptPath)
    $EvidenceRoot = 'E:\DEV\Codex-web\.coding-tools\reports\native-first-20261012\'
    if (-not $ResolvedReceiptPath.StartsWith($EvidenceRoot, [StringComparison]::OrdinalIgnoreCase) -or
        (Get-Item -LiteralPath $ResolvedReceiptPath).Length -gt 2097152) { throw 'A bounded native-first evidence receipt is required.' }
    Get-Content -LiteralPath $ResolvedReceiptPath -Raw | ConvertFrom-Json
}
$Parity = Read-BoundedReceipt $ParityProofPath
$Smoke = Read-BoundedReceipt $SmokeProofPath
$ExeSha = (Get-FileHash -LiteralPath $NewExe -Algorithm SHA256).Hash.ToLowerInvariant()
$AsarSha = (Get-FileHash -LiteralPath (Join-Path $NewCandidate 'resources\app.asar') -Algorithm SHA256).Hash.ToLowerInvariant()
if ($Parity.ok -ne $true -or $Parity.proof_kind -ne 'exact_source_package_parity' -or $Parity.candidate -ne $NewCandidate -or
    $Parity.executable_sha256 -ne $ExeSha -or $Parity.app_asar_sha256 -ne $AsarSha -or
    $Smoke.ok -ne $true -or $Smoke.candidate -ne $NewCandidate -or $Smoke.sha256.executable -ne $ExeSha -or
    $Smoke.sha256.app_asar -ne $AsarSha -or $Smoke.sha256.source_package_parity_receipt -ne (Get-FileHash -LiteralPath $ParityProofPath -Algorithm SHA256).Hash.ToLowerInvariant()) { throw 'The exact final package requires source parity and isolated smoke proof.' }
if (-not $Apply) {
    [pscustomobject]@{operation=$Operation; apply=$false; package_verified=$true; runtime_effects=0} | ConvertTo-Json -Compress
    exit 0
}
$Retired = Read-BoundedReceipt $RetirementReceiptPath
$RetirementAgeMs = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() - [long]$Retired.observed_at_ms
if ($Retired.ok -ne $true -or $Retired.operation -ne 'retire' -or $Retired.candidate -ne $OldCandidate -or
    $Retired.receipt.owner.owner_pid -ne $ExpectedOldPid -or $Retired.receipt.owner.owner_process_start_token -ne $ExpectedOldStartToken -or
    $Retired.receipt.owner.instance_id -ne $ExpectedOldInstance -or $Retired.receipt.owner.installation_id -ne $ExpectedOldInstallation -or
    $Retired.receipt.retirement.identity.pid -ne $ExpectedOldPid -or $Retired.receipt.retirement.identity.process_start_token -ne $ExpectedOldStartToken -or
    $Retired.receipt.retirement.state -ne 'terminated' -or $Retired.receipt.retirement.exit_state -ne 'exited' -or
    $Retired.receipt.stopped_census.safe -ne $true -or $Retired.receipt.durable_state_deleted -ne $false -or
    $Retired.receipt.ui_stopped.alive -ne $false -or $Retired.receipt.final_candidate -ne $NewCandidate -or
    $Retired.receipt.final_package.executable_sha256 -ne $ExeSha -or $Retired.receipt.final_package.app_asar_sha256 -ne $AsarSha -or
    $RetirementAgeMs -lt 0 -or $RetirementAgeMs -gt 900000) { throw 'A fresh exact r2 retirement receipt and quiescent census are required.' }
if (Get-Process -Id $ExpectedOldPid -ErrorAction SilentlyContinue) { throw 'The retired PID is live; refusing installation replacement.' }
$DataRoot = Join-Path ([Environment]::GetFolderPath('ApplicationData')) 'web-mcp-assistant'
$ManifestPath = Join-Path $DataRoot 'recovery-supervisor\manifest.json'
$DescriptorPath = Join-Path $DataRoot 'recovery-host.json'
if ($Operation -eq 'InstallSupervisor') {
    $Manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
    if ($Manifest.mode -ne 'packaged' -or $Manifest.app_root -ne $OldCandidate -or
        (Get-FileHash -LiteralPath $ManifestPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $Retired.receipt.manifest_sha256 -or
        -not (Test-Path -LiteralPath (Join-Path $DataRoot 'recovery-supervisor\stop.request'))) { throw 'The exact stopped r2 supervisor changed.' }
    if (Test-Path -LiteralPath $DescriptorPath) {
        $Descriptor = Get-Content -LiteralPath $DescriptorPath -Raw | ConvertFrom-Json
        if ($Descriptor.owner_pid -ne $ExpectedOldPid -or $Descriptor.instance_id -ne $ExpectedOldInstance -or
            $Descriptor.installation_id -ne $ExpectedOldInstallation -or $Descriptor.owner_process_start_token -ne $ExpectedOldStartToken) { throw 'The retired descriptor changed after the exact stop.' }
    }
    $Supervisor = Join-Path $NewCandidate 'resources\resources\recovery-supervisor\recovery-supervisor.ps1'
    $PowerShell = Join-Path ([Environment]::GetFolderPath('System')) 'WindowsPowerShell\v1.0\powershell.exe'
    $Output = & $PowerShell -NoLogo -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File $Supervisor -Action Install -Packaged -AppRoot $NewCandidate -Executable $NewExe
    if ($LASTEXITCODE -ne 0) { throw 'Final supervisor installation failed.' }
    $Result = ($Output -join [Environment]::NewLine) | ConvertFrom-Json
    $Manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
    if ($Result.installed -ne $true -or $Manifest.mode -ne 'packaged' -or $Manifest.app_root -ne $NewCandidate -or
        $Manifest.executable -ne $NewExe -or $Manifest.executable_sha256 -ne $ExeSha) { throw 'The installed supervisor does not target the final verified package.' }
    $Receipt = [ordered]@{operation='install_parallel_supervisor'; ok=$true; observed_at=[DateTimeOffset]::UtcNow.ToString('o'); observed_at_ms=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds(); candidate=$NewCandidate; installed=$Result.installed; manifest_sha256=(Get-FileHash -LiteralPath $ManifestPath -Algorithm SHA256).Hash.ToLowerInvariant(); retirement_receipt=[IO.Path]::GetFullPath($RetirementReceiptPath)}
} else {
    $Installed = Read-BoundedReceipt $InstallReceiptPath
    $Manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
    if ($Installed.ok -ne $true -or $Installed.operation -ne 'install_parallel_supervisor' -or $Installed.candidate -ne $NewCandidate -or
        $Manifest.app_root -ne $NewCandidate -or $Manifest.executable -ne $NewExe -or
        (Get-FileHash -LiteralPath $ManifestPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $Installed.manifest_sha256) { throw 'The exact new supervisor installation receipt is required.' }
    $PriorNodeFlag = $env:ELECTRON_RUN_AS_NODE
    try {
        Remove-Item Env:ELECTRON_RUN_AS_NODE -ErrorAction SilentlyContinue
        $Ui = Start-Process -FilePath $NewExe -WorkingDirectory $NewCandidate -WindowStyle Hidden -PassThru
    } finally {
        if ($null -eq $PriorNodeFlag) { Remove-Item Env:ELECTRON_RUN_AS_NODE -ErrorAction SilentlyContinue } else { $env:ELECTRON_RUN_AS_NODE = $PriorNodeFlag }
    }
    $Receipt = [ordered]@{operation='launch_parallel_ui'; ok=$true; observed_at=[DateTimeOffset]::UtcNow.ToString('o'); observed_at_ms=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds(); candidate=$NewCandidate; spawned_pid=$Ui.Id; install_receipt=[IO.Path]::GetFullPath($InstallReceiptPath); readiness_not_inferred=$true}
}
$OutputPath = Join-Path $PSScriptRoot ($Receipt.operation + '-' + [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() + '.json')
$Receipt.report_path = $OutputPath
[IO.File]::WriteAllText($OutputPath, ($Receipt | ConvertTo-Json -Depth 10) + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
$Receipt | ConvertTo-Json -Depth 10 -Compress

param(
    [ValidateSet('InstallSupervisor', 'LaunchUi')][string]$Operation,
    [string]$RetirementReceiptPath,
    [string]$InstallReceiptPath,
    [switch]$Apply
)
$ErrorActionPreference = 'Stop'
$PriorCandidate = 'E:\DEV\Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-machine-folder-access-1012-r9b\win-unpacked'
$NewCandidate = 'E:\DEV\Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-machine-folder-access-1012-r9c\win-unpacked'
$Exe = Join-Path $NewCandidate 'Coding Tools MCP.exe'
$ExpectedExeSha = '88a36a0c15cc5eb97657c8e68554f07aa7704cfaab9fd0ab2078ea4423f19bf2'
$ExpectedAsarSha = '45903d28f4c7e0415ca30857992e5b34c66e1f7f597822c35036874df7dd78cd'
$ExpectedAdapterSha = '3147cb5d6a4f1a9ca908a240f7955b8598cdde0e4258e031a348eae77d8521d9'
function Read-TransitionReceipt([string]$ReceiptPath) {
    $Resolved = [IO.Path]::GetFullPath($ReceiptPath)
    if (-not $Resolved.StartsWith($PSScriptRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -or
        (Get-Item -LiteralPath $Resolved).Length -gt 65536) { throw 'A bounded receipt from this transition directory is required.' }
    Get-Content -LiteralPath $Resolved -Raw | ConvertFrom-Json
}
if ((Get-FileHash -LiteralPath $Exe -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedExeSha -or
    (Get-FileHash -LiteralPath (Join-Path $NewCandidate 'resources\app.asar') -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedAsarSha -or
    (Get-FileHash -LiteralPath (Join-Path $NewCandidate 'resources\resources\coding-tools-mcp\coding_tools_mcp\windows_mxc_state_aware.py') -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedAdapterSha) { throw 'The r9c package changed after verification.' }
if (-not $Apply) {
    [pscustomobject]@{operation=$Operation; apply=$false; package_verified=$true; runtime_effects=0} | ConvertTo-Json -Compress
    exit 0
}
$Retired = Read-TransitionReceipt $RetirementReceiptPath
$RetirementTimestamp = if ($Retired.observed_at -is [DateTime]) { [DateTimeOffset]::new($Retired.observed_at) } else { [DateTimeOffset]::Parse($Retired.observed_at, [Globalization.CultureInfo]::InvariantCulture) }
$RetirementAge = [DateTimeOffset]::UtcNow.Subtract($RetirementTimestamp).TotalSeconds
if ($Retired.ok -ne $true -or $Retired.operation -ne 'retire' -or $Retired.candidate -ne $PriorCandidate -or
    $Retired.receipt.host_pid -ne 43176 -or
    $Retired.receipt.retirement.identity.pid -ne 43176 -or
    $Retired.receipt.retirement.identity.process_start_token -ne '134362674908503410' -or $Retired.receipt.retirement.state -ne 'terminated' -or
    $Retired.receipt.retirement.exit_state -ne 'exited' -or $Retired.receipt.stopped_census.safe -ne $true -or
    $Retired.receipt.durable_state_deleted -ne $false -or $Retired.receipt.ui_stopped.alive -ne $false -or
    $RetirementAge -lt 0 -or $RetirementAge -gt 900) { throw 'A fresh exact prior-r9b retirement and quiescent census are required.' }
if (Get-Process -Id 43176 -ErrorAction SilentlyContinue) { throw 'The retired prior-r9b Host PID is live; refusing transition.' }
$DataRoot = Join-Path ([Environment]::GetFolderPath('ApplicationData')) 'web-mcp-assistant'
$ManifestPath = Join-Path $DataRoot 'recovery-supervisor\manifest.json'
$DescriptorPath = Join-Path $DataRoot 'recovery-host.json'
if ($Operation -eq 'InstallSupervisor') {
    $Manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
    if ($Manifest.mode -ne 'packaged' -or $Manifest.app_root -ne $PriorCandidate -or
        -not (Test-Path -LiteralPath (Join-Path $DataRoot 'recovery-supervisor\stop.request'))) { throw 'The expected stopped prior-r9b supervisor installation changed.' }
    if (Test-Path -LiteralPath $DescriptorPath) {
        $Descriptor = Get-Content -LiteralPath $DescriptorPath -Raw | ConvertFrom-Json
        if ($Descriptor.owner_pid -ne 43176 -or $Descriptor.instance_id -ne '21106c0b1376ec5a6142d074c619575f' -or
            $Descriptor.installation_id -ne '588b9782f4c3a2577a003894c95668543d81eb69311a77cb288b0cafa13a6148' -or
            $Descriptor.owner_process_start_token -ne '134362674908503410') { throw 'The preserved retired descriptor is not the exact prior r9b owner.' }
        if (Get-Process -Id ([int]$Descriptor.owner_pid) -ErrorAction SilentlyContinue) { throw 'A Recovery Host became live after retirement; refusing replacement.' }
    }
    $Supervisor = Join-Path $NewCandidate 'resources\resources\recovery-supervisor\recovery-supervisor.ps1'
    $PowerShell = Join-Path ([Environment]::GetFolderPath('System')) 'WindowsPowerShell\v1.0\powershell.exe'
    $Output = & $PowerShell -NoLogo -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File $Supervisor -Action Install -Packaged -AppRoot $NewCandidate -Executable $Exe
    if ($LASTEXITCODE -ne 0) { throw 'r9c supervisor installation failed.' }
    $Result = ($Output -join [Environment]::NewLine) | ConvertFrom-Json
    $Manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
    if ($Result.installed -ne $true -or $Manifest.mode -ne 'packaged' -or $Manifest.app_root -ne $NewCandidate -or
        $Manifest.executable -ne $Exe -or $Manifest.executable_sha256 -ne $ExpectedExeSha) { throw 'The installed supervisor does not target exact r9c.' }
    $Receipt = [ordered]@{operation='install_r9c_supervisor'; ok=$true; observed_at=[DateTimeOffset]::UtcNow.ToString('o'); candidate=$NewCandidate; result=$Result; manifest_sha256=(Get-FileHash -LiteralPath $ManifestPath -Algorithm SHA256).Hash.ToLowerInvariant(); retirement_receipt=[IO.Path]::GetFullPath($RetirementReceiptPath)}
} else {
    $Installed = Read-TransitionReceipt $InstallReceiptPath
    $Manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
    if ($Installed.ok -ne $true -or $Installed.operation -ne 'install_r9c_supervisor' -or $Installed.candidate -ne $NewCandidate -or
        $Manifest.app_root -ne $NewCandidate -or $Manifest.executable -ne $Exe -or
        (Get-FileHash -LiteralPath $ManifestPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $Installed.manifest_sha256) { throw 'The exact r9c supervisor installation receipt is required.' }
    $PreviousNodeFlag = $env:ELECTRON_RUN_AS_NODE
    try {
        Remove-Item Env:ELECTRON_RUN_AS_NODE -ErrorAction SilentlyContinue
        $Ui = Start-Process -FilePath $Exe -WorkingDirectory $NewCandidate -WindowStyle Hidden -PassThru
    } finally {
        if ($null -ne $PreviousNodeFlag) { $env:ELECTRON_RUN_AS_NODE = $PreviousNodeFlag }
    }
    $Receipt = [ordered]@{operation='launch_r9c_ui'; ok=$true; observed_at=[DateTimeOffset]::UtcNow.ToString('o'); candidate=$NewCandidate; spawned_pid=$Ui.Id; install_receipt=[IO.Path]::GetFullPath($InstallReceiptPath); readiness_not_inferred=$true}
}
$OutputPath = Join-Path $PSScriptRoot ($Receipt.operation + '-' + [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() + '.json')
$Receipt.report_path = $OutputPath
[IO.File]::WriteAllText($OutputPath, ($Receipt | ConvertTo-Json -Depth 10) + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
$Receipt | ConvertTo-Json -Depth 10 -Compress

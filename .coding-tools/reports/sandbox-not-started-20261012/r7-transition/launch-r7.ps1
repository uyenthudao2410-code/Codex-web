param(
    [ValidateSet('InstallSupervisor', 'LaunchUi')][string]$Operation,
    [string]$RetirementReceiptPath,
    [string]$InstallReceiptPath,
    [switch]$Apply
)
$ErrorActionPreference = 'Stop'
$R6 = 'E:\DEV\Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-machine-exec-lifecycle-1012-r6\win-unpacked'
$R7 = 'E:\DEV\Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-machine-exec-lifecycle-1012-r7\win-unpacked'
$Exe = Join-Path $R7 'Coding Tools MCP.exe'
$ExpectedExeSha = 'a18ba16a640c30ad67758d6ba19aaf7044d947cea2f8026796b6e88f930243a8'
$ExpectedAsarSha = '69bac603b0dab1ad27f86fa114da140b059a93c695a4b7dfdbe24b53b3c007ae'
$ExpectedAdapterSha = '3147cb5d6a4f1a9ca908a240f7955b8598cdde0e4258e031a348eae77d8521d9'
function Read-TransitionReceipt([string]$ReceiptPath) {
    $Resolved = [IO.Path]::GetFullPath($ReceiptPath)
    if (-not $Resolved.StartsWith($PSScriptRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -or
        (Get-Item -LiteralPath $Resolved).Length -gt 65536) { throw 'A bounded receipt from this transition directory is required.' }
    Get-Content -LiteralPath $Resolved -Raw | ConvertFrom-Json
}
if ((Get-FileHash -LiteralPath $Exe -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedExeSha -or
    (Get-FileHash -LiteralPath (Join-Path $R7 'resources\app.asar') -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedAsarSha -or
    (Get-FileHash -LiteralPath (Join-Path $R7 'resources\resources\coding-tools-mcp\coding_tools_mcp\windows_mxc_state_aware.py') -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedAdapterSha) { throw 'The r7 package changed after verification.' }
if (-not $Apply) {
    [pscustomobject]@{operation=$Operation; apply=$false; package_verified=$true; runtime_effects=0} | ConvertTo-Json -Compress
    exit 0
}
$Retired = Read-TransitionReceipt $RetirementReceiptPath
$RetirementTimestamp = if ($Retired.observed_at -is [DateTime]) { [DateTimeOffset]::new($Retired.observed_at) } else { [DateTimeOffset]::Parse($Retired.observed_at, [Globalization.CultureInfo]::InvariantCulture) }
$RetirementAge = [DateTimeOffset]::UtcNow.Subtract($RetirementTimestamp).TotalSeconds
if ($Retired.ok -ne $true -or $Retired.operation -ne 'retire' -or $Retired.candidate -ne $R6 -or
    $Retired.receipt.host_pid -ne 25028 -or $Retired.receipt.retirement.state -ne 'terminated' -or
    $Retired.receipt.retirement.exit_state -ne 'exited' -or $Retired.receipt.stopped_census.safe -ne $true -or
    $Retired.receipt.durable_state_deleted -ne $false -or $Retired.receipt.ui_stopped.alive -ne $false -or
    $RetirementAge -lt 0 -or $RetirementAge -gt 900) { throw 'A fresh exact r6 retirement and quiescent census are required.' }
if (Get-Process -Id 25028 -ErrorAction SilentlyContinue) { throw 'The retired r6 Host PID is live; refusing transition.' }
$DataRoot = Join-Path ([Environment]::GetFolderPath('ApplicationData')) 'web-mcp-assistant'
$ManifestPath = Join-Path $DataRoot 'recovery-supervisor\manifest.json'
$DescriptorPath = Join-Path $DataRoot 'recovery-host.json'
if ($Operation -eq 'InstallSupervisor') {
    $Manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
    if ($Manifest.mode -ne 'packaged' -or $Manifest.app_root -ne $R6 -or
        -not (Test-Path -LiteralPath (Join-Path $DataRoot 'recovery-supervisor\stop.request'))) { throw 'The expected stopped r6 supervisor installation changed.' }
    if (Test-Path -LiteralPath $DescriptorPath) {
        $Descriptor = Get-Content -LiteralPath $DescriptorPath -Raw | ConvertFrom-Json
        if (Get-Process -Id ([int]$Descriptor.owner_pid) -ErrorAction SilentlyContinue) { throw 'A Recovery Host became live after retirement; refusing replacement.' }
    }
    $Supervisor = Join-Path $R7 'resources\resources\recovery-supervisor\recovery-supervisor.ps1'
    $PowerShell = Join-Path ([Environment]::GetFolderPath('System')) 'WindowsPowerShell\v1.0\powershell.exe'
    $Output = & $PowerShell -NoLogo -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File $Supervisor -Action Install -Packaged -AppRoot $R7 -Executable $Exe
    if ($LASTEXITCODE -ne 0) { throw 'r7 supervisor installation failed.' }
    $Result = ($Output -join [Environment]::NewLine) | ConvertFrom-Json
    $Manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
    if ($Result.installed -ne $true -or $Manifest.mode -ne 'packaged' -or $Manifest.app_root -ne $R7 -or
        $Manifest.executable -ne $Exe -or $Manifest.executable_sha256 -ne $ExpectedExeSha) { throw 'The installed supervisor does not target exact r7.' }
    $Receipt = [ordered]@{operation='install_r7_supervisor'; ok=$true; observed_at=[DateTimeOffset]::UtcNow.ToString('o'); candidate=$R7; result=$Result; manifest_sha256=(Get-FileHash -LiteralPath $ManifestPath -Algorithm SHA256).Hash.ToLowerInvariant(); retirement_receipt=[IO.Path]::GetFullPath($RetirementReceiptPath)}
} else {
    $Installed = Read-TransitionReceipt $InstallReceiptPath
    $Manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
    if ($Installed.ok -ne $true -or $Installed.operation -ne 'install_r7_supervisor' -or $Installed.candidate -ne $R7 -or
        $Manifest.app_root -ne $R7 -or $Manifest.executable -ne $Exe -or
        (Get-FileHash -LiteralPath $ManifestPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $Installed.manifest_sha256) { throw 'The exact r7 supervisor installation receipt is required.' }
    $PreviousNodeFlag = $env:ELECTRON_RUN_AS_NODE
    try {
        Remove-Item Env:ELECTRON_RUN_AS_NODE -ErrorAction SilentlyContinue
        $Ui = Start-Process -FilePath $Exe -WorkingDirectory $R7 -WindowStyle Hidden -PassThru
    } finally {
        if ($null -ne $PreviousNodeFlag) { $env:ELECTRON_RUN_AS_NODE = $PreviousNodeFlag }
    }
    $Receipt = [ordered]@{operation='launch_r7_ui'; ok=$true; observed_at=[DateTimeOffset]::UtcNow.ToString('o'); candidate=$R7; spawned_pid=$Ui.Id; install_receipt=[IO.Path]::GetFullPath($InstallReceiptPath); readiness_not_inferred=$true}
}
$OutputPath = Join-Path $PSScriptRoot ($Receipt.operation + '-' + [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() + '.json')
$Receipt.report_path = $OutputPath
[IO.File]::WriteAllText($OutputPath, ($Receipt | ConvertTo-Json -Depth 10) + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
$Receipt | ConvertTo-Json -Depth 10 -Compress

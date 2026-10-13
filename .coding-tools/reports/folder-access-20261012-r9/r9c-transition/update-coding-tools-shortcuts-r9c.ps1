param(
    [string]$TargetPath,
    [string]$ExpectedEpoch,
    [string]$ReadyReceiptPath,
    [switch]$Apply
)

$ErrorActionPreference = 'Stop'
$ExpectedExeSha256 = '88a36a0c15cc5eb97657c8e68554f07aa7704cfaab9fd0ab2078ea4423f19bf2'
$ExpectedAsarSha256 = '45903d28f4c7e0415ca30857992e5b34c66e1f7f597822c35036874df7dd78cd'
$ExpectedOldTarget = 'E:\DEV\Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-machine-exec-lifecycle-1012-r8\win-unpacked\Coding Tools MCP.exe'
$ExpectedNewTarget = 'E:\DEV\Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-machine-folder-access-1012-r9c\win-unpacked\Coding Tools MCP.exe'
$ShortcutSpecs = @(
    @{ path = 'C:\Users\Admin\Desktop\Coding Tools MCP.lnk'; sha256 = '982304384ba8a66df884e440c2e0f4ed27f5516ddc1377accd92d7450208c329'; backup = 'desktop-coding-tools-r8-original.lnk' },
    @{ path = 'C:\Users\Admin\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Coding Tools MCP.lnk'; sha256 = '84f5444f2360de1e8e01d32a3bd892784b93ca3d5b5bf3fc938ce50dba0cc0b9'; backup = 'start-menu-coding-tools-r8-original.lnk' }
)
$Shell = New-Object -ComObject WScript.Shell
$ShellApplication = New-Object -ComObject Shell.Application

function Get-ShortcutObservation([string]$Path) {
    $Shortcut = $Shell.CreateShortcut($Path)
    $Folder = $ShellApplication.NameSpace([IO.Path]::GetDirectoryName($Path))
    $Item = $Folder.ParseName([IO.Path]::GetFileName($Path))
    [ordered]@{
        path = $Path
        sha256 = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
        target = $Shortcut.TargetPath
        working_directory = $Shortcut.WorkingDirectory
        arguments = $Shortcut.Arguments
        description = $Shortcut.Description
        icon_location = $Shortcut.IconLocation
        window_style = $Shortcut.WindowStyle
        hotkey = $Shortcut.Hotkey
        app_user_model_id = $Item.ExtendedProperty('System.AppUserModel.ID')
        target_exists = Test-Path -LiteralPath $Shortcut.TargetPath -PathType Leaf
    }
}

$Before = @()
foreach ($Spec in $ShortcutSpecs) {
    $Observation = Get-ShortcutObservation $Spec.path
    if ($Observation.sha256 -ne $Spec.sha256 -or $Observation.target -ne $ExpectedOldTarget -or $Observation.arguments) {
        throw 'A Coding Tools MCP shortcut changed since inspection; refusing to overwrite it.'
    }
    $Before += $Observation
    $BackupPath = Join-Path $PSScriptRoot $Spec.backup
    if (Test-Path -LiteralPath $BackupPath) {
        if ((Get-FileHash -LiteralPath $BackupPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $Spec.sha256) {
            throw 'An original shortcut backup has unexpected content.'
        }
    } else {
        Copy-Item -LiteralPath $Spec.path -Destination $BackupPath
    }
    if ((Get-FileHash -LiteralPath $BackupPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $Spec.sha256) {
        throw 'A shortcut changed during backup; refusing to proceed.'
    }
}
$BeforeReceiptPath = Join-Path $PSScriptRoot 'coding-tools-shortcuts-before-r9c.json'
if (-not (Test-Path -LiteralPath $BeforeReceiptPath)) {
    [IO.File]::WriteAllText($BeforeReceiptPath, (ConvertTo-Json -InputObject $Before -Depth 5) + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
}

if (-not $Apply) {
    [pscustomobject]@{ operation = 'coding_tools_shortcuts_prepared'; originals_verified = 2; backups_verified = 2; changed_shortcuts = 0 } | ConvertTo-Json -Compress
    exit 0
}

$ResolvedTarget = [IO.Path]::GetFullPath($TargetPath)
$AuthorizedRoot = 'E:\DEV\Codex-web\dist\'
if (-not $ResolvedTarget.StartsWith($AuthorizedRoot, [StringComparison]::OrdinalIgnoreCase) -or
    $ResolvedTarget -ne $ExpectedNewTarget) {
    throw 'The target must be the exact verified r9c package.'
}
$TargetRoot = [IO.Path]::GetDirectoryName($ResolvedTarget)
$AsarPath = Join-Path $TargetRoot 'resources\app.asar'
if ((Get-FileHash -LiteralPath $ResolvedTarget -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedExeSha256 -or
    (Get-FileHash -LiteralPath $AsarPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedAsarSha256 -or
    (Get-FileHash -LiteralPath (Join-Path $TargetRoot 'resources\resources\coding-tools-mcp\coding_tools_mcp\windows_mxc_state_aware.py') -Algorithm SHA256).Hash.ToLowerInvariant() -ne '3147cb5d6a4f1a9ca908a240f7955b8598cdde0e4258e031a348eae77d8521d9') {
    throw 'The target does not match the expected r9c EXE, app.asar and adapter.'
}
if ($ExpectedEpoch -notmatch '^activation-[A-Za-z0-9_-]+$' -or
    $ExpectedEpoch -eq 'activation-mv4ztgwa-41d4eace008278b49931d1b727068507') { throw 'A new r9c activation epoch is required.' }
$ResolvedReceipt = [IO.Path]::GetFullPath($ReadyReceiptPath)
if (-not $ResolvedReceipt.StartsWith($PSScriptRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -or
    [IO.Path]::GetFileName($ResolvedReceipt) -notlike ('final-machine-observation-' + $ExpectedEpoch + '-*.json')) { throw 'An r9c observer receipt from this transition directory is required.' }
$Ready = Get-Content -LiteralPath $ResolvedReceipt -Raw | ConvertFrom-Json
$ReadyTimestamp = if ($Ready.observed_at -is [DateTime]) { [DateTimeOffset]::new($Ready.observed_at) } else { [DateTimeOffset]::Parse($Ready.observed_at, [Globalization.CultureInfo]::InvariantCulture) }
$ReceiptAgeSeconds = [DateTimeOffset]::UtcNow.Subtract($ReadyTimestamp).TotalSeconds
if ($Ready.ok -ne $true -or $Ready.read_only -ne $true -or $Ready.candidate -ne $TargetRoot -or
    $Ready.target_activation_epoch_id -ne $ExpectedEpoch -or $Ready.epoch.state -ne 'READY' -or
    $Ready.epoch.admission_state -ne 'OPEN' -or $Ready.runtime.fullyReady -ne $true -or
    $Ready.descriptor_stable -ne $true -or $Ready.epoch_stable -ne $true -or
    $ReceiptAgeSeconds -lt 0 -or $ReceiptAgeSeconds -gt 120) { throw 'The r9c READY/OPEN receipt is absent, stale or inconsistent.' }

# Check both links immediately before any change, then check each again before Save.
foreach ($Spec in $ShortcutSpecs) {
    if ((Get-FileHash -LiteralPath $Spec.path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $Spec.sha256) {
        throw 'A shortcut changed before application; refusing to overwrite it.'
    }
}
$After = @()
for ($Index = 0; $Index -lt $ShortcutSpecs.Count; $Index++) {
    $Spec = $ShortcutSpecs[$Index]
    if ((Get-FileHash -LiteralPath $Spec.path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $Spec.sha256) {
        throw 'A shortcut changed during application; original backups are preserved.'
    }
    $Shortcut = $Shell.CreateShortcut($Spec.path)
    $Shortcut.TargetPath = $ResolvedTarget
    $Shortcut.WorkingDirectory = $TargetRoot
    $Shortcut.Save()
    $Observation = Get-ShortcutObservation $Spec.path
    if ($Observation.target -ne $ResolvedTarget -or $Observation.working_directory -ne $TargetRoot -or -not $Observation.target_exists) {
        throw 'A saved shortcut does not target the verified r9c package.'
    }
    foreach ($Property in @('arguments', 'description', 'icon_location', 'window_style', 'hotkey', 'app_user_model_id')) {
        if ($Observation[$Property] -ne $Before[$Index][$Property]) {
            throw "A shortcut property was unexpectedly changed: $Property. Original backups are preserved."
        }
    }
    $After += $Observation
    [IO.File]::WriteAllText((Join-Path $PSScriptRoot 'coding-tools-shortcuts-after-r9c.json'), (ConvertTo-Json -InputObject $After -Depth 5) + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
}
[pscustomobject]@{ operation = 'coding_tools_shortcuts_updated'; changed_shortcuts = 2; target = $ResolvedTarget; exe_sha256 = $ExpectedExeSha256; asar_sha256 = $ExpectedAsarSha256; preserved_other_properties = $true } | ConvertTo-Json -Compress

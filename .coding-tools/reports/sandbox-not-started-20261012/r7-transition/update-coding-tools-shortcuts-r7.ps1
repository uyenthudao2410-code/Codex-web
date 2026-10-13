param(
    [string]$TargetPath,
    [string]$ExpectedEpoch,
    [string]$ReadyReceiptPath,
    [switch]$Apply
)

$ErrorActionPreference = 'Stop'
$ExpectedExeSha256 = 'a18ba16a640c30ad67758d6ba19aaf7044d947cea2f8026796b6e88f930243a8'
$ExpectedAsarSha256 = '69bac603b0dab1ad27f86fa114da140b059a93c695a4b7dfdbe24b53b3c007ae'
$ExpectedOldTarget = 'E:\DEV\Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-machine-exec-lifecycle-1012-r6\win-unpacked\Coding Tools MCP.exe'
$ExpectedNewTarget = 'E:\DEV\Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-machine-exec-lifecycle-1012-r7\win-unpacked\Coding Tools MCP.exe'
$ShortcutSpecs = @(
    @{ path = 'C:\Users\Admin\Desktop\Coding Tools MCP.lnk'; sha256 = '06d5d0ddbb40bf396184556491b1cd8706746f38762f4a83ee17e97ccd114dd2'; backup = 'desktop-coding-tools-r6-original.lnk' },
    @{ path = 'C:\Users\Admin\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Coding Tools MCP.lnk'; sha256 = '5c6d4389f81d70179eeeeedf3c29e1d23b0fe57d9f05ceb60532553e90452003'; backup = 'start-menu-coding-tools-r6-original.lnk' }
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
$BeforeReceiptPath = Join-Path $PSScriptRoot 'coding-tools-shortcuts-before-r7.json'
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
    throw 'The target must be the exact verified r7 package.'
}
$TargetRoot = [IO.Path]::GetDirectoryName($ResolvedTarget)
$AsarPath = Join-Path $TargetRoot 'resources\app.asar'
if ((Get-FileHash -LiteralPath $ResolvedTarget -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedExeSha256 -or
    (Get-FileHash -LiteralPath $AsarPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedAsarSha256 -or
    (Get-FileHash -LiteralPath (Join-Path $TargetRoot 'resources\resources\coding-tools-mcp\coding_tools_mcp\windows_mxc_state_aware.py') -Algorithm SHA256).Hash.ToLowerInvariant() -ne '3147cb5d6a4f1a9ca908a240f7955b8598cdde0e4258e031a348eae77d8521d9') {
    throw 'The target does not match the expected r7 EXE, app.asar and adapter.'
}
if ($ExpectedEpoch -notmatch '^activation-[A-Za-z0-9_-]+$' -or
    $ExpectedEpoch -eq 'activation-mv4u5k6v-cfeabc74ae10012ae61eab8d4c87e8b4') { throw 'A new r7 activation epoch is required.' }
$ResolvedReceipt = [IO.Path]::GetFullPath($ReadyReceiptPath)
if (-not $ResolvedReceipt.StartsWith($PSScriptRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -or
    [IO.Path]::GetFileName($ResolvedReceipt) -notlike ('final-machine-observation-' + $ExpectedEpoch + '-*.json')) { throw 'An r7 observer receipt from this transition directory is required.' }
$Ready = Get-Content -LiteralPath $ResolvedReceipt -Raw | ConvertFrom-Json
$ReadyTimestamp = if ($Ready.observed_at -is [DateTime]) { [DateTimeOffset]::new($Ready.observed_at) } else { [DateTimeOffset]::Parse($Ready.observed_at, [Globalization.CultureInfo]::InvariantCulture) }
$ReceiptAgeSeconds = [DateTimeOffset]::UtcNow.Subtract($ReadyTimestamp).TotalSeconds
if ($Ready.ok -ne $true -or $Ready.read_only -ne $true -or $Ready.candidate -ne $TargetRoot -or
    $Ready.target_activation_epoch_id -ne $ExpectedEpoch -or $Ready.epoch.state -ne 'READY' -or
    $Ready.epoch.admission_state -ne 'OPEN' -or $Ready.runtime.fullyReady -ne $true -or
    $Ready.descriptor_stable -ne $true -or $Ready.epoch_stable -ne $true -or
    $ReceiptAgeSeconds -lt 0 -or $ReceiptAgeSeconds -gt 120) { throw 'The r7 READY/OPEN receipt is absent, stale or inconsistent.' }

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
        throw 'A saved shortcut does not target the verified r7 package.'
    }
    foreach ($Property in @('arguments', 'description', 'icon_location', 'window_style', 'hotkey', 'app_user_model_id')) {
        if ($Observation[$Property] -ne $Before[$Index][$Property]) {
            throw "A shortcut property was unexpectedly changed: $Property. Original backups are preserved."
        }
    }
    $After += $Observation
    [IO.File]::WriteAllText((Join-Path $PSScriptRoot 'coding-tools-shortcuts-after-r7.json'), (ConvertTo-Json -InputObject $After -Depth 5) + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
}
[pscustomobject]@{ operation = 'coding_tools_shortcuts_updated'; changed_shortcuts = 2; target = $ResolvedTarget; exe_sha256 = $ExpectedExeSha256; asar_sha256 = $ExpectedAsarSha256; preserved_other_properties = $true } | ConvertTo-Json -Compress

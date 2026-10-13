param(
    [string]$TargetPath,
    [switch]$Apply
)

$ErrorActionPreference = 'Stop'
$ExpectedExeSha256 = 'a18ba16a640c30ad67758d6ba19aaf7044d947cea2f8026796b6e88f930243a8'
$ExpectedAsarSha256 = '69bac603b0dab1ad27f86fa114da140b059a93c695a4b7dfdbe24b53b3c007ae'
$ExpectedOldTarget = 'C:\Users\Admin\AppData\Local\Programs\Coding Tools MCP\Coding Tools MCP.exe'
$ShortcutSpecs = @(
    @{ path = 'C:\Users\Admin\Desktop\Coding Tools MCP.lnk'; sha256 = 'a905c973c381d921fd003e003e3e63d4f4aeae0788cc6304bc407d2f5825bcd2'; backup = 'desktop-coding-tools-original.lnk' },
    @{ path = 'C:\Users\Admin\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Coding Tools MCP.lnk'; sha256 = 'a128c864524a8323c1cadfa9c7c1c4f66df438970d4a6aee9a21253ba0838b28'; backup = 'start-menu-coding-tools-original.lnk' }
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
$BeforeReceiptPath = Join-Path $PSScriptRoot 'coding-tools-shortcuts-before-r6.json'
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
    [IO.Path]::GetFileName($ResolvedTarget) -ne 'Coding Tools MCP.exe') {
    throw 'The target must be the verified r6 package inside this repository dist directory.'
}
$TargetRoot = [IO.Path]::GetDirectoryName($ResolvedTarget)
$AsarPath = Join-Path $TargetRoot 'resources\app.asar'
if ((Get-FileHash -LiteralPath $ResolvedTarget -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedExeSha256 -or
    (Get-FileHash -LiteralPath $AsarPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedAsarSha256) {
    throw 'The target does not match the expected r6 EXE and app.asar.'
}

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
        throw 'A saved shortcut does not target the verified r6 package.'
    }
    foreach ($Property in @('arguments', 'description', 'icon_location', 'window_style', 'hotkey', 'app_user_model_id')) {
        if ($Observation[$Property] -ne $Before[$Index][$Property]) {
            throw "A shortcut property was unexpectedly changed: $Property. Original backups are preserved."
        }
    }
    $After += $Observation
    [IO.File]::WriteAllText((Join-Path $PSScriptRoot 'coding-tools-shortcuts-after-r6.json'), (ConvertTo-Json -InputObject $After -Depth 5) + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
}
[pscustomobject]@{ operation = 'coding_tools_shortcuts_updated'; changed_shortcuts = 2; target = $ResolvedTarget; exe_sha256 = $ExpectedExeSha256; asar_sha256 = $ExpectedAsarSha256; preserved_other_properties = $true } | ConvertTo-Json -Compress

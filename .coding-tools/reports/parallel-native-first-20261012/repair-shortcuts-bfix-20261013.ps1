$ErrorActionPreference = 'Stop'

$candidate = 'E:\DEV\Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-r4-timefix-bfix\win-unpacked\Coding Tools MCP.exe'
$candidateDir = Split-Path -Path $candidate -Parent
$oldTarget = 'E:\DEV\Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-parallel-r4-timefix\win-unpacked\Coding Tools MCP.exe'
$shortcutPaths = @(
  'C:\Users\Admin\Desktop\Coding Tools MCP.lnk',
  'C:\Users\Admin\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Coding Tools MCP.lnk'
)

if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) { throw 'CANDIDATE_EXECUTABLE_MISSING' }
$shell = New-Object -ComObject WScript.Shell
$before = @()
foreach ($path in $shortcutPaths) {
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "SHORTCUT_MISSING:$path" }
  $item = $shell.CreateShortcut($path)
  if ([IO.Path]::GetFullPath($item.TargetPath) -ne [IO.Path]::GetFullPath($oldTarget)) { throw "SHORTCUT_TARGET_CHANGED:$path ($($item.TargetPath) != $oldTarget)" }
  if ([IO.Path]::GetFullPath($item.WorkingDirectory) -ne [IO.Path]::GetFullPath((Split-Path -Path $oldTarget -Parent))) { throw "SHORTCUT_WORKDIR_CHANGED:$path" }
  $before += [pscustomobject]@{
    path = $path
    target = $item.TargetPath
    working_directory = $item.WorkingDirectory
    arguments = $item.Arguments
    description = $item.Description
    hotkey = $item.Hotkey
    window_style = $item.WindowStyle
    icon_location = $item.IconLocation
    sha256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
  }
}

$changed = @()
foreach ($entry in $before) {
  $item = $shell.CreateShortcut($entry.path)
  $item.TargetPath = $candidate
  $item.WorkingDirectory = $candidateDir
  $item.Save()
  $check = $shell.CreateShortcut($entry.path)
  $targetMatches = ([IO.Path]::GetFullPath($check.TargetPath) -eq [IO.Path]::GetFullPath($candidate))
  $workdirMatches = ([IO.Path]::GetFullPath($check.WorkingDirectory) -eq [IO.Path]::GetFullPath($candidateDir))
  $fieldsPreserved = ($check.Arguments -eq $entry.arguments) -and ($check.Description -eq $entry.description) -and ($check.Hotkey -eq $entry.hotkey) -and ($check.WindowStyle -eq $entry.window_style)
  if (-not ($targetMatches -and $workdirMatches -and $fieldsPreserved)) { throw "SHORTCUT_REPAIR_VERIFY_FAILED:$($entry.path)" }
  $changed += [pscustomobject]@{
    path = $entry.path
    target = $check.TargetPath
    working_directory = $check.WorkingDirectory
    arguments_preserved = $check.Arguments -eq $entry.arguments
    description_preserved = $check.Description -eq $entry.description
    hotkey_preserved = $check.Hotkey -eq $entry.hotkey
    window_style_preserved = $check.WindowStyle -eq $entry.window_style
    sha256 = (Get-FileHash -LiteralPath $entry.path -Algorithm SHA256).Hash.ToLowerInvariant()
  }
}

$report = [ordered]@{
  schema_version = 1
  operation = 'repair_shortcuts_to_bfix_candidate'
  observed_at = [DateTimeOffset]::UtcNow.ToString('o')
  candidate = $candidate
  old_target = $oldTarget
  external_mutation = $true
  guarded_precondition = 'both shortcuts exactly targeted the stale r4-timefix candidate and its working directory'
  before = $before
  changed = $changed
  verification = [ordered]@{ all_match_candidate = $true; all_non_target_fields_preserved = $true }
}
$out = Join-Path $PSScriptRoot 'shortcuts-bfix-repair-20261013.json'
if (Test-Path -LiteralPath $out) { throw 'REPAIR_RECEIPT_EXISTS' }
$report | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $out -Encoding UTF8
$report | ConvertTo-Json -Depth 10

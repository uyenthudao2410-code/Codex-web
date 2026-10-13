$ErrorActionPreference = 'Stop'
$candidate = 'E:\DEV\Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-parallel-r4-timefix\win-unpacked\Coding Tools MCP.exe'
$candidateDir = Split-Path -Path $candidate -Parent
$shortcuts = @(
  'C:\Users\Admin\Desktop\Coding Tools MCP.lnk',
  'C:\Users\Admin\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Coding Tools MCP.lnk'
)
$shell = New-Object -ComObject WScript.Shell
$shortcutResults = foreach ($path in $shortcuts) {
  $item = $shell.CreateShortcut($path)
  [pscustomobject]@{
    path = $path
    target = $item.TargetPath
    working_directory = $item.WorkingDirectory
    matches_candidate = ([IO.Path]::GetFullPath($item.TargetPath) -eq [IO.Path]::GetFullPath($candidate) -and [IO.Path]::GetFullPath($item.WorkingDirectory) -eq [IO.Path]::GetFullPath($candidateDir))
    sha256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
  }
}
$sandbox = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match '^(WindowsSandbox.*|vmmemWSB|wxc-windows-sandbox-daemon|wxc-exec)$' } | ForEach-Object { [pscustomobject]@{ process_name = $_.ProcessName; pid = $_.Id } })
$manifestPath = Join-Path $env:APPDATA 'web-mcp-assistant/recovery-supervisor/manifest.json'
$manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
$report = [ordered]@{
  schema_version = 1
  operation = 'production_post_shortcut_verification'
  observed_at = [DateTimeOffset]::UtcNow.ToString('o')
  candidate = $candidate
  shortcut_results = $shortcutResults
  shortcuts_match_candidate = (@($shortcutResults | Where-Object { -not $_.matches_candidate }).Count -eq 0)
  supervisor_manifest_matches_candidate = ([IO.Path]::GetFullPath($manifest.executable) -eq [IO.Path]::GetFullPath($candidate) -and [IO.Path]::GetFullPath($manifest.app_root) -eq [IO.Path]::GetFullPath($candidateDir))
  sandbox_named_process_count = $sandbox.Count
  sandbox_named_processes = $sandbox
  external_mutation_performed_before_capture = $true
  credential_emitted = $false
}
$out = Join-Path $PSScriptRoot 'production-post-shortcut-verification-20261013.json'
if (Test-Path -LiteralPath $out) { throw 'VERIFICATION_RECEIPT_EXISTS' }
$report | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $out -Encoding UTF8
$report | ConvertTo-Json -Depth 10

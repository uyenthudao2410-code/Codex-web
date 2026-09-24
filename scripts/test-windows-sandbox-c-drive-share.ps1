param(
    [ValidateRange(30, 300)]
    [int]$TimeoutSeconds = 120
)

$ErrorActionPreference = 'Stop'
$SystemRootValue = $env:SystemRoot
if (-not $SystemRootValue) { $SystemRootValue = $env:WINDIR }
if (-not $SystemRootValue) { $SystemRootValue = 'C:\Windows' }
$SystemRootPath = [IO.Path]::GetFullPath([string]$SystemRootValue)
$WindowsSandboxExe = Join-Path $SystemRootPath 'System32\WindowsSandbox.exe'
if (-not (Test-Path -LiteralPath $WindowsSandboxExe -PathType Leaf)) {
    throw 'Windows Sandbox is not installed. Enable Containers-DisposableClientVM and reboot first.'
}

# Do not collide with or stop a user-owned/manual Sandbox session.
$existingRemoteSessions = @(Get-Process -Name 'WindowsSandboxRemoteSession' -ErrorAction SilentlyContinue)
if ($existingRemoteSessions.Count -gt 0) {
    throw 'A Windows Sandbox remote session is already running; refusing to start another diagnostic VM.'
}

$TempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
$RunId = [guid]::NewGuid().ToString('N')
$WorkspacePath = [IO.Path]::GetFullPath((Join-Path $TempRoot ('codex-wsb-map-' + $RunId)))
$ConfigPath = [IO.Path]::GetFullPath((Join-Path $TempRoot ('codex-wsb-map-' + $RunId + '.wsb')))
if ((Test-Path -LiteralPath $WorkspacePath) -or (Test-Path -LiteralPath $ConfigPath)) {
    throw 'A unique Windows Sandbox diagnostic path unexpectedly exists.'
}

$launcher = $null
$workspaceCreated = $false
try {
    New-Item -ItemType Directory -Path $WorkspacePath | Out-Null
    $workspaceCreated = $true
    $bootstrap = @'
@echo off
echo WSB_C_DRIVE_MAPPING_OK>C:\CodexWorkspace\result.txt
shutdown.exe /s /t 5 /c "Codex Windows Sandbox mapping diagnostic complete"
'@
    [IO.File]::WriteAllText(
        (Join-Path $WorkspacePath 'bootstrap.cmd'),
        $bootstrap.Replace("`n", "`r`n"),
        [Text.UTF8Encoding]::new($false)
    )

    $hostXml = [Security.SecurityElement]::Escape($WorkspacePath)
    $configuration = @"
<Configuration>
  <MappedFolders>
    <MappedFolder>
      <HostFolder>$hostXml</HostFolder>
      <SandboxFolder>C:\CodexWorkspace</SandboxFolder>
      <ReadOnly>false</ReadOnly>
    </MappedFolder>
  </MappedFolders>
  <LogonCommand>
    <Command>C:\CodexWorkspace\bootstrap.cmd</Command>
  </LogonCommand>
  <vGPU>Disable</vGPU>
  <Networking>Disable</Networking>
</Configuration>
"@
    $null = [xml]$configuration
    [IO.File]::WriteAllText($ConfigPath, $configuration, [Text.UTF8Encoding]::new($false))

    $launchAt = Get-Date
    $launcher = Start-Process -FilePath $WindowsSandboxExe -ArgumentList @($ConfigPath) -PassThru
    $marker = Join-Path $WorkspacePath 'result.txt'
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while (-not (Test-Path -LiteralPath $marker -PathType Leaf) -and (Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 2
    }
    if (-not (Test-Path -LiteralPath $marker -PathType Leaf)) {
        $remoteSessions = @(Get-Process -Name 'WindowsSandboxRemoteSession' -ErrorAction SilentlyContinue |
            Where-Object { $_.StartTime -ge $launchAt })
        [pscustomobject]@{
            probe = 'windows_sandbox_c_drive_share_v1'
            available = $false
            reason = 'GUEST_MARKER_TIMEOUT'
            remote_session_count = $remoteSessions.Count
            diagnostic_workspace_preserved = $WorkspacePath
        } | ConvertTo-Json -Compress
        # Preserve the owned VM/config/workspace for operator diagnostics. Never
        # terminate a Sandbox or guess at ownership when the guest did not attest.
        $workspaceCreated = $false
        exit 0
    }

    $markerText = (Get-Content -LiteralPath $marker -Raw).Trim()
    if ($markerText -ne 'WSB_C_DRIVE_MAPPING_OK') {
        throw 'The Windows Sandbox guest returned an unexpected diagnostic marker.'
    }

    $remoteDeadline = (Get-Date).AddSeconds(45)
    do {
        $remoteSessions = @(Get-Process -Name 'WindowsSandboxRemoteSession' -ErrorAction SilentlyContinue |
            Where-Object { $_.StartTime -ge $launchAt })
        if ($remoteSessions.Count -eq 0) { break }
        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $remoteDeadline)
    if ($remoteSessions.Count -gt 0) {
        [pscustomobject]@{
            probe = 'windows_sandbox_c_drive_share_v1'
            available = $false
            reason = 'GUEST_MARKER_OK_BUT_TEARDOWN_UNCONFIRMED'
            remote_session_count = $remoteSessions.Count
            diagnostic_workspace_preserved = $WorkspacePath
        } | ConvertTo-Json -Compress
        $workspaceCreated = $false
        exit 0
    }

    Remove-Item -LiteralPath $WorkspacePath -Recurse -Force
    $workspaceCreated = $false
    Remove-Item -LiteralPath $ConfigPath -Force
    [pscustomobject]@{
        probe = 'windows_sandbox_c_drive_share_v1'
        available = $true
        reason = $null
        mapped_host_drive = [IO.Path]::GetPathRoot($WorkspacePath).TrimEnd('\')
        mapped_guest_path = 'C:\CodexWorkspace'
        guest_marker = $markerText
        teardown_confirmed = $true
    } | ConvertTo-Json -Compress
} finally {
    if ($null -eq $launcher -and $workspaceCreated -and (Test-Path -LiteralPath $WorkspacePath)) {
        $resolvedWorkspace = [IO.Path]::GetFullPath($WorkspacePath)
        if ([IO.Path]::GetDirectoryName($resolvedWorkspace) -ne $TempRoot -or
            -not [IO.Path]::GetFileName($resolvedWorkspace).StartsWith('codex-wsb-map-', [StringComparison]::Ordinal)) {
            throw 'Refusing to clean an unexpected Windows Sandbox diagnostic directory.'
        }
        Remove-Item -LiteralPath $resolvedWorkspace -Recurse -Force
        if (Test-Path -LiteralPath $ConfigPath) { Remove-Item -LiteralPath $ConfigPath -Force }
    }
}

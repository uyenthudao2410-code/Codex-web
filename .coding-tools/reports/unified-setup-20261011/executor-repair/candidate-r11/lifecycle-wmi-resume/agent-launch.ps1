[CmdletBinding()]
param([Parameter(Mandatory=$true)][switch]$OperatorApproved,[Parameter(Mandatory=$true)][ValidateRange(1,240)][int]$MaxIterations)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2
$r11Package = 'E:\Github\Tools-Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-initial-proof-1011-r11\win-unpacked'
$r11Profile = 'C:\Users\daoth\AppData\Roaming\web-mcp-assistant'
$r11Python = Join-Path $r11Package 'resources\resources\native-python\python.exe'
try {
    $r11Now = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
    if (-not $OperatorApproved -or $r11Now -ge 1791739329910 -or $MaxIterations -gt [Math]::Ceiling((1791739329910-$r11Now)/15000)) { throw 'AUTHORITY_EXPIRED_OR_DURATION_CHANGED' }
    $r11SafeNames = @('SystemRoot','WINDIR','COMSPEC','PATH','PATHEXT','TEMP','TMP','APPDATA','LOCALAPPDATA','USERPROFILE','USERNAME','USERDOMAIN','HOMEDRIVE','HOMEPATH','ALLUSERSPROFILE','ProgramData','ProgramFiles','ProgramFiles(x86)','ProgramW6432')
    $r11Environment = @($r11SafeNames | ForEach-Object { $r11Value = [Environment]::GetEnvironmentVariable($_); if (-not [string]::IsNullOrEmpty($r11Value)) { $_ + '=' + $r11Value } })
    $r11Startup = New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{ ShowWindow=[uint16]0; CreateFlags=[uint32]16777216; EnvironmentVariables=[string[]]$r11Environment }
    $r11Argv = @($r11Python,'-B','-I','-u',(Join-Path $r11Package 'resources\resources\control-plane\node_agent.py'),'run-connected-agent','--config',(Join-Path $r11Profile 'control-plane-node.json'),'--workspace-registry',(Join-Path $r11Profile 'control-plane-workspaces.json'),'--project-root',$r11Package,'--node',(Join-Path $r11Package 'Coding Tools MCP.exe'),'--runtime-mode','packaged','--interval-seconds','15','--max-backoff-seconds','60','--max-iterations',[string]$MaxIterations)
    $r11Command = ($r11Argv | ForEach-Object { if ($_.Contains('"') -or $_.Contains("`r") -or $_.Contains("`n")) { throw 'UNSAFE_ARGUMENT' }; '"' + $_ + '"' }) -join ' '
    $r11Created = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine=$r11Command;CurrentDirectory=$r11Package;ProcessStartupInformation=$r11Startup}
    @{ok=($r11Created.ReturnValue -eq 0);return_value=[int]$r11Created.ReturnValue;pid=[int]$r11Created.ProcessId;at_ms=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();creation_flags=16777216;show_window=0;max_iterations=$MaxIterations;environment_allowlisted=$true;no_automatic_retry=$true} | ConvertTo-Json -Compress
    if ($r11Created.ReturnValue -ne 0) { exit 2 }
} catch {
    @{ok=$false;code='AGENT_WMI_LAUNCH_FAILED_RECONCILE_NO_REPLAY';no_automatic_retry=$true;raw_error_emitted=$false} | ConvertTo-Json -Compress
    exit 2
}

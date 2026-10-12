[CmdletBinding()]
param([Parameter(Mandatory=$true)][switch]$OperatorApproved)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2
$r11Package = 'E:\Github\Tools-Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-initial-proof-1011-r11\win-unpacked'
$r11Exe = Join-Path $r11Package 'Coding Tools MCP.exe'
$r11Profile = 'C:\Users\daoth\AppData\Roaming\web-mcp-assistant'
try {
    if (-not $OperatorApproved -or [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() -ge 1791739329910) { throw 'AUTHORITY_EXPIRED' }
    if ((Get-FileHash -LiteralPath $r11Exe -Algorithm SHA256).Hash.ToLower() -ne 'd556d6040ced8fd0d6ed52b05cbdbb15a398344d1995402ad3bfcd8efbce94bc') { throw 'PACKAGE_CHANGED' }
    if (@(Get-CimInstance Win32_Process -Filter "Name='Coding Tools MCP.exe'").Count -ne 0) { throw 'PACKAGE_PROCESS_REAPPEARED' }
    $r11SafeNames = @('SystemRoot','WINDIR','COMSPEC','PATH','PATHEXT','TEMP','TMP','APPDATA','LOCALAPPDATA','USERPROFILE','USERNAME','USERDOMAIN','HOMEDRIVE','HOMEPATH','ALLUSERSPROFILE','ProgramData','ProgramFiles','ProgramFiles(x86)','ProgramW6432')
    $r11SafeEnvironment = @($r11SafeNames | ForEach-Object { $r11Value = [Environment]::GetEnvironmentVariable($_); if (-not [string]::IsNullOrEmpty($r11Value)) { $_ + '=' + $r11Value } })
    $r11Startup = New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{ ShowWindow=[uint16]0; CreateFlags=[uint32]16777216; EnvironmentVariables=[string[]]$r11SafeEnvironment }
    $r11Command = '"' + $r11Exe + '" --recovery-host "--user-data-dir=' + $r11Profile + '"'
    $r11Created = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine=$r11Command;CurrentDirectory=$r11Package;ProcessStartupInformation=$r11Startup}
    @{ok=($r11Created.ReturnValue -eq 0);return_value=[int]$r11Created.ReturnValue;pid=[int]$r11Created.ProcessId;at_ms=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();creation_flags=16777216;show_window=0;environment_allowlisted=$true;no_automatic_retry=$true} | ConvertTo-Json -Compress
    if ($r11Created.ReturnValue -ne 0) { exit 2 }
} catch {
    @{ok=$false;code='WMI_LAUNCH_FAILED_RECONCILE_NO_REPLAY';no_automatic_retry=$true;raw_error_emitted=$false} | ConvertTo-Json -Compress
    exit 2
}

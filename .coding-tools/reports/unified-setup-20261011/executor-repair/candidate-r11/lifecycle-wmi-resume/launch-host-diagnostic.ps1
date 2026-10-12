[CmdletBinding()]
param([Parameter(Mandatory=$true)][switch]$OperatorApproved)
$ErrorActionPreference='Stop'
Set-StrictMode -Version 2
$r11Stage='approval_clock';$r11CreateInvoked=$false;$r11CreateReturned=$false;$r11ReturnValue=$null;$r11ChildPid=$null
$r11Package='E:\Github\Tools-Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-initial-proof-1011-r11\win-unpacked'
$r11Exe=Join-Path $r11Package 'Coding Tools MCP.exe'
$r11Profile='C:\Users\daoth\AppData\Roaming\web-mcp-assistant'
try {
    if(-not $OperatorApproved -or [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() -ge 1791739329910){throw 'AUTHORITY_EXPIRED'}
    $r11Stage='package_hash'
    if((Get-FileHash -LiteralPath $r11Exe -Algorithm SHA256).Hash.ToLower() -ne 'd556d6040ced8fd0d6ed52b05cbdbb15a398344d1995402ad3bfcd8efbce94bc'){throw 'PACKAGE_CHANGED'}
    $r11Stage='process_count'
    if(@(Get-CimInstance Win32_Process -Filter "Name='Coding Tools MCP.exe'").Count -ne 0){throw 'PACKAGE_PROCESS_REAPPEARED'}
    $r11Stage='environment'
    $r11Names=@('SystemRoot','WINDIR','COMSPEC','PATH','PATHEXT','TEMP','TMP','APPDATA','LOCALAPPDATA','USERPROFILE','USERNAME','USERDOMAIN','HOMEDRIVE','HOMEPATH','ALLUSERSPROFILE','ProgramData','ProgramFiles','ProgramFiles(x86)','ProgramW6432')
    $r11Environment=@($r11Names | ForEach-Object {$r11Value=[Environment]::GetEnvironmentVariable($_);if(-not [string]::IsNullOrEmpty($r11Value)){$_+'='+$r11Value}})
    $r11Stage='startup_client_instance'
    $r11Startup=New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{ShowWindow=[uint16]0;CreateFlags=[uint32]16777216;EnvironmentVariables=[string[]]$r11Environment}
    $r11Command='"'+$r11Exe+'" --recovery-host "--user-data-dir='+$r11Profile+'"'
    $r11Stage='create_invocation';$r11CreateInvoked=$true
    $r11Created=Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine=$r11Command;CurrentDirectory=$r11Package;ProcessStartupInformation=$r11Startup}
    $r11CreateReturned=$true;$r11Stage='create_result'
    if($null -ne $r11Created.PSObject.Properties['ReturnValue']){$r11ReturnValue=[int]$r11Created.ReturnValue}
    if($null -ne $r11Created.PSObject.Properties['ProcessId'] -and $null -ne $r11Created.ProcessId){$r11ChildPid=[int]$r11Created.ProcessId}
    $r11Ok=($r11ReturnValue -eq 0 -and $null -ne $r11ChildPid -and $r11ChildPid -gt 0)
    @{ok=$r11Ok;stage=$r11Stage;return_value=$r11ReturnValue;pid=$r11ChildPid;create_invoked=$r11CreateInvoked;create_returned=$r11CreateReturned;at_ms=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();creation_flags=16777216;show_window=0;environment_allowlisted=$true;no_automatic_retry=$true;raw_error_emitted=$false} | ConvertTo-Json -Compress
    if(-not $r11Ok){exit 2}
} catch {
    $r11NativeError=$null
    if($null -ne $_.Exception.PSObject.Properties['NativeErrorCode']){$r11NativeError=[int]$_.Exception.NativeErrorCode}
    @{ok=$false;stage=$r11Stage;code='WMI_DIAGNOSTIC_FAILED_RECONCILE_NO_REPLAY';return_value=$r11ReturnValue;pid=$r11ChildPid;create_invoked=$r11CreateInvoked;create_returned=$r11CreateReturned;fqid=([regex]::Replace([string]$_.FullyQualifiedErrorId,'[^A-Za-z0-9_.:,/-]',''));hresult=[int]$_.Exception.HResult;native_error_code=$r11NativeError;exception_type=$_.Exception.GetType().FullName;no_automatic_retry=$true;raw_error_emitted=$false} | ConvertTo-Json -Compress
    exit 2
}

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2
$r11Stage='clock'
try {
    $r11Now=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
    $r11Stage='package_hash'
    $r11Package='E:\Github\Tools-Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-initial-proof-1011-r11\win-unpacked'
    $r11Exe=Join-Path $r11Package 'Coding Tools MCP.exe'
    $r11Hash=(Get-FileHash -LiteralPath $r11Exe -Algorithm SHA256).Hash.ToLower()
    $r11Stage='process_count'
    $r11Count=@(Get-CimInstance Win32_Process -Filter "Name='Coding Tools MCP.exe'").Count
    $r11Stage='environment'
    $r11SafeNames=@('SystemRoot','WINDIR','COMSPEC','PATH','PATHEXT','TEMP','TMP','APPDATA','LOCALAPPDATA','USERPROFILE','USERNAME','USERDOMAIN','HOMEDRIVE','HOMEPATH','ALLUSERSPROFILE','ProgramData','ProgramFiles','ProgramFiles(x86)','ProgramW6432')
    $r11SafeEnvironment=@($r11SafeNames | ForEach-Object {$r11Value=[Environment]::GetEnvironmentVariable($_);if(-not [string]::IsNullOrEmpty($r11Value)){$_+'='+$r11Value}})
    $r11Stage='startup_client_instance'
    $r11Startup=New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{ShowWindow=[uint16]0;CreateFlags=[uint32]16777216;EnvironmentVariables=[string[]]$r11SafeEnvironment}
    $r11Stage='create_whatif_binding_only'
    $r11Command='"'+$r11Exe+'" --recovery-host "--user-data-dir=C:\Users\daoth\AppData\Roaming\web-mcp-assistant"'
    Invoke-CimMethod -ClassName Win32_Process -MethodName Create -WhatIf -Arguments @{CommandLine=$r11Command;CurrentDirectory=$r11Package;ProcessStartupInformation=$r11Startup} | Out-Null
    @{ok=$true;stage=$r11Stage;whatif=$true;runtime_mutated=$false;process_count=$r11Count;package_match=($r11Hash -eq 'd556d6040ced8fd0d6ed52b05cbdbb15a398344d1995402ad3bfcd8efbce94bc');ps_version=[string]$PSVersionTable.PSVersion} | ConvertTo-Json -Compress
} catch {
    $r11NativeError=$null
    if($null -ne $_.Exception.PSObject.Properties['NativeErrorCode']){$r11NativeError=[int]$_.Exception.NativeErrorCode}
    @{ok=$false;stage=$r11Stage;fqid=[string]$_.FullyQualifiedErrorId;exception_type=$_.Exception.GetType().FullName;hresult=[int]$_.Exception.HResult;native_error_code=$r11NativeError;whatif=$true;runtime_mutated=$false;raw_error_emitted=$false;ps_version=[string]$PSVersionTable.PSVersion} | ConvertTo-Json -Compress
    exit 2
}

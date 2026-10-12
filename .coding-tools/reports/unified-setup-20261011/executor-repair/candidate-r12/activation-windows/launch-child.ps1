[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][switch]$OperatorApprovedR12,
    [Parameter(Mandatory=$true)][ValidateSet('host','agent')][string]$Kind,
    [Parameter(Mandatory=$true)][string]$ManifestSha256,
    [Parameter(Mandatory=$true)][string]$ServerReceipt,
    [Parameter(Mandatory=$true)][string]$ServerSha256,
    [Parameter(Mandatory=$true)][string]$RenewalReceipt,
    [Parameter(Mandatory=$true)][string]$RenewalSha256,
    [Parameter(Mandatory=$true)][string]$IntentFile,
    [Parameter(Mandatory=$true)][string]$IntentSha256,
    [Parameter(Mandatory=$true)][long]$ExpiresAtMs,
    [ValidateRange(1,240)][int]$MaxIterations=1
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version 2
$r12Stage='approval';$r12CreateInvoked=$false;$r12CreateReturned=$false;$r12ReturnValue=$null;$r12ChildPid=$null
$r12Repo='E:\Github\Tools-Codex-web'
$r12Package=Join-Path $r12Repo 'dist\windows-candidate-mxc-wsb-cbe1774-policy-contract-1012-r12\win-unpacked'
$r12Profile='C:\Users\daoth\AppData\Roaming\web-mcp-assistant'
$r12Exe=Join-Path $r12Package 'Coding Tools MCP.exe'
$r12Python=Join-Path $r12Package 'resources\resources\native-python\python.exe'
function Get-R12Hash([string]$File) { return ([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([IO.File]::ReadAllBytes($File)))).Replace('-','').ToLowerInvariant() }
function Read-R12Receipt([string]$File,[string]$Hash) {
    if(-not [IO.Path]::IsPathRooted($File) -or $Hash -notmatch '^[a-f0-9]{64}$' -or (Get-R12Hash $File) -ne $Hash){throw 'PIN_CHANGED'}
    $r12Parsed=[IO.File]::ReadAllText($File) | ConvertFrom-Json
    if($null -ne $r12Parsed.PSObject.Properties['public_receipts']) {
        if(@($r12Parsed.public_receipts).Count -ne 1){throw 'RECEIPT_COUNT_CHANGED'}
        return $r12Parsed.public_receipts[0]
    }
    return $r12Parsed
}
try {
    if(-not $OperatorApprovedR12){throw 'EXPLICIT_APPROVAL_REQUIRED'}
    $r12Manifest=Read-R12Receipt (Join-Path $PSScriptRoot 'helper-manifest.json') $ManifestSha256
    foreach($r12Item in $r12Manifest.helper_files){if((Get-R12Hash (Join-Path $PSScriptRoot $r12Item.file)) -ne $r12Item.sha256){throw 'HELPER_CHANGED'}}
    $r12Intent=Read-R12Receipt $IntentFile $IntentSha256
    if($r12Intent.phase -ne $(if($Kind -eq 'host'){'activate'}else{'agent'}) -or $r12Intent.no_automatic_retry -ne $true){throw 'INTENT_CHANGED'}
    $r12Server=Read-R12Receipt $ServerReceipt $ServerSha256
    $r12Renewal=Read-R12Receipt $RenewalReceipt $RenewalSha256
    $r12Now=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
    if($r12Now -ge $ExpiresAtMs -or $ExpiresAtMs -ne $r12Renewal.expires_at_ms -or $r12Renewal.requested_at_ms -le 1791739329910 -or $r12Renewal.requested_at_ms -gt $r12Now -or ($ExpiresAtMs-$r12Renewal.requested_at_ms) -ne 3600000){throw 'NEW_60M_WINDOW_REQUIRED'}
    if($r12Server.ok -ne $true -or $r12Server.host -ne '100.116.112.22' -or $r12Server.service -ne 'codex-control-plane.service' -or $r12Server.source_revision -ne '9cae104420e091811b94f76736a95e94ff333010be344eed7d1274f08601386c' -or $r12Server.admission -ne 'recovery' -or $r12Now-$r12Server.observed_at_ms -lt 0 -or $r12Now-$r12Server.observed_at_ms -ge 60000 -or $r12Server.binding_id -ne 'bind_3e05bf64cb3e4bab93d930ae1692bebb' -or $r12Server.state.schema_version -ne 29){throw 'FRESH_EXACT_SERVER_REQUIRED'}
    foreach($r12Field in @('queued_actions','accepted_actions','open_writers','open_tasks','target_unsettled_actions')){if($r12Server.state.$r12Field -ne 0){throw 'SERVER_BUSY'}}
    if($r12Renewal.ok -ne $true -or $r12Renewal.service_instance_id -ne $r12Server.service_instance_id -or $r12Renewal.host -ne $r12Server.host -or $r12Renewal.service -ne $r12Server.service -or $r12Renewal.source_revision -ne $r12Server.source_revision -or $r12Renewal.binding_id -ne $r12Server.binding_id -or $r12Renewal.admission -ne 'recovery' -or $r12Renewal.context_id -notmatch '^ctx_[A-Za-z0-9]+$' -or $r12Renewal.pilot_id -notmatch '^pilot_[A-Za-z0-9]+$'){throw 'RENEWAL_TARGET_CHANGED'}
    $r12Assignment=$null
    if($null -ne $r12Renewal.PSObject.Properties['policy_assignment']){$r12Assignment=$r12Renewal.policy_assignment}
    if($null -eq $r12Assignment){$r12Assignment=$r12Renewal}
    if($r12Assignment.root -ne $r12Repo -or $r12Assignment.profile -ne 'web-mcp-assistant' -or $r12Assignment.device_id -ne '72ceec2d-e3f2-472f-8e3c-99fffe053035' -or $r12Assignment.workspace_id -ne 'workspace_dda1d78e9a21402aa6213f72af64f788' -or $r12Assignment.workspace_generation -ne 'generation_c2f13e8d02344cf6a38a3f42ecfa59b6' -or $r12Assignment.context_id -ne $r12Renewal.context_id -or $r12Assignment.expires_at_ms -ne $ExpiresAtMs){throw 'EXACT_SCOPE_REQUIRED'}
    $r12Stage='native_module_import';Import-Module (Join-Path $PSHOME 'Modules\CimCmdlets\CimCmdlets.psd1') -ErrorAction Stop
    $r12Stage='package_hash'
    if((Get-R12Hash $r12Exe) -ne '797d4d00d855c05da17117471816ebafc7e2b3397d09c738eea49cf7368bfbb8' -or (Get-R12Hash (Join-Path $r12Package 'resources\app.asar')) -ne '2bd2bed8d9389a9381b49c92eeca6864cd6230db16d3dcff1822742f062888b1'){throw 'PACKAGE_CHANGED'}
    $r12Stage='environment'
    $r12Names=@('SystemRoot','WINDIR','COMSPEC','PATH','PATHEXT','TEMP','TMP','APPDATA','LOCALAPPDATA','USERPROFILE','USERNAME','USERDOMAIN','HOMEDRIVE','HOMEPATH','ALLUSERSPROFILE','ProgramData','ProgramFiles','ProgramFiles(x86)','ProgramW6432')
    $r12Environment=@($r12Names | ForEach-Object {$r12Value=[Environment]::GetEnvironmentVariable($_);if(-not [string]::IsNullOrEmpty($r12Value)){$_+'='+$r12Value}})
    $r12Stage='startup_instance'
    $r12Startup=New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{ShowWindow=[uint16]0;CreateFlags=[uint32]16777216;EnvironmentVariables=[string[]]$r12Environment}
    if($Kind -eq 'host') {
        $r12Argv=@($r12Exe,'--recovery-host',('--user-data-dir='+$r12Profile))
    } else {
        if($MaxIterations -gt [Math]::Floor(($ExpiresAtMs-[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds())/15000)){throw 'AGENT_ITERATION_BOUND_CHANGED'}
        $r12Argv=@($r12Python,'-B','-I','-u',(Join-Path $r12Package 'resources\resources\control-plane\node_agent.py'),'run-connected-agent','--config',(Join-Path $r12Profile 'control-plane-node.json'),'--workspace-registry',(Join-Path $r12Profile 'control-plane-workspaces.json'),'--project-root',$r12Package,'--node',$r12Exe,'--runtime-mode','packaged','--interval-seconds','15','--max-backoff-seconds','60','--max-iterations',[string]$MaxIterations)
    }
    $r12Command=($r12Argv | ForEach-Object {if($_.Contains('"') -or $_.Contains("`r") -or $_.Contains("`n")){throw 'UNSAFE_ARGUMENT'};'"'+$_+'"'}) -join ' '
    if([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() -ge $ExpiresAtMs){throw 'AUTHORITY_EXPIRED_BEFORE_CREATE'}
    $r12Stage='create_invocation';$r12CreateInvoked=$true
    $r12Created=Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine=$r12Command;CurrentDirectory=$r12Package;ProcessStartupInformation=$r12Startup}
    $r12CreateReturned=$true;$r12Stage='create_result'
    if($null -ne $r12Created.PSObject.Properties['ReturnValue']){$r12ReturnValue=[int]$r12Created.ReturnValue}
    if($null -ne $r12Created.PSObject.Properties['ProcessId'] -and $null -ne $r12Created.ProcessId){$r12ChildPid=[int]$r12Created.ProcessId}
    $r12Ok=($r12ReturnValue -eq 0 -and $null -ne $r12ChildPid -and $r12ChildPid -gt 0)
    @{ok=$r12Ok;kind=$Kind;stage=$r12Stage;return_value=$r12ReturnValue;pid=$r12ChildPid;launching_powershell_pid=$PID;create_invoked=$r12CreateInvoked;create_returned=$r12CreateReturned;at_ms=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();creation_flags=16777216;show_window=0;environment_allowlisted=$true;max_iterations=$(if($Kind -eq 'agent'){$MaxIterations}else{$null});no_automatic_retry=$true;raw_error_emitted=$false} | ConvertTo-Json -Compress
    if(-not $r12Ok){exit 2}
} catch {
    @{ok=$false;kind=$Kind;stage=$r12Stage;code='WMI_LAUNCH_FAILED_RECONCILE_NO_REPLAY';return_value=$r12ReturnValue;pid=$r12ChildPid;launching_powershell_pid=$PID;create_invoked=$r12CreateInvoked;create_returned=$r12CreateReturned;no_automatic_retry=$true;raw_error_emitted=$false} | ConvertTo-Json -Compress
    exit 2
}

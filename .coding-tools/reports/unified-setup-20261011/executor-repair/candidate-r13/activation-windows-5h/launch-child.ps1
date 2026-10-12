[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][switch]$OperatorApprovedR13FiveHours,
    [Parameter(Mandatory=$true)][string]$ApprovalId,
    [Parameter(Mandatory=$true)][ValidateSet('host','agent')][string]$Kind,
    [Parameter(Mandatory=$true)][string]$ManifestSha256,
    [Parameter(Mandatory=$true)][string]$ServerReceipt,
    [Parameter(Mandatory=$true)][string]$ServerSha256,
    [Parameter(Mandatory=$true)][string]$RenewalReceipt,
    [Parameter(Mandatory=$true)][string]$RenewalSha256,
    [Parameter(Mandatory=$true)][string]$IntentFile,
    [Parameter(Mandatory=$true)][string]$IntentSha256,
    [Parameter(Mandatory=$true)][long]$ExpiresAtMs,
    [ValidateRange(1,1200)][int]$MaxIterations=1
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version 2
$r13Stage='approval';$r13CreateInvoked=$false;$r13CreateReturned=$false;$r13ReturnValue=$null;$r13ChildPid=$null
$r13Repo='E:\Github\Tools-Codex-web'
$r13Package=Join-Path $r13Repo 'dist\windows-candidate-mxc-wsb-cbe1774-source-fingerprint-1012-r13\win-unpacked'
$r13Profile='C:\Users\daoth\AppData\Roaming\web-mcp-assistant'
$r13Exe=Join-Path $r13Package 'Coding Tools MCP.exe'
$r13Python=Join-Path $r13Package 'resources\resources\native-python\python.exe'
function Get-R13Hash([string]$File) { return ([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([IO.File]::ReadAllBytes($File)))).Replace('-','').ToLowerInvariant() }
function Read-R13Receipt([string]$File,[string]$Hash) {
    if(-not [IO.Path]::IsPathRooted($File) -or $Hash -notmatch '^[a-f0-9]{64}$' -or (Get-R13Hash $File) -ne $Hash){throw 'PIN_CHANGED'}
    $r13Parsed=[IO.File]::ReadAllText($File) | ConvertFrom-Json
    if($null -ne $r13Parsed.PSObject.Properties['public_receipts']) {
        if(@($r13Parsed.public_receipts).Count -ne 1){throw 'RECEIPT_COUNT_CHANGED'}
        return $r13Parsed.public_receipts[0]
    }
    return $r13Parsed
}
try {
    if(-not $OperatorApprovedR13FiveHours){throw 'EXPLICIT_5H_APPROVAL_REQUIRED'}
    $r13Manifest=Read-R13Receipt (Join-Path $PSScriptRoot 'helper-manifest.json') $ManifestSha256
    foreach($r13Item in $r13Manifest.helper_files){if((Get-R13Hash (Join-Path $PSScriptRoot $r13Item.file)) -ne $r13Item.sha256){throw 'HELPER_CHANGED'}}
    $r13Intent=Read-R13Receipt $IntentFile $IntentSha256
    if($r13Intent.phase -ne $(if($Kind -eq 'host'){'activate'}else{'agent'}) -or $r13Intent.no_automatic_retry -ne $true){throw 'INTENT_CHANGED'}
    $r13Server=Read-R13Receipt $ServerReceipt $ServerSha256
    $r13Renewal=Read-R13Receipt $RenewalReceipt $RenewalSha256
    $r13Now=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
    if($ApprovalId -cne 'call_a60e931056bd402b997c6c10b0796d81' -or $r13Renewal.approval_id -cne $ApprovalId){throw 'EXPLICIT_R13_5H_APPROVAL_REQUIRED'}
    if($r13Now -ge $ExpiresAtMs -or $ExpiresAtMs -ne $r13Renewal.expires_at_ms -or $r13Renewal.requested_at_ms -lt 1791751335200 -or ($ExpiresAtMs-$r13Now) -lt 720000 -or $r13Renewal.requested_at_ms -gt $r13Now -or ($ExpiresAtMs-$r13Renewal.requested_at_ms) -ne 18000000 -or $r13Renewal.duration_ms -ne 18000000){throw 'EXACT_APPROVED_NEW_5H_AUTHORITY_WITH_12M_REQUIRED'}
    foreach($r13Receipt in @($r13Server,$r13Renewal)) {
        if($r13Receipt.pilot_id -cnotmatch '^pilot_[a-f0-9]{32}$' -or $r13Receipt.pilot_id -eq 'pilot_98c0b502568a4f888b3106838004c117' -or $r13Receipt.context_id -cnotmatch '^ctx_[a-f0-9]{32}$' -or $r13Receipt.context_id -eq 'ctx_d7a539dd85264a62951fddad0ffa2f23' -or $r13Receipt.approved_window_covered -ne $true -or $r13Receipt.grant_expires_at_ms -lt $ExpiresAtMs){throw 'EXACT_NEW_5H_AUTHORITY_REQUIRED'}
    }
    if($r13Server.next_operation -ne 'owner_approved_r13_initial_verification_5h' -or $r13Server.phase -ne 'r13_5h_read_only_observation' -or $r13Server.next_phase -ne 'authority_renewed' -or $r13Renewal.phase -ne 'r13_5h_authority_renewed'){throw 'EXACT_AUTHORITY_RENEWAL_PHASE_REQUIRED'}
    if($r13Renewal.prior_marker_sha256 -ne 'a3c5c2ee239644a3937fa5f81c7fc14b89544bfde82c4bea56a928ddda408487' -or $r13Renewal.next_marker_sha256 -cnotmatch '^[a-f0-9]{64}$'){throw 'AUTHORITY_MARKER_LINEAGE_CHANGED'}
    foreach($r13Field in @('context_id','pilot_id','requested_at_ms','expires_at_ms')){$r13NextField='next_'+$r13Field;if($r13Server.$r13Field -ne $r13Renewal.$r13Field -or $r13Server.$r13NextField -ne $r13Renewal.$r13Field){throw '5H_RECEIPT_LINKAGE_CHANGED'}}
    if($r13Server.ok -ne $true -or $r13Server.host -ne '100.116.112.22' -or $r13Server.service -ne 'codex-control-plane.service' -or $r13Server.source_revision -ne '9cae104420e091811b94f76736a95e94ff333010be344eed7d1274f08601386c' -or $r13Server.admission -ne 'recovery' -or $r13Now-$r13Server.observed_at_ms -lt 0 -or $r13Now-$r13Server.observed_at_ms -ge 60000 -or $r13Server.binding_id -ne 'bind_3e05bf64cb3e4bab93d930ae1692bebb' -or $r13Server.state.schema_version -ne 29){throw 'FRESH_EXACT_SERVER_REQUIRED'}
    foreach($r13Capability in @('read','write','exec')){if($r13Server.capabilities.$r13Capability -ne $true){throw 'EXACT_CAPABILITIES_REQUIRED'}}
    foreach($r13Field in @('queued_actions','accepted_actions','open_writers','open_tasks','target_unsettled_actions')){if($r13Server.state.$r13Field -ne 0){throw 'SERVER_BUSY'}}
    if($r13Renewal.ok -ne $true -or $r13Renewal.service_instance_id -ne $r13Server.service_instance_id -or $r13Renewal.host -ne $r13Server.host -or $r13Renewal.service -ne $r13Server.service -or $r13Renewal.source_revision -ne $r13Server.source_revision -or $r13Renewal.binding_id -ne $r13Server.binding_id -or $r13Renewal.admission -ne 'recovery' -or $r13Renewal.context_id -notmatch '^ctx_[A-Za-z0-9]+$' -or $r13Renewal.pilot_id -notmatch '^pilot_[A-Za-z0-9]+$'){throw 'RENEWAL_TARGET_CHANGED'}
    $r13Assignment=$null
    if($null -ne $r13Renewal.PSObject.Properties['policy_assignment']){$r13Assignment=$r13Renewal.policy_assignment}
    if($null -eq $r13Assignment){$r13Assignment=$r13Renewal}
    if($r13Assignment.root -ne $r13Repo -or $r13Assignment.profile -ne 'web-mcp-assistant' -or $r13Assignment.device_id -ne '72ceec2d-e3f2-472f-8e3c-99fffe053035' -or $r13Assignment.workspace_id -ne 'workspace_dda1d78e9a21402aa6213f72af64f788' -or $r13Assignment.workspace_generation -ne 'generation_c2f13e8d02344cf6a38a3f42ecfa59b6' -or $r13Assignment.context_id -ne $r13Renewal.context_id -or $r13Assignment.expires_at_ms -ne $ExpiresAtMs){throw 'EXACT_SCOPE_REQUIRED'}
    $r13Stage='native_module_import';Import-Module (Join-Path $PSHOME 'Modules\CimCmdlets\CimCmdlets.psd1') -ErrorAction Stop
    $r13Stage='package_hash'
    if((Get-R13Hash $r13Exe) -ne '797d4d00d855c05da17117471816ebafc7e2b3397d09c738eea49cf7368bfbb8' -or (Get-R13Hash (Join-Path $r13Package 'resources\app.asar')) -ne '2bd2bed8d9389a9381b49c92eeca6864cd6230db16d3dcff1822742f062888b1'){throw 'PACKAGE_CHANGED'}
    $r13Stage='environment'
    $r13Names=@('SystemRoot','WINDIR','COMSPEC','PATH','PATHEXT','TEMP','TMP','APPDATA','LOCALAPPDATA','USERPROFILE','USERNAME','USERDOMAIN','HOMEDRIVE','HOMEPATH','ALLUSERSPROFILE','ProgramData','ProgramFiles','ProgramFiles(x86)','ProgramW6432')
    $r13Environment=@($r13Names | ForEach-Object {$r13Value=[Environment]::GetEnvironmentVariable($_);if(-not [string]::IsNullOrEmpty($r13Value)){$_+'='+$r13Value}})
    $r13Stage='startup_instance'
    $r13Startup=New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{ShowWindow=[uint16]0;CreateFlags=[uint32]16777216;EnvironmentVariables=[string[]]$r13Environment}
    if($Kind -eq 'host') {
        $r13Argv=@($r13Exe,'--recovery-host',('--user-data-dir='+$r13Profile))
    } else {
        if($MaxIterations -gt [Math]::Floor(($ExpiresAtMs-[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds())/15000)){throw 'AGENT_ITERATION_BOUND_CHANGED'}
        $r13Argv=@($r13Python,'-B','-I','-u',(Join-Path $r13Package 'resources\resources\control-plane\node_agent.py'),'run-connected-agent','--config',(Join-Path $r13Profile 'control-plane-node.json'),'--workspace-registry',(Join-Path $r13Profile 'control-plane-workspaces.json'),'--project-root',$r13Package,'--node',$r13Exe,'--runtime-mode','packaged','--interval-seconds','15','--max-backoff-seconds','60','--max-iterations',[string]$MaxIterations)
    }
    $r13Command=($r13Argv | ForEach-Object {if($_.Contains('"') -or $_.Contains("`r") -or $_.Contains("`n")){throw 'UNSAFE_ARGUMENT'};'"'+$_+'"'}) -join ' '
    if([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() -ge $ExpiresAtMs){throw 'AUTHORITY_EXPIRED_BEFORE_CREATE'}
    $r13Stage='create_invocation';$r13CreateInvoked=$true
    $r13Created=Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine=$r13Command;CurrentDirectory=$r13Package;ProcessStartupInformation=$r13Startup}
    $r13CreateReturned=$true;$r13Stage='create_result'
    if($null -ne $r13Created.PSObject.Properties['ReturnValue']){$r13ReturnValue=[int]$r13Created.ReturnValue}
    if($null -ne $r13Created.PSObject.Properties['ProcessId'] -and $null -ne $r13Created.ProcessId){$r13ChildPid=[int]$r13Created.ProcessId}
    $r13Ok=($r13ReturnValue -eq 0 -and $null -ne $r13ChildPid -and $r13ChildPid -gt 0)
    @{ok=$r13Ok;kind=$Kind;stage=$r13Stage;return_value=$r13ReturnValue;pid=$r13ChildPid;launching_powershell_pid=$PID;create_invoked=$r13CreateInvoked;create_returned=$r13CreateReturned;at_ms=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();creation_flags=16777216;show_window=0;environment_allowlisted=$true;max_iterations=$(if($Kind -eq 'agent'){$MaxIterations}else{$null});no_automatic_retry=$true;raw_error_emitted=$false} | ConvertTo-Json -Compress
    if(-not $r13Ok){exit 2}
} catch {
    @{ok=$false;kind=$Kind;stage=$r13Stage;code='WMI_LAUNCH_FAILED_RECONCILE_NO_REPLAY';return_value=$r13ReturnValue;pid=$r13ChildPid;launching_powershell_pid=$PID;create_invoked=$r13CreateInvoked;create_returned=$r13CreateReturned;no_automatic_retry=$true;raw_error_emitted=$false} | ConvertTo-Json -Compress
    exit 2
}

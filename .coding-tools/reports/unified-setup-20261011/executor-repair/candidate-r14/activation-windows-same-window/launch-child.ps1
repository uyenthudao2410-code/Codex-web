[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][switch]$OperatorApprovedR14SameWindow,
    [Parameter(Mandatory=$true)][string]$ApprovalId,
    [Parameter(Mandatory=$true)][ValidateSet('host','agent')][string]$Kind,
    [Parameter(Mandatory=$true)][string]$ManifestSha256,
    [Parameter(Mandatory=$true)][string]$ServerReceipt,
    [Parameter(Mandatory=$true)][string]$ServerSha256,
    [Parameter(Mandatory=$true)][string]$AuthorityReceipt,
    [Parameter(Mandatory=$true)][string]$AuthoritySha256,
    [Parameter(Mandatory=$true)][string]$ApprovalReceipt,
    [Parameter(Mandatory=$true)][string]$ApprovalSha256,
    [Parameter(Mandatory=$true)][string]$IntentFile,
    [Parameter(Mandatory=$true)][string]$IntentSha256,
    [Parameter(Mandatory=$true)][long]$ExpiresAtMs,
    [ValidateRange(1,1200)][int]$MaxIterations=1
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version 2
$r14Stage='approval';$r14CreateInvoked=$false;$r14CreateReturned=$false;$r14ReturnValue=$null;$r14ChildPid=$null
$r14Repo='E:\Github\Tools-Codex-web'
$r14Package=Join-Path $r14Repo 'dist\windows-candidate-mxc-wsb-cbe1774-workflow-timeout-1012-r14\win-unpacked'
$r14Profile='C:\Users\daoth\AppData\Roaming\web-mcp-assistant'
$r14Exe=Join-Path $r14Package 'Coding Tools MCP.exe'
$r14Python=Join-Path $r14Package 'resources\resources\native-python\python.exe'
function Get-R14Hash([string]$File) { return ([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([IO.File]::ReadAllBytes($File)))).Replace('-','').ToLowerInvariant() }
function Read-R14Receipt([string]$File,[string]$Hash) {
    if(-not [IO.Path]::IsPathRooted($File) -or $Hash -notmatch '^[a-f0-9]{64}$' -or (Get-R14Hash $File) -ne $Hash){throw 'PIN_CHANGED'}
    $r14Parsed=[IO.File]::ReadAllText($File) | ConvertFrom-Json
    if($null -ne $r14Parsed.PSObject.Properties['public_receipts']) {
        if(@($r14Parsed.public_receipts).Count -ne 1){throw 'RECEIPT_COUNT_CHANGED'}
        return $r14Parsed.public_receipts[0]
    }
    return $r14Parsed
}
try {
    if(-not $OperatorApprovedR14SameWindow){throw 'EXPLICIT_R14_APPROVAL_REQUIRED'}
    $r14Manifest=Read-R14Receipt (Join-Path $PSScriptRoot 'helper-manifest.json') $ManifestSha256
    foreach($r14Item in $r14Manifest.helper_files){if((Get-R14Hash (Join-Path $PSScriptRoot $r14Item.file)) -ne $r14Item.sha256){throw 'HELPER_CHANGED'}}
    $r14Intent=Read-R14Receipt $IntentFile $IntentSha256
    if($r14Intent.phase -ne $(if($Kind -eq 'host'){'activate'}else{'agent'}) -or $r14Intent.no_automatic_retry -ne $true){throw 'INTENT_CHANGED'}
    $r14Server=Read-R14Receipt $ServerReceipt $ServerSha256
    $r14Authority=Read-R14Receipt $AuthorityReceipt $AuthoritySha256
    $r14Approval=Read-R14Receipt $ApprovalReceipt $ApprovalSha256
    $r14Now=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
    if($ApprovalId -cnotmatch '^call_[A-Za-z0-9_-]+$' -or $ApprovalId -in @('call_a60e931056bd402b997c6c10b0796d81','call_1KzUkF0gMn6uVpHd3QisTzXF') -or $r14Approval.approval_id -cne $ApprovalId -or $r14Approval.approved -ne $true -or $r14Approval.source -ne 'human_user_response' -or $r14Approval.operation -ne 'owner_approved_r14_same_window_activation' -or $r14Approval.candidate_tag -ne 'workflow-timeout-1012-r14'){throw 'EXPLICIT_FUTURE_R14_APPROVAL_REQUIRED'}
    if($ExpiresAtMs -ne 1791776571067 -or $r14Now -ge $ExpiresAtMs -or ($ExpiresAtMs-$r14Now) -lt 720000 -or $r14Authority.expires_at_ms -ne $ExpiresAtMs -or $r14Authority.context_id -ne 'ctx_1e7e2fec6f0e43018db7a51c6980e5c2' -or $r14Authority.requested_at_ms -ne 1791758571067 -or $r14Authority.pilot_id -ne 'pilot_b1cb26c319fb489aae24d3b746318447' -or $r14Authority.approval_id -ne 'call_a60e931056bd402b997c6c10b0796d81' -or $r14Authority.phase -ne 'r13_5h_authority_renewed'){throw 'EXACT_EXISTING_AUTHORITY_WINDOW_REQUIRED'}
    if($r14Approval.context_id -ne $r14Authority.context_id -or $r14Approval.expires_at_ms -ne $ExpiresAtMs -or $r14Approval.pilot_replacement_same_principal_binding_expiry -ne $true -or $r14Approval.r13_owned_executor_cleanup_refresh -ne $true -or $r14Approval.new_approved_patch_verification_canary -ne $true -or $r14Approval.authority_extension -ne $false -or $r14Approval.ubuntu_deploy_or_restart -ne $false -or $r14Approval.windows_reboot -ne $false -or $r14Approval.semantic_acceptance -ne $false -or $r14Approval.approved_at_ms -gt $r14Now){throw 'APPROVAL_SCOPE_CHANGED'}
    foreach($r14Field in @('binding_id','device_id','workspace_id','workspace_generation','profile','root')){if($r14Approval.target.$r14Field -ne $r14Authority.$r14Field -or $r14Server.$r14Field -ne $r14Authority.$r14Field){throw 'TARGET_SCOPE_CHANGED'}}
    if($r14Server.ok -ne $true -or $r14Server.host -ne '100.116.112.22' -or $r14Server.service -ne 'codex-control-plane.service' -or $r14Server.source_revision -ne '9cae104420e091811b94f76736a95e94ff333010be344eed7d1274f08601386c' -or $r14Server.service_instance_id -ne $r14Authority.service_instance_id -or $r14Server.admission -ne 'recovery' -or $r14Now-$r14Server.observed_at_ms -lt 0 -or $r14Now-$r14Server.observed_at_ms -ge 60000 -or $r14Server.binding_id -ne 'bind_3e05bf64cb3e4bab93d930ae1692bebb' -or $r14Server.state.schema_version -ne 29){throw 'FRESH_EXACT_SERVER_REQUIRED'}
    if($r14Server.phase -ne 'r14_same_window_read_only_observation' -or $r14Server.next_operation -ne 'owner_approved_r14_same_window_activation' -or $r14Server.next_phase -notin @('intake_closed','pilot_replaced') -or $r14Server.context_id -ne $r14Authority.context_id -or $r14Server.expires_at_ms -ne $ExpiresAtMs -or $r14Server.prior_pilot_id -ne $r14Authority.pilot_id -or $r14Server.prior_pilot_revoked -ne $true -or $r14Server.approved_window_covered -ne $true -or $r14Server.grant_expires_at_ms -lt $ExpiresAtMs){throw 'EXACT_CLOSED_SAME_WINDOW_SERVER_REQUIRED'}
    if($r14Server.next_phase -eq 'intake_closed'){if($null -ne $r14Server.pilot_id){throw 'REVOKED_PILOT_REUSE'}}else{if($r14Server.pilot_id -cnotmatch '^pilot_[a-f0-9]{32}$' -or $r14Server.pilot_id -eq $r14Authority.pilot_id -or $r14Server.replacement_pilot_same_principal -ne $true -or $r14Server.replacement_pilot_same_binding -ne $true -or $r14Server.replacement_pilot_expires_at_ms -ne $ExpiresAtMs){throw 'REPLACEMENT_SCOPE_CHANGED'}}
    foreach($r14Capability in @('read','write','exec')){if($r14Server.capabilities.$r14Capability -ne $true){throw 'EXACT_CAPABILITIES_REQUIRED'}}
    foreach($r14Field in @('queued_actions','accepted_actions','open_writers','open_tasks','target_unsettled_actions')){if($r14Server.state.$r14Field -ne 0){throw 'SERVER_BUSY'}}
    if($r14Authority.policy_assignment.root -ne $r14Repo -or $r14Authority.policy_assignment.profile -ne 'web-mcp-assistant' -or $r14Authority.policy_assignment.device_id -ne '72ceec2d-e3f2-472f-8e3c-99fffe053035' -or $r14Authority.policy_assignment.workspace_id -ne 'workspace_dda1d78e9a21402aa6213f72af64f788' -or $r14Authority.policy_assignment.workspace_generation -ne 'generation_c2f13e8d02344cf6a38a3f42ecfa59b6' -or $r14Authority.policy_assignment.context_id -ne $r14Authority.context_id -or $r14Authority.policy_assignment.expires_at_ms -ne $ExpiresAtMs){throw 'EXACT_SCOPE_REQUIRED'}
    $r14Stage='native_module_import';Import-Module (Join-Path $PSHOME 'Modules\CimCmdlets\CimCmdlets.psd1') -ErrorAction Stop
    $r14Stage='package_hash'
    if((Get-R14Hash $r14Exe) -ne '8270535a8149b54527172f9b774ea1fd6ed975fde44e4bb91022bdde31dea154' -or (Get-R14Hash (Join-Path $r14Package 'resources\app.asar')) -ne 'f2a1e77b08f7109ccbd4072055da8d281a339dd5f32f154285d3696ad11f6324'){throw 'PACKAGE_CHANGED'}
    $r14Stage='environment'
    $r14Names=@('SystemRoot','WINDIR','COMSPEC','PATH','PATHEXT','TEMP','TMP','APPDATA','LOCALAPPDATA','USERPROFILE','USERNAME','USERDOMAIN','HOMEDRIVE','HOMEPATH','ALLUSERSPROFILE','ProgramData','ProgramFiles','ProgramFiles(x86)','ProgramW6432')
    $r14Environment=@($r14Names | ForEach-Object {$r14Value=[Environment]::GetEnvironmentVariable($_);if(-not [string]::IsNullOrEmpty($r14Value)){$_+'='+$r14Value}})
    $r14Stage='startup_instance'
    $r14Startup=New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{ShowWindow=[uint16]0;CreateFlags=[uint32]16777216;EnvironmentVariables=[string[]]$r14Environment}
    if($Kind -eq 'host') {
        $r14Argv=@($r14Exe,'--recovery-host',('--user-data-dir='+$r14Profile))
    } else {
        if($MaxIterations -gt [Math]::Floor(($ExpiresAtMs-[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds())/15000)){throw 'AGENT_ITERATION_BOUND_CHANGED'}
        $r14Argv=@($r14Python,'-B','-I','-u',(Join-Path $r14Package 'resources\resources\control-plane\node_agent.py'),'run-connected-agent','--config',(Join-Path $r14Profile 'control-plane-node.json'),'--workspace-registry',(Join-Path $r14Profile 'control-plane-workspaces.json'),'--project-root',$r14Package,'--node',$r14Exe,'--runtime-mode','packaged','--interval-seconds','15','--max-backoff-seconds','60','--max-iterations',[string]$MaxIterations)
    }
    $r14Command=($r14Argv | ForEach-Object {if($_.Contains('"') -or $_.Contains("`r") -or $_.Contains("`n")){throw 'UNSAFE_ARGUMENT'};'"'+$_+'"'}) -join ' '
    if([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() -ge $ExpiresAtMs){throw 'AUTHORITY_EXPIRED_BEFORE_CREATE'}
    $r14Stage='create_invocation';$r14CreateInvoked=$true
    $r14Created=Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine=$r14Command;CurrentDirectory=$r14Package;ProcessStartupInformation=$r14Startup}
    $r14CreateReturned=$true;$r14Stage='create_result'
    if($null -ne $r14Created.PSObject.Properties['ReturnValue']){$r14ReturnValue=[int]$r14Created.ReturnValue}
    if($null -ne $r14Created.PSObject.Properties['ProcessId'] -and $null -ne $r14Created.ProcessId){$r14ChildPid=[int]$r14Created.ProcessId}
    $r14Ok=($r14ReturnValue -eq 0 -and $null -ne $r14ChildPid -and $r14ChildPid -gt 0)
    @{ok=$r14Ok;kind=$Kind;stage=$r14Stage;return_value=$r14ReturnValue;pid=$r14ChildPid;launching_powershell_pid=$PID;create_invoked=$r14CreateInvoked;create_returned=$r14CreateReturned;at_ms=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();creation_flags=16777216;show_window=0;environment_allowlisted=$true;max_iterations=$(if($Kind -eq 'agent'){$MaxIterations}else{$null});no_automatic_retry=$true;raw_error_emitted=$false} | ConvertTo-Json -Compress
    if(-not $r14Ok){exit 2}
} catch {
    @{ok=$false;kind=$Kind;stage=$r14Stage;code='WMI_LAUNCH_FAILED_RECONCILE_NO_REPLAY';return_value=$r14ReturnValue;pid=$r14ChildPid;launching_powershell_pid=$PID;create_invoked=$r14CreateInvoked;create_returned=$r14CreateReturned;no_automatic_retry=$true;raw_error_emitted=$false} | ConvertTo-Json -Compress
    exit 2
}

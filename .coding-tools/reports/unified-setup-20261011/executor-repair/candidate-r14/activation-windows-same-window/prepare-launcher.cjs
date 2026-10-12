'use strict';
const fs = require('node:fs'), path = require('node:path');
let text = fs.readFileSync(path.join(__dirname, '../../candidate-r13/activation-windows-5h/launch-child.ps1'), 'utf8')
  .replaceAll('\r\n', '\n').replaceAll('r13', 'r14').replaceAll('R13', 'R14')
  .replaceAll('OperatorApprovedR14FiveHours', 'OperatorApprovedR14SameWindow')
  .replaceAll('RenewalReceipt', 'AuthorityReceipt').replaceAll('RenewalSha256', 'AuthoritySha256')
  .replaceAll('source-fingerprint-1012-r14', 'workflow-timeout-1012-r14');
text = text.replace('    [Parameter(Mandatory=$true)][string]$IntentFile,', '    [Parameter(Mandatory=$true)][string]$ApprovalReceipt,\n    [Parameter(Mandatory=$true)][string]$ApprovalSha256,\n    [Parameter(Mandatory=$true)][string]$IntentFile,');
const start = text.indexOf("    if(-not $OperatorApprovedR14SameWindow)"), end = text.indexOf("    $r14Stage='native_module_import'", start);
if (start < 0 || end < 0) throw new Error('LAUNCH_GUARD_ANCHOR_MISSING');
text = text.slice(0, start) + `    if(-not $OperatorApprovedR14SameWindow){throw 'EXPLICIT_R14_APPROVAL_REQUIRED'}
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
    if($r14Approval.context_id -ne $r14Authority.context_id -or $r14Approval.expires_at_ms -ne $ExpiresAtMs -or $r14Approval.pilot_replacement_same_principal_binding_expiry -ne $true -or $r14Approval.authority_extension -ne $false -or $r14Approval.ubuntu_deploy_or_restart -ne $false -or $r14Approval.windows_reboot -ne $false -or $r14Approval.semantic_acceptance -ne $false -or $r14Approval.approved_at_ms -gt $r14Now){throw 'APPROVAL_SCOPE_CHANGED'}
    foreach($r14Field in @('binding_id','device_id','workspace_id','workspace_generation','profile','root')){if($r14Approval.target.$r14Field -ne $r14Authority.$r14Field -or $r14Server.$r14Field -ne $r14Authority.$r14Field){throw 'TARGET_SCOPE_CHANGED'}}
    if($r14Server.ok -ne $true -or $r14Server.host -ne '100.116.112.22' -or $r14Server.service -ne 'codex-control-plane.service' -or $r14Server.source_revision -ne '9cae104420e091811b94f76736a95e94ff333010be344eed7d1274f08601386c' -or $r14Server.service_instance_id -ne $r14Authority.service_instance_id -or $r14Server.admission -ne 'recovery' -or $r14Now-$r14Server.observed_at_ms -lt 0 -or $r14Now-$r14Server.observed_at_ms -ge 60000 -or $r14Server.binding_id -ne 'bind_3e05bf64cb3e4bab93d930ae1692bebb' -or $r14Server.state.schema_version -ne 29){throw 'FRESH_EXACT_SERVER_REQUIRED'}
    if($r14Server.phase -ne 'r14_same_window_read_only_observation' -or $r14Server.next_operation -ne 'owner_approved_r14_same_window_activation' -or $r14Server.next_phase -notin @('intake_closed','pilot_replaced') -or $r14Server.context_id -ne $r14Authority.context_id -or $r14Server.expires_at_ms -ne $ExpiresAtMs -or $r14Server.prior_pilot_id -ne $r14Authority.pilot_id -or $r14Server.prior_pilot_revoked -ne $true -or $r14Server.approved_window_covered -ne $true -or $r14Server.grant_expires_at_ms -lt $ExpiresAtMs){throw 'EXACT_CLOSED_SAME_WINDOW_SERVER_REQUIRED'}
    if($r14Server.next_phase -eq 'intake_closed'){if($null -ne $r14Server.pilot_id){throw 'REVOKED_PILOT_REUSE'}}else{if($r14Server.pilot_id -cnotmatch '^pilot_[a-f0-9]{32}$' -or $r14Server.pilot_id -eq $r14Authority.pilot_id -or $r14Server.replacement_pilot_same_principal -ne $true -or $r14Server.replacement_pilot_same_binding -ne $true -or $r14Server.replacement_pilot_expires_at_ms -ne $ExpiresAtMs){throw 'REPLACEMENT_SCOPE_CHANGED'}}
    foreach($r14Capability in @('read','write','exec')){if($r14Server.capabilities.$r14Capability -ne $true){throw 'EXACT_CAPABILITIES_REQUIRED'}}
    foreach($r14Field in @('queued_actions','accepted_actions','open_writers','open_tasks','target_unsettled_actions')){if($r14Server.state.$r14Field -ne 0){throw 'SERVER_BUSY'}}
    if($r14Authority.policy_assignment.root -ne $r14Repo -or $r14Authority.policy_assignment.profile -ne 'web-mcp-assistant' -or $r14Authority.policy_assignment.device_id -ne '72ceec2d-e3f2-472f-8e3c-99fffe053035' -or $r14Authority.policy_assignment.workspace_id -ne 'workspace_dda1d78e9a21402aa6213f72af64f788' -or $r14Authority.policy_assignment.workspace_generation -ne 'generation_c2f13e8d02344cf6a38a3f42ecfa59b6' -or $r14Authority.policy_assignment.context_id -ne $r14Authority.context_id -or $r14Authority.policy_assignment.expires_at_ms -ne $ExpiresAtMs){throw 'EXACT_SCOPE_REQUIRED'}
` + text.slice(end);
text = text.replaceAll('797d4d00d855c05da17117471816ebafc7e2b3397d09c738eea49cf7368bfbb8', '8270535a8149b54527172f9b774ea1fd6ed975fde44e4bb91022bdde31dea154')
  .replaceAll('2bd2bed8d9389a9381b49c92eeca6864cd6230db16d3dcff1822742f062888b1', 'f2a1e77b08f7109ccbd4072055da8d281a339dd5f32f154285d3696ad11f6324');
fs.writeFileSync(path.join(__dirname, 'launch-child.ps1'), text, { flag: 'wx' });
process.stdout.write(JSON.stringify({ ok: true, generated: 'launch-child.ps1', process_started: false }) + '\n');

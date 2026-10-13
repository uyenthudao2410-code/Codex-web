param([ValidateSet('recovered','after-stop')][string]$Stage)
$ErrorActionPreference='Stop'
$server=Join-Path $PSScriptRoot ('server-before-'+$Stage+'-'+[guid]::NewGuid().ToString('N')+'.json')
Get-Content -LiteralPath 'E:\DEV\Codex-web\.coding-tools\reports\shared-write-exec-20261012\inspect-final-server-surface.py' -Raw | ssh.exe -T -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=yes svhome@100.116.112.22 python3 -B - | Set-Content -LiteralPath $server -Encoding utf8
if($LASTEXITCODE){throw 'SERVER_OBSERVER_FAILED'}
$s=Get-Content -LiteralPath $server -Raw|ConvertFrom-Json
if($s.node.readiness -ne 'ready' -or $s.node.activation_epoch -notmatch '^activation-' -or $s.current_generation_census.open_tasks -ne 0 -or $s.current_generation_census.unsettled_current_generation_actions -ne 0 -or $s.current_generation_census.unreleased_writers -ne 0){throw 'FRESH_READY_NODE_AND_IDLE_CENSUS_REQUIRED'}
$pilot=$s.live_pilot|Where-Object decision_id -eq 'pilot_dfb3174078d842299c41c6638830e505'
$args=@{ExecuteConfirmedReadyPilot=$true;BindingId=$pilot.binding_id;WorkspaceGeneration=$pilot.workspace_generation;PilotDecisionId=$pilot.decision_id;ActivationEpoch=$s.node.activation_epoch;ProcessInstanceId=$s.node.runtime_instance_id;ServerInstanceId=$s.node.mcp_server_instance_id;LocalToolContractSha256='0e4733844a471814a3a6240fa9c0423b56195ab80f6e5283b5c978e28edaaed4';FacadeSchemaVersion=$s.tool_contract.schema_version;FacadeContractSha256=$s.tool_contract.sha256;ServicePid=$s.service_pid;AttemptId=[guid]::NewGuid()}
$console=Join-Path $PSScriptRoot ($Stage+'-exec-console-'+$args.AttemptId.ToString('N')+'.txt')
@{operation='r8_fresh_original_exec_start';stage=$Stage;attempt=$args.AttemptId;epoch=$s.node.activation_epoch;process=$s.node.runtime_instance_id;server=$s.node.mcp_server_instance_id;console=$console}|ConvertTo-Json -Compress
& (Join-Path $PSScriptRoot 'invoke-shared-exec-after-stop-r8.ps1') @args *> $console
$code=$LASTEXITCODE
Get-Content -LiteralPath $console -Tail 1
exit $code

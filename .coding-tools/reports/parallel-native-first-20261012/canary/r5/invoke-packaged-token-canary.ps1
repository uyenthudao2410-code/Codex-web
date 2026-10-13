param([Parameter(Mandatory=$true)][switch]$ExecuteConfirmedPackagedToken)
$ErrorActionPreference='Stop'
if (-not $ExecuteConfirmedPackagedToken) { throw 'EXPLICIT_PACKAGED_TOKEN_EXECUTION_REQUIRED' }
$root='E:\DEV\Codex-web'
$here=$PSScriptRoot
$pinsPath=Join-Path $root '.coding-tools\reports\parallel-native-first-20261012\canary\r4\codex-ready-pins-timefix.json'
$scriptPath=Join-Path $here 'run-token-child-packaged-canary.py'
$basePath=Join-Path $here '..\r4\run-native-first-canary.py'
$pins=Get-Content -LiteralPath $pinsPath -Raw | ConvertFrom-Json
$attempt=[guid]::NewGuid().ToString('N')
$receipt=Join-Path $here ('packaged-token-canary-'+$attempt+'.ndjson')
if (Test-Path -LiteralPath $receipt) { throw 'ATTEMPT_RECEIPT_EXISTS' }
$pinsB=[Convert]::ToBase64String([IO.File]::ReadAllBytes($pinsPath))
$scriptB=[Convert]::ToBase64String([IO.File]::ReadAllBytes($scriptPath))
$baseB=[Convert]::ToBase64String([IO.File]::ReadAllBytes($basePath))
$remote=@"
import base64, types
_BASE_CANARY=types.ModuleType('reviewed_native_canary')
exec(compile(base64.b64decode('$baseB'),'reviewed-run-native-first-canary.py','exec'),_BASE_CANARY.__dict__)
_REVIEWED_PINS_BYTES=base64.b64decode('$pinsB')
exec(compile(base64.b64decode('$scriptB'),'run-token-child-packaged-canary.py','exec'))
"@
$ssh=@('-T','-o','BatchMode=yes','-o','ConnectTimeout=5','-o','StrictHostKeyChecking=yes','svhome@100.116.112.22','python3','-B','-',
  ('--principal-id='+$pins.principal_id),('--grant-id='+$pins.grant_id),('--device-id='+$pins.device_id),('--workspace-id='+$pins.workspace_id),('--binding-id='+$pins.binding_id),('--workspace-generation='+$pins.workspace_generation),('--pilot-decision-id='+$pins.pilot_decision_id),('--activation-epoch='+$pins.activation_epoch),('--process-instance-id='+$pins.process_instance_id),('--server-instance-id='+$pins.server_instance_id),('--local-tool-contract-sha256='+$pins.local_tool_contract_sha256),('--facade-contract-sha256='+$pins.facade_contract_sha256),('--serving-mcp-facade-sha256='+$pins.serving_mcp_facade_sha256),('--serving-node-agent-sha256='+$pins.serving_node_agent_sha256),('--facade-schema-version='+$pins.facade_schema_version),('--service-pid='+$pins.service_pid),'--attempt-id',$attempt,'--credential-file','/home/svhome/.config/codex-control-plane/ubuntu-root-mcp-authorization','--execute-confirmed-packaged-token')
$remote | & ssh.exe @ssh | Tee-Object -FilePath $receipt
if ($LASTEXITCODE -ne 0) { throw 'TOKEN_CANARY_FAILED_INSPECT_RECEIPT' }
Write-Output (ConvertTo-Json -Compress @{ok=$true;attempt_id=$attempt;receipt_path=$receipt})

[CmdletBinding()]
param(
  [ValidateSet('Install','Uninstall','Status','Run','Once')]
  [string]$Action = 'Run',
  [string]$Executable = '',
  [string]$AppRoot = '',
  [switch]$Packaged,
  [string]$ManifestPath = '',
  [string]$StatusPath = ''
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$TaskName = 'WebMCP Recovery Supervisor'
$PollSeconds = 5
$FailureThreshold = 4
$StartupCooldownSeconds = 20
$RestartWindowMinutes = 10
$RestartLimit = 4
$SuppressionMinutes = 5
$MaxJsonBytes = 65536
$MaxDescriptorBytes = 16384
$ReplacementStopTimeoutSeconds = 15
$InstallReadyTimeoutSeconds = 15
$DeferredDirectoryName = 'full-clean-activation'
$DeferredRequestKind = 'full_clean_activation_deferred'
$DeferredLaunchKind = 'full_clean_activation_supervisor_launch'
$DeferredOperationPattern = 'full-clean-cli-[A-Za-z0-9_-]{15,127}'
$MaxDeferredRequestBytes = 65536

function Get-DataRoot { Join-Path ([Environment]::GetFolderPath('ApplicationData')) 'web-mcp-assistant' }
function Get-InstallRoot { Join-Path (Get-DataRoot) 'recovery-supervisor' }
function Get-LegacyInstallRoot { Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'WebMcpRecoverySupervisor' }
function Get-InstalledScript { Join-Path (Get-InstallRoot) 'recovery-supervisor.ps1' }
function Get-SourceLauncher { Join-Path $PSScriptRoot 'recovery-supervisor-launcher.vbs' }
function Get-InstalledLauncher { Join-Path (Get-InstallRoot) 'recovery-supervisor-launcher.vbs' }
function Get-InstalledManifest { Join-Path (Get-InstallRoot) 'manifest.json' }
function Get-StopRequest {
  # Explicit manifest/status paths are used by packaged smoke tests and local
  # harnesses. Keep their stop sentinel in the same isolated data directory so
  # a legitimate stop.request from the installed development supervisor does
  # not force every independent Once/Run invocation into `stopping`.
  if($StatusPath){return Join-Path (Split-Path -Parent ([IO.Path]::GetFullPath($StatusPath))) 'stop.request'}
  if($ManifestPath){return Join-Path (Split-Path -Parent ([IO.Path]::GetFullPath($ManifestPath))) 'stop.request'}
  Join-Path (Get-InstallRoot) 'stop.request'
}
function Get-Sha256File([string]$Path) {
  $sha = [Security.Cryptography.SHA256]::Create()
  $stream = $null
  try {
    $stream = [IO.File]::Open(
      $Path,
      [IO.FileMode]::Open,
      [IO.FileAccess]::Read,
      [IO.FileShare]::Read
    )
    ([BitConverter]::ToString($sha.ComputeHash($stream))).Replace('-','').ToLowerInvariant()
  }
  finally {
    if ($null -ne $stream) { $stream.Dispose() }
    $sha.Dispose()
  }
}
function Get-Sha256Text([string]$Text) {
  $sha = [Security.Cryptography.SHA256]::Create()
  try { ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($Text)))).Replace('-','').ToLowerInvariant() }
  finally { $sha.Dispose() }
}
function Ensure-Parent([string]$Path) { $p=Split-Path -Parent $Path; if($p -and -not(Test-Path -LiteralPath $p)){New-Item -ItemType Directory -Path $p -Force|Out-Null} }
function Write-JsonAtomic([string]$Path,$Value) {
  Ensure-Parent $Path
  $json=$Value|ConvertTo-Json -Depth 8 -Compress
  if([Text.Encoding]::UTF8.GetByteCount($json)-gt $MaxJsonBytes){throw 'Recovery Supervisor JSON exceeded bound.'}
  $tmp="$Path.tmp-$PID-$([Guid]::NewGuid().ToString('N'))"
  [IO.File]::WriteAllText($tmp,$json,(New-Object Text.UTF8Encoding($false)))
  Move-Item -LiteralPath $tmp -Destination $Path -Force
}
function Read-BoundedJson([string]$Path,[int]$MaxBytes,[switch]$Required) {
  if(-not(Test-Path -LiteralPath $Path -PathType Leaf)){if($Required){throw "Required JSON file missing: $Path"};return $null}
  if((Get-Item -LiteralPath $Path).Length -gt $MaxBytes){throw "JSON file exceeded bound: $Path"}
  try { [IO.File]::ReadAllText($Path,[Text.Encoding]::UTF8)|ConvertFrom-Json } catch { throw "JSON file invalid: $Path" }
}
function Test-AbsoluteSafePath([string]$Value) {
  if([string]::IsNullOrWhiteSpace($Value)-or -not[IO.Path]::IsPathRooted($Value)){return $false}
  -not($Value.Contains('"')-or $Value.Contains("`r")-or $Value.Contains("`n"))
}
function Test-ProcessAlive([int]$ProcessId) { if($ProcessId-le 0){return $false};try{Get-Process -Id $ProcessId -ErrorAction Stop|Out-Null;return $true}catch{return $false} }
function Test-PathEqual([string]$A,[string]$B) { [string]::Equals([IO.Path]::GetFullPath($A),[IO.Path]::GetFullPath($B),[StringComparison]::OrdinalIgnoreCase) }

function Assert-Manifest($M) {
  if($null-eq $M -or [int]$M.schema_version-ne 1){throw 'Recovery Supervisor manifest schema invalid.'}
  $mode=[string]$M.mode; if($mode-notin @('development','packaged')){throw 'Recovery Supervisor manifest mode invalid.'}
  foreach($field in @('executable','app_root','data_root')){if(-not(Test-AbsoluteSafePath ([string]$M.$field))){throw "Manifest $field invalid."}}
  if(-not(Test-Path -LiteralPath ([string]$M.executable) -PathType Leaf)){throw 'Recovery Supervisor executable missing.'}
  if(-not(Test-Path -LiteralPath ([string]$M.app_root) -PathType Container)){throw 'Recovery Supervisor app root missing.'}
  if([string]$M.executable_sha256-notmatch '^[a-f0-9]{64}$'){throw 'Recovery Supervisor executable hash invalid.'}
  $args=@($M.arguments)
  if($mode-eq 'development'){
    if($args.Count-ne 2 -or -not(Test-PathEqual ([string]$args[0]) ([string]$M.app_root)) -or [string]$args[1]-ne '--recovery-host'){throw 'Development argv is not fixed recovery-host argv.'}
  } elseif($args.Count-ne 1 -or [string]$args[0]-ne '--recovery-host'){throw 'Packaged argv is not fixed recovery-host argv.'}
  $agentFields=@('control_plane_python_path','control_plane_python_sha256','control_plane_node_agent_path','control_plane_node_agent_sha256','control_plane_node_path','control_plane_node_sha256');$present=@($agentFields|Where-Object{$null-ne$M.PSObject.Properties[$_]});if($present.Count-ne0-and$present.Count-ne$agentFields.Count){throw 'Control-plane agent identity is incomplete.'};if($present.Count-eq$agentFields.Count){foreach($field in @('control_plane_python_path','control_plane_node_agent_path','control_plane_node_path')){if(-not(Test-AbsoluteSafePath ([string]$M.$field))-or-not(Test-Path -LiteralPath ([string]$M.$field) -PathType Leaf)){throw "Manifest $field invalid."}};foreach($field in @('control_plane_python_sha256','control_plane_node_agent_sha256','control_plane_node_sha256')){if([string]$M.$field-notmatch'^[a-f0-9]{64}$'){throw "Manifest $field invalid."}};if((Get-Sha256File ([string]$M.control_plane_python_path))-ne[string]$M.control_plane_python_sha256-or(Get-Sha256File ([string]$M.control_plane_node_agent_path))-ne[string]$M.control_plane_node_agent_sha256-or(Get-Sha256File ([string]$M.control_plane_node_path))-ne[string]$M.control_plane_node_sha256){throw 'Control-plane agent identity hash mismatch.'};if($mode-eq'packaged'-and-not(Test-PathEqual ([string]$M.control_plane_node_path) ([string]$M.executable))){throw 'Packaged control-plane node runtime must be the Recovery Host executable.'};if($mode-eq'development'-and[IO.Path]::GetFileName([string]$M.control_plane_node_path)-ine'node.exe'){throw 'Development control-plane node runtime must be node.exe.'}}
}
function Get-ManifestPath { if($ManifestPath){[IO.Path]::GetFullPath($ManifestPath)}else{Get-InstalledManifest} }
function Get-StatePath($M) { if($StatusPath){[IO.Path]::GetFullPath($StatusPath)}else{Join-Path ([string]$M.data_root) 'recovery-supervisor-status.json'} }
function Get-LockStatus([string]$DataRoot) {
  try{$l=Read-BoundedJson (Join-Path $DataRoot 'recovery-host.lock') $MaxDescriptorBytes;$p=if($null-ne$l){[int]$l.pid}else{0};[pscustomobject]@{alive=(Test-ProcessAlive $p);pid=$p}}
  catch{[pscustomobject]@{alive=$false;pid=0}}
}
function Invoke-RecoveryPing([string]$DataRoot) {
  $d=$null
  try{
    $d=Read-BoundedJson (Join-Path $DataRoot 'recovery-host.json') $MaxDescriptorBytes
    if($null-eq$d){return [pscustomobject]@{healthy=$false;code='DESCRIPTOR_MISSING';owner_alive=$false;owner_pid=0;instance_id=$null}}
    $ownerPid=[int]$d.owner_pid;$alive=Test-ProcessAlive $ownerPid
    if([int]$d.version-ne 1 -or [string]$d.host-ne '127.0.0.1' -or [string]$d.owner-ne 'recovery-host'){return [pscustomobject]@{healthy=$false;code='DESCRIPTOR_INVALID';owner_alive=$alive;owner_pid=$ownerPid;instance_id=$null}}
    $port=[int]$d.port;$token=[string]$d.token;$instance=[string]$d.instance_id
    if($port-lt 1 -or $port-gt 65535 -or $token.Length-lt 32 -or [string]::IsNullOrWhiteSpace($instance)){return [pscustomobject]@{healthy=$false;code='DESCRIPTOR_INCOMPLETE';owner_alive=$alive;owner_pid=$ownerPid;instance_id=$instance}}
    if(-not$alive){return [pscustomobject]@{healthy=$false;code='OWNER_DEAD';owner_alive=$false;owner_pid=$ownerPid;instance_id=$instance}}
    $r=[Net.HttpWebRequest]::Create("http://127.0.0.1:$port/v1/call");$r.Method='POST';$r.Proxy=$null;$r.Timeout=1500;$r.ReadWriteTimeout=1500;$r.ContentType='application/json';$r.Headers.Add('Authorization',"Bearer $token")
    $bytes=[Text.Encoding]::UTF8.GetBytes('{"action":"recovery.ping","args":[]}');$r.ContentLength=$bytes.Length;$s=$r.GetRequestStream();try{$s.Write($bytes,0,$bytes.Length)}finally{$s.Dispose()}
    $resp=$r.GetResponse();try{$reader=New-Object IO.StreamReader($resp.GetResponseStream(),[Text.Encoding]::UTF8);try{$text=$reader.ReadToEnd()}finally{$reader.Dispose()}}finally{$resp.Dispose()}
    if([Text.Encoding]::UTF8.GetByteCount($text)-gt $MaxJsonBytes){throw 'Ping response exceeded bound.'};$p=$text|ConvertFrom-Json
    if($p.ok-ne$true -or $p.data.ready-ne$true -or [int]$p.data.pid-ne$ownerPid -or [string]$p.data.instance_id-ne$instance){return [pscustomobject]@{healthy=$false;code='PING_IDENTITY_MISMATCH';owner_alive=$true;owner_pid=$ownerPid;instance_id=$instance}}
    [pscustomobject]@{healthy=$true;code='HEALTHY';owner_alive=$true;owner_pid=$ownerPid;instance_id=$instance}
  }catch{$ownerPid=0;$instance=$null;try{if($null-ne$d){$ownerPid=[int]$d.owner_pid;$instance=[string]$d.instance_id}}catch{};[pscustomobject]@{healthy=$false;code='PING_UNAVAILABLE';owner_alive=(Test-ProcessAlive $ownerPid);owner_pid=$ownerPid;instance_id=$instance}}
}
function Convert-ToUtc($Value){if($null-eq$Value-or[string]::IsNullOrWhiteSpace([string]$Value)){return $null};try{[DateTimeOffset]::Parse([string]$Value).ToUniversalTime()}catch{$null}}
function Get-OptionalProperty($Object,[string]$Name,$Default){if($null-eq$Object){return $Default};if($Object-is[Collections.IDictionary]){if($Object.Contains($Name)){return $Object[$Name]};return $Default};$property=$Object.PSObject.Properties[$Name];if($null-eq$property){return $Default};$property.Value}
function Get-ControlPlaneAgentConfigPath($M) { Join-Path ([string]$M.data_root) 'control-plane-node.json' }
function Get-ControlPlaneAgentPolicyPath($M) { Join-Path ([string]$M.data_root) 'control-plane-read-only-policy.json' }
function Get-ControlPlaneWorkspaceRegistryPath($M) { Join-Path ([string]$M.data_root) 'control-plane-workspaces.json' }
function Resolve-ControlPlaneNodePath($M) {
  $mode=[string](Get-OptionalProperty $M 'mode' '')
  if($mode-eq'packaged') {
    $packaged=[string](Get-OptionalProperty $M 'executable' '')
    if([string]::IsNullOrWhiteSpace($packaged)){try{$packaged=[string](Resolve-Inputs).executable}catch{return $null}}
    if(-not(Test-AbsoluteSafePath $packaged)-or-not(Test-Path -LiteralPath $packaged -PathType Leaf)){return $null}
    return [IO.Path]::GetFullPath($packaged)
  }
  if($mode-eq'development') {
    try {
      $command=Get-Command -Name 'node.exe' -CommandType Application -ErrorAction Stop|Select-Object -First 1
      $node=[string]$command.Source
    } catch { return $null }
    if(-not(Test-AbsoluteSafePath $node)-or-not(Test-Path -LiteralPath $node -PathType Leaf)-or[IO.Path]::GetFileName($node)-ine'node.exe'){return $null}
    return [IO.Path]::GetFullPath($node)
  }
  $null
}
function Get-ControlPlaneAgentPaths($M) {
  $mode=[string](Get-OptionalProperty $M 'mode' '')
  $node=Resolve-ControlPlaneNodePath $M
  if($mode-eq'packaged') {
    $resources=Join-Path ([string]$M.app_root) 'resources\resources'
    return [pscustomobject]@{runtime_mode=$mode;python_path=(Join-Path $resources 'native-python\python.exe');agent_path=(Join-Path $resources 'control-plane\node_agent.py');node_path=$node}
  }
  if($mode-eq'development') {
    $resources=Join-Path ([string]$M.app_root) 'resources'
    $agentRoot=Join-Path ([string]$M.app_root) 'control-plane\control_plane'
    return [pscustomobject]@{runtime_mode=$mode;python_path=(Join-Path $resources 'native-python\python.exe');agent_path=(Join-Path $agentRoot 'node_agent.py');node_path=$node}
  }
  $null
}
function Get-ControlPlaneStandingPolicyCandidates($M) {
  @(
    [pscustomobject]@{lane='file_read';path=(Join-Path ([string]$M.data_root) 'control-plane-file-read-policy.json');fields=@('schema_version','enabled','server_origin','owner_id','device_id','endpoint_id','workspace_id','workspace_generation','expires_at_ms','facade_contract','allowed_relative_paths','max_bytes','max_lines','authority_mode')},
    [pscustomobject]@{lane='approved_patch';path=(Join-Path ([string]$M.data_root) 'control-plane-approved-patch-policy.json');fields=@('schema_version','enabled','server_origin','owner_id','device_id','endpoint_id','workspace_id','workspace_generation','expires_at_ms','facade_contract','allowed_relative_paths','max_patch_bytes','max_file_bytes','validation_profile','authority_mode')},
    [pscustomobject]@{lane='exec';path=(Join-Path ([string]$M.data_root) 'control-plane-exec-policy.json');fields=@('schema_version','enabled','server_origin','owner_id','device_id','endpoint_id','workspace_id','workspace_generation','expires_at_ms','facade_contract','allowed_argv_prefixes','max_timeout_ms','max_output_bytes','max_concurrent','authority_mode')}
  )
}
function Test-ControlPlanePropertySet($Object,$Expected) {
  if($Object -isnot [PSCustomObject]){return $false}
  $actual=@($Object.PSObject.Properties.Name|Sort-Object)
  $expected=@($Expected|Sort-Object)
  ($actual -join "`n") -eq ($expected -join "`n")
}
function Test-ControlPlaneNodeCredential($Config) {
  # The Python agent migrates plaintext credentials to DPAPI after the first
  # authenticated read.  Supervisor must accept either representation without
  # ever decrypting, logging or forwarding the secret itself.
  $plain=[string](Get-OptionalProperty $Config 'node_secret' '')
  $protected=[string](Get-OptionalProperty $Config 'node_secret_dpapi' '')
  $plain.Length -ge 16 -or $protected -match '^dpapi-v1:.{16,}$'
}
function Test-ControlPlaneWorkspaceRegistration([string]$RegistryPath,$Policy) {
  # The Python agent re-resolves the selected root immediately before every
  # admission/effect.  This supervisor preflight is deliberately smaller: it
  # prevents a stale or removed local registration from repeatedly spawning an
  # agent that can never pass its own stricter check.
  try {
    $registry=Read-BoundedJson $RegistryPath $MaxJsonBytes -Required
    if($registry-isnot[PSCustomObject]-or[int](Get-OptionalProperty $registry 'schema_version' 0)-ne1){return 'workspace_registry_unavailable'}
    $entriesProperty=$registry.PSObject.Properties['entries']
    if($null-eq$entriesProperty-or$entriesProperty.Value-is[string]){return 'workspace_registry_unavailable'}
    $entries=@($entriesProperty.Value)
    if($entries.Count-gt64){return 'workspace_registry_unavailable'}
    $matches=@($entries|Where-Object{
      $_-is[PSCustomObject]-and
      [string](Get-OptionalProperty $_ 'workspace_id' '')-eq[string]$Policy.workspace_id-and
      [string](Get-OptionalProperty $_ 'workspace_generation' '')-eq[string]$Policy.workspace_generation
    })
    if($matches.Count-ne1){return 'workspace_registration_not_current'}
    $root=[string](Get-OptionalProperty $matches[0] 'canonical_path' '')
    if(-not(Test-AbsoluteSafePath $root)-or-not(Test-Path -LiteralPath $root -PathType Container)){return 'workspace_registration_not_current'}
    'current'
  } catch { 'workspace_registry_unavailable' }
}
function Get-ControlPlaneOrigin([string]$Value) {
  try { $uri=[Uri]$Value } catch { return $null }
  if(-not$uri.IsAbsoluteUri-or$uri.Scheme-notin@('http','https')-or[string]::IsNullOrWhiteSpace($uri.Host)-or$uri.UserInfo-or$uri.Query-or$uri.Fragment-or$uri.AbsolutePath-notin@('','/')){return $null}
  # $Host is a read-only PowerShell automatic variable (case-insensitive).
  $originHost=$uri.Host.ToLowerInvariant()
  if($originHost.Contains(':')){try{$originHost="[$([Net.IPAddress]::Parse($originHost.Trim([char[]]'[]')).ToString().ToLowerInvariant())]"}catch{return $null}}
  $originPort=[int]$uri.Port
  "$($uri.Scheme.ToLowerInvariant())://$originHost$(if(($uri.Scheme-eq'http'-and$originPort-ne80)-or($uri.Scheme-eq'https'-and$originPort-ne443)){":$originPort"})"
}
function Get-ControlPlaneAgentSpec($M) {
  $fields=@('control_plane_python_path','control_plane_python_sha256','control_plane_node_agent_path','control_plane_node_agent_sha256','control_plane_node_path','control_plane_node_sha256')
  if(@($fields|Where-Object{$null-eq$M.PSObject.Properties[$_]}).Count-ne0){return [pscustomobject]@{eligible=$false;state='manifest_legacy';pid=$null}}
  $paths=Get-ControlPlaneAgentPaths $M
  if($null-eq$paths){return [pscustomobject]@{eligible=$false;state='unsupported_mode';pid=$null}}
  $python=[string]$paths.python_path;$agent=[string]$paths.agent_path;$node=[string]$paths.node_path
  if([string]::IsNullOrWhiteSpace($node)-or-not(Test-PathEqual ([string]$M.control_plane_node_path) $node)-or-not(Test-Path -LiteralPath $node -PathType Leaf)-or[string]$M.control_plane_node_sha256-notmatch'^[a-f0-9]{64}$'-or(Get-Sha256File $node)-ne[string]$M.control_plane_node_sha256-or-not(Test-PathEqual ([string]$M.control_plane_python_path) $python)-or-not(Test-PathEqual ([string]$M.control_plane_node_agent_path) $agent)-or[string]$M.control_plane_python_sha256-notmatch'^[a-f0-9]{64}$'-or[string]$M.control_plane_node_agent_sha256-notmatch'^[a-f0-9]{64}$'-or-not(Test-Path -LiteralPath $python -PathType Leaf)-or-not(Test-Path -LiteralPath $agent -PathType Leaf)-or(Get-Sha256File $python)-ne[string]$M.control_plane_python_sha256-or(Get-Sha256File $agent)-ne[string]$M.control_plane_node_agent_sha256){return [pscustomobject]@{eligible=$false;state='integrity_unproven';pid=$null}}
  $configPath=Get-ControlPlaneAgentConfigPath $M;if(-not(Test-Path -LiteralPath $configPath -PathType Leaf)){return [pscustomobject]@{eligible=$false;state='waiting_for_pairing';pid=$null}};$workspaceRegistryPath=Get-ControlPlaneWorkspaceRegistryPath $M
  try{$config=Read-BoundedJson $configPath $MaxJsonBytes -Required}catch{return [pscustomobject]@{eligible=$false;state='config_unavailable';pid=$null}}
  if($config -isnot [PSCustomObject]){return [pscustomobject]@{eligible=$false;state='config_invalid';pid=$null}}
  $origin=Get-ControlPlaneOrigin ([string](Get-OptionalProperty $config 'server_url' ''))
  $deviceId=[string](Get-OptionalProperty $config 'device_id' '')
  $endpointId=[string](Get-OptionalProperty $config 'endpoint_id' '')
  if($null-eq$origin-or[string]::IsNullOrWhiteSpace($deviceId)-or[string]::IsNullOrWhiteSpace($endpointId)-or-not(Test-ControlPlaneNodeCredential $config)){return [pscustomobject]@{eligible=$false;state='policy_config_mismatch';pid=$null}}
  $candidateStates=@();$eligiblePolicies=0
  foreach($candidate in @(Get-ControlPlaneStandingPolicyCandidates $M)) {
    if(-not(Test-Path -LiteralPath ([string]$candidate.path) -PathType Leaf)){continue}
    try{$policy=Read-BoundedJson ([string]$candidate.path) $MaxJsonBytes -Required}catch{$candidateStates+=@('standing_policy_invalid');continue}
    if(-not(Test-ControlPlanePropertySet $policy $candidate.fields)-or[int]$policy.schema_version-ne2-or$policy.enabled-ne$true-or[string]$policy.authority_mode-ne'standing'-or$null-ne$policy.expires_at_ms-or$null-eq$policy.facade_contract){$candidateStates+=@('standing_policy_invalid');continue}
    $policyOrigin=Get-ControlPlaneOrigin ([string]$policy.server_origin)
    if($null-eq$policyOrigin-or$policyOrigin-ne$origin-or[string]$policy.device_id-ne$deviceId-or[string]$policy.endpoint_id-ne$endpointId){$candidateStates+=@('policy_config_mismatch');continue}
    $workspaceState=Test-ControlPlaneWorkspaceRegistration $workspaceRegistryPath $policy
    if($workspaceState-ne'current'){$candidateStates+=@($workspaceState);continue}
    $eligiblePolicies+=1
  }
  if($eligiblePolicies -lt 1){
    # Heartbeat eligibility is deliberately independent from effect-lane
    # authority.  The connected agent sends one authenticated heartbeat first
    # and each file/patch/document/exec lane fails closed on its own policy
    # admission.  Starting in this mode never grants write or exec access.
    $reason='standing_policy_unavailable'
    if($candidateStates -contains 'workspace_registry_unavailable'){$reason='workspace_registry_unavailable'}
    elseif($candidateStates -contains 'workspace_registration_not_current'){$reason='workspace_registration_not_current'}
    elseif($candidateStates -contains 'policy_config_mismatch'){$reason='policy_config_mismatch'}
    return [pscustomobject]@{eligible=$true;heartbeat_only=$true;capability_state=$reason;state='heartbeat_only';pid=$null;python_path=$python;agent_path=$agent;config_path=$configPath;workspace_registry_path=$workspaceRegistryPath}
  }
  [pscustomobject]@{eligible=$true;heartbeat_only=$false;capability_state='standing_policy_ready';state='eligible';pid=$null;python_path=$python;agent_path=$agent;config_path=$configPath;workspace_registry_path=$workspaceRegistryPath}
}
function Get-ControlPlaneAgentArguments($M,$Spec) {
  $mode=[string](Get-OptionalProperty $M 'mode' '')
  if($mode-notin @('development','packaged')){throw 'Control-plane agent runtime mode is invalid.'}
  $node=[string](Get-OptionalProperty $Spec 'node_path' (Get-OptionalProperty $M 'control_plane_node_path' ''))
  if([string]::IsNullOrWhiteSpace($node)-or-not(Test-AbsoluteSafePath $node)-or-not(Test-Path -LiteralPath $node -PathType Leaf)){throw 'Control-plane node executable identity is unavailable.'}
  @('-I',[string]$Spec.agent_path,'run-connected-agent','--config',[string]$Spec.config_path,'--workspace-registry',[string]$Spec.workspace_registry_path,'--project-root',[string]$M.app_root,'--node',$node,'--runtime-mode',$mode)
}
function Start-ControlPlaneReadOnlyAgent($M,$Spec) {
  $args=Get-ControlPlaneAgentArguments $M $Spec|ForEach-Object{Quote-Fixed ([string]$_)}
  $psi=New-Object Diagnostics.ProcessStartInfo;$psi.FileName=[string]$Spec.python_path;$psi.Arguments=$args-join' ';$psi.WorkingDirectory=[string]$M.app_root;$psi.UseShellExecute=$false;$psi.CreateNoWindow=$true;$psi.WindowStyle=[Diagnostics.ProcessWindowStyle]::Hidden
  foreach($key in @($psi.EnvironmentVariables.Keys)){if([string]$key-match'^(OPENAI_API_KEY|ANTHROPIC_API_KEY|AZURE_OPENAI_API_KEY|.*(?:AUTHORIZATION|ACCESS_TOKEN|BEARER_TOKEN|PASSWORD|PASSWD|COOKIE|PRIVATE_KEY|SECRET_KEY|API_KEY|AUTH_TOKEN|MCP_AUTH_TOKEN|P5_A0_SEED).*)$'){$psi.EnvironmentVariables.Remove([string]$key)}}
  $psi.EnvironmentVariables.Remove('NODE_OPTIONS');$psi.EnvironmentVariables.Remove('NODE_EXTRA_CA_CERTS');$psi.EnvironmentVariables['WEBCODEX_PROCESS_ROLE']='control-plane-read-only-agent';$p=[Diagnostics.Process]::Start($psi);if($null-eq$p){throw 'Control-plane connected agent spawn failed.'};[int]$p.Id
}
function Invoke-ControlPlaneReadOnlyAgent($M,$State) {
  $spec=Get-ControlPlaneAgentSpec $M;if(-not$spec.eligible){$State.control_plane_agent_state=[string]$spec.state;$State.control_plane_agent_pid=$null;$State.control_plane_agent_last_error_code=$null;return $State}
  $heartbeatOnly=([bool](Get-OptionalProperty $spec 'heartbeat_only' $false));$existingPid=0;try{$existingPid=[int](Get-OptionalProperty $State 'control_plane_agent_pid' 0)}catch{};if(Test-ProcessAlive $existingPid){$State.control_plane_agent_state=if($heartbeatOnly){'running_heartbeat_only'}else{'running'};$State.control_plane_agent_last_error_code=$null;return $State}
  try{$State.control_plane_agent_pid=Start-ControlPlaneReadOnlyAgent $M $spec;$State.control_plane_agent_state=if($heartbeatOnly){'started_heartbeat_only'}else{'started'};$State.control_plane_agent_last_error_code=$null;$State.control_plane_agent_last_started_at=[DateTimeOffset]::UtcNow.ToString('o')}catch{$State.control_plane_agent_pid=$null;$State.control_plane_agent_state='spawn_failed';$State.control_plane_agent_last_error_code='CONTROL_PLANE_AGENT_START_FAILED'}
  $State
}
function New-State($M,[string]$StatePath){$old=$null;try{$old=Read-BoundedJson $StatePath $MaxJsonBytes}catch{};$manifestSha=Get-Sha256File (Get-ManifestPath);$oldManifestSha=[string](Get-OptionalProperty $old 'manifest_sha256' '');$reuseAgent=[string]::Equals($oldManifestSha,$manifestSha,[StringComparison]::OrdinalIgnoreCase);$oldAgentPid=if($reuseAgent){Get-OptionalProperty $old 'control_plane_agent_pid' $null}else{$null};$oldAgentState=if($reuseAgent){Get-OptionalProperty $old 'control_plane_agent_state' 'not_checked'}else{'not_checked'};$oldAgentStartedAt=if($reuseAgent){Get-OptionalProperty $old 'control_plane_agent_last_started_at' $null}else{$null};[ordered]@{version=1;supervisor_pid=$PID;supervisor_started_at=[DateTimeOffset]::UtcNow.ToString('o');state='starting';last_check_at=$null;last_healthy_at=(Get-OptionalProperty $old 'last_healthy_at' $null);last_host_pid=(Get-OptionalProperty $old 'last_host_pid' $null);last_host_instance_id=(Get-OptionalProperty $old 'last_host_instance_id' $null);consecutive_failures=[int](Get-OptionalProperty $old 'consecutive_failures' 0);restart_attempts=@((Get-OptionalProperty $old 'restart_attempts' $null));next_attempt_after=(Get-OptionalProperty $old 'next_attempt_after' $null);suppressed_until=(Get-OptionalProperty $old 'suppressed_until' $null);last_error_code=$null;last_error_message=$null;last_spawned_pid=$null;deferred_activation_worker_v1=$true;last_deferred_operation_id=(Get-OptionalProperty $old 'last_deferred_operation_id' $null);last_deferred_worker_pid=(Get-OptionalProperty $old 'last_deferred_worker_pid' $null);last_deferred_started_at=(Get-OptionalProperty $old 'last_deferred_started_at' $null);last_deferred_error_code=$null;last_deferred_error_message=$null;control_plane_agent_v1=$true;control_plane_agent_state=$oldAgentState;control_plane_agent_pid=$oldAgentPid;control_plane_agent_last_started_at=$oldAgentStartedAt;control_plane_agent_last_error_code=$null;manifest_sha256=$manifestSha;task_name=$TaskName}}
function Quote-Fixed([string]$V){if($V.Contains('"')-or$V.Contains("`r")-or$V.Contains("`n")){throw 'Unsafe fixed argument.'};if($V-match '\s'){'"'+$V+'"'}else{$V}}
function Start-RecoveryHostFixed($M){Assert-Manifest $M;if((Get-Sha256File ([string]$M.executable))-ne[string]$M.executable_sha256){throw 'Recovery Supervisor executable identity changed; reinstall is required.'};$psi=New-Object Diagnostics.ProcessStartInfo;$psi.FileName=[string]$M.executable;$psi.Arguments=(@($M.arguments)|ForEach-Object{Quote-Fixed ([string]$_)})-join' ';$psi.WorkingDirectory=[string]$M.app_root;$psi.UseShellExecute=$false;$psi.CreateNoWindow=$true;$psi.WindowStyle=[Diagnostics.ProcessWindowStyle]::Hidden;$psi.EnvironmentVariables['WEBCODEX_PROCESS_ROLE']='recovery-host';$p=[Diagnostics.Process]::Start($psi);if($null-eq$p){throw 'Fixed Recovery Host spawn failed.'};[int]$p.Id}
function Get-DeferredRequest($M,$File,[DateTimeOffset]$Now){if([string]$M.mode-ne'development'){throw 'Deferred activation supervisor queue is development-only.'};if($null-eq$File-or-not$File.Exists-or$File.Length-gt$MaxDeferredRequestBytes){throw 'Deferred activation request is unavailable or too large.'};$match=[regex]::Match([string]$File.Name,"^($DeferredOperationPattern)\.json$");if(-not$match.Success){throw 'Deferred activation request filename is invalid.'};$request=Read-BoundedJson ([string]$File.FullName) $MaxDeferredRequestBytes -Required;$operation=[string]$request.operation_id;if([int]$request.schema_version-ne 1-or[string]$request.kind-ne$DeferredRequestKind-or$operation-ne$match.Groups[1].Value){throw 'Deferred activation request identity is invalid.'};if([string]$request.runtime_mode-ne'development'-or-not(Test-PathEqual ([string]$request.app_root) ([string]$M.app_root))){throw 'Deferred activation request workspace is invalid.'};$sourceCheckpoint=Get-OptionalProperty $request 'source_checkpoint' $null;if($null-eq$sourceCheckpoint){throw 'Deferred activation request is not trusted recovery bootstrap work.'};$trustedBootstrap=Get-OptionalProperty $request 'trusted_recovery_bootstrap' $null;if($null-ne$trustedBootstrap -and $trustedBootstrap -isnot [PSCustomObject]){throw 'Deferred activation trusted recovery bootstrap is invalid.'};$requested=Convert-ToUtc ([DateTimeOffset]::FromUnixTimeMilliseconds([long]$request.requested_at_unix_ms));$expires=Convert-ToUtc ([DateTimeOffset]::FromUnixTimeMilliseconds([long]$request.expires_at_unix_ms));if($null-eq$requested-or$null-eq$expires-or$expires-le$requested-or($expires-$requested).TotalMinutes-gt 5-or$expires-le$Now-or$requested-gt$Now.AddSeconds(30)){throw 'Deferred activation request timing is invalid or expired.'};if([string]$request.integrity_sha256-notmatch'^[a-f0-9]{64}$'){throw 'Deferred activation request integrity identity is invalid.'};$expectedMarker=Join-Path ([string]$File.DirectoryName) "$operation.parent.json";if(-not(Test-PathEqual ([string]$request.parent_marker) $expectedMarker)){throw 'Deferred activation parent marker path is invalid.'};[pscustomobject]@{operation_id=$operation;request_path=[string]$File.FullName;request_sha256=[string]$request.integrity_sha256}}
function New-DeferredLaunchClaim($M,$Request,[DateTimeOffset]$Now){$queue=Join-Path ([string]$M.data_root) $DeferredDirectoryName;$target=Join-Path $queue "$([string]$Request.operation_id).supervisor.launch.json";$value=[ordered]@{schema_version=1;kind=$DeferredLaunchKind;operation_id=[string]$Request.operation_id;supervisor_pid=$PID;request_sha256=[string]$Request.request_sha256;created_at=$Now.ToString('o')};$json=($value|ConvertTo-Json -Compress);$stream=$null;try{$stream=[IO.File]::Open($target,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read);$bytes=[Text.Encoding]::UTF8.GetBytes($json);$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)}finally{if($null-ne$stream){$stream.Dispose()}};[pscustomobject]@{path=$target;value=$value}}
function Start-DeferredActivationWorker($M,$Request){Assert-Manifest $M;if([string]$M.mode-ne'development'){throw 'Deferred activation worker is development-only.'};if((Get-Sha256File ([string]$M.executable))-ne[string]$M.executable_sha256){throw 'Recovery Supervisor executable identity changed; reinstall is required.'};$worker=Join-Path ([string]$M.app_root) 'scripts\full-clean-activation.js';if(-not(Test-Path -LiteralPath $worker -PathType Leaf)){throw 'Deferred activation worker source is missing.'};$psi=New-Object Diagnostics.ProcessStartInfo;$psi.FileName=[string]$M.executable;$psi.Arguments=(@($worker,'--deferred-worker',[string]$Request.request_path)|ForEach-Object{Quote-Fixed ([string]$_)})-join' ';$psi.WorkingDirectory=[string]$M.app_root;$psi.UseShellExecute=$false;$psi.CreateNoWindow=$true;$psi.WindowStyle=[Diagnostics.ProcessWindowStyle]::Hidden;foreach($key in @($psi.EnvironmentVariables.Keys)){if([string]$key-match'^(OPENAI_API_KEY|ANTHROPIC_API_KEY|AZURE_OPENAI_API_KEY|.*(?:AUTHORIZATION|ACCESS_TOKEN|BEARER_TOKEN|PASSWORD|PASSWD|COOKIE|PRIVATE_KEY|SECRET_KEY|API_KEY|AUTH_TOKEN|MCP_AUTH_TOKEN|P5_A0_SEED).*)$'){$psi.EnvironmentVariables.Remove([string]$key)}};$psi.EnvironmentVariables.Remove('NODE_OPTIONS');$psi.EnvironmentVariables.Remove('NODE_EXTRA_CA_CERTS');$psi.EnvironmentVariables.Remove('FULL_CLEAN_SOURCE_CHECKPOINT_JSON');$psi.EnvironmentVariables['ELECTRON_RUN_AS_NODE']='1';$psi.EnvironmentVariables['FULL_CLEAN_DEFERRED_WORKER']='1';$p=[Diagnostics.Process]::Start($psi);if($null-eq$p){throw 'Deferred activation worker spawn failed.'};[int]$p.Id}
function Invoke-DeferredActivationQueue($M,$State){if([string]$M.mode-ne'development'){return $State};$queue=Join-Path ([string]$M.data_root) $DeferredDirectoryName;if(-not(Test-Path -LiteralPath $queue -PathType Container)){return $State};$now=[DateTimeOffset]::UtcNow;$files=@(Get-ChildItem -LiteralPath $queue -File -ErrorAction SilentlyContinue|Where-Object{$_.Name-match'^full-clean-cli-[A-Za-z0-9_-]{15,127}\.json$'}|Sort-Object CreationTimeUtc);foreach($file in $files){$operation=[IO.Path]::GetFileNameWithoutExtension([string]$file.Name);if(Test-Path -LiteralPath (Join-Path $queue "$operation.result.json")){continue};if(Test-Path -LiteralPath (Join-Path $queue "$operation.worker.lock.json")){continue};if(Test-Path -LiteralPath (Join-Path $queue "$operation.supervisor.launch.json")){continue};try{$request=Get-DeferredRequest $M $file $now;$claim=New-DeferredLaunchClaim $M $request $now;$workerPid=Start-DeferredActivationWorker $M $request;$State.last_deferred_operation_id=$operation;$State.last_deferred_worker_pid=$workerPid;$State.last_deferred_started_at=$now.ToString('o');$State.last_deferred_error_code=$null;$State.last_deferred_error_message=$null;return $State}catch{$State.last_deferred_operation_id=$operation;$State.last_deferred_worker_pid=$null;$State.last_deferred_started_at=$now.ToString('o');$State.last_deferred_error_code='DEFERRED_WORKER_START_FAILED';$State.last_deferred_error_message=[string]$_.Exception.Message;continue}};$State}
function Prune-Attempts($State,[DateTimeOffset]$Now){$cutoff=$Now.AddMinutes(-$RestartWindowMinutes);$State.restart_attempts=@($State.restart_attempts|Where-Object{$t=Convert-ToUtc $_;$null-ne$t-and$t-ge$cutoff})}
function Invoke-Cycle($M,[string]$StatePath,$State){$now=[DateTimeOffset]::UtcNow;$State=Invoke-DeferredActivationQueue $M $State;$State=Invoke-ControlPlaneReadOnlyAgent $M $State;$health=Invoke-RecoveryPing([string]$M.data_root);$lock=Get-LockStatus([string]$M.data_root);$State.last_check_at=$now.ToString('o');Prune-Attempts $State $now;if($health.healthy){$State.state='healthy';$State.consecutive_failures=0;$State.last_healthy_at=$now.ToString('o');$State.last_host_pid=[int]$health.owner_pid;$State.last_host_instance_id=[string]$health.instance_id;$State.next_attempt_after=$null;$State.suppressed_until=$null;$State.last_error_code=$null;$State.last_error_message=$null;Write-JsonAtomic $StatePath $State;return $State};$State.consecutive_failures=[int]$State.consecutive_failures+1;$State.last_error_code=[string]$health.code;$State.last_error_message='Recovery Host health check is not healthy.';if($health.owner_alive-or$lock.alive){$State.state='blocked_live_owner';$State.last_error_code='LIVE_OWNER_UNRESPONSIVE';$State.last_error_message='A Recovery Host owner is alive; supervisor will not kill or replace it.';Write-JsonAtomic $StatePath $State;return $State};$next=Convert-ToUtc $State.next_attempt_after;if($null-ne$next-and$now-lt$next){$State.state='starting';Write-JsonAtomic $StatePath $State;return $State};$sup=Convert-ToUtc $State.suppressed_until;if($null-ne$sup-and$now-lt$sup){$State.state='suppressed';Write-JsonAtomic $StatePath $State;return $State};if([int]$State.consecutive_failures-lt$FailureThreshold){$State.state='degraded';Write-JsonAtomic $StatePath $State;return $State};if(@($State.restart_attempts).Count-ge$RestartLimit){$State.state='suppressed';$State.suppressed_until=$now.AddMinutes($SuppressionMinutes).ToString('o');$State.last_error_code='CRASH_LOOP_SUPPRESSED';$State.last_error_message='Restart attempts exceeded bounded crash-loop limit.';Write-JsonAtomic $StatePath $State;return $State};try{$spawnedPid=Start-RecoveryHostFixed $M;$State.restart_attempts=@($State.restart_attempts)+@($now.ToString('o'));$State.last_spawned_pid=$spawnedPid;$State.next_attempt_after=$now.AddSeconds($StartupCooldownSeconds).ToString('o');$State.consecutive_failures=0;$State.state='restart_started';$State.last_error_code=$null;$State.last_error_message=$null}catch{$State.state='spawn_failed';$State.last_error_code='SPAWN_FAILED';$State.last_error_message=[string]$_.Exception.Message};Write-JsonAtomic $StatePath $State;$State}
function Get-Summary([string]$StatePath){$task=$null;try{$task=Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop}catch{};$status=$null;try{$status=Read-BoundedJson $StatePath $MaxJsonBytes}catch{};[ordered]@{version=1;installed=$null-ne$task;task_name=$TaskName;task_state=if($task){[string]$task.State}else{'NotInstalled'};status=$status}}
function Resolve-Inputs{$sourceRoot=Split-Path -Parent (Split-Path -Parent $PSScriptRoot);$root=if($AppRoot){[IO.Path]::GetFullPath($AppRoot)}else{[IO.Path]::GetFullPath($sourceRoot)};$exe=if($Executable){[IO.Path]::GetFullPath($Executable)}else{Join-Path $root 'node_modules\electron\dist\electron.exe'};if(-not(Test-AbsoluteSafePath $root)-or-not(Test-Path -LiteralPath $root -PathType Container)){throw 'Install app root invalid.'};if(-not(Test-AbsoluteSafePath $exe)-or-not(Test-Path -LiteralPath $exe -PathType Leaf)){throw 'Install executable invalid.'};[pscustomobject]@{app_root=$root;executable=[IO.Path]::GetFullPath($exe)}}
function Remove-LegacyInstallRoot{$legacy=Get-LegacyInstallRoot;$current=Get-InstallRoot;if(Test-PathEqual $legacy $current){return};try{Remove-Item -LiteralPath $legacy -Recurse -Force -ErrorAction SilentlyContinue}catch{}}
function Stop-InstalledSupervisorForReplacement([string]$StatePath){$stop=Get-StopRequest;Ensure-Parent $stop;Set-Content -LiteralPath $stop -Value ([DateTimeOffset]::UtcNow.ToString('o')) -Encoding Ascii;$legacyRoot=Get-LegacyInstallRoot;$legacyStop=Join-Path $legacyRoot 'stop.request';if((Test-Path -LiteralPath $legacyRoot -PathType Container)-and-not(Test-PathEqual $legacyStop $stop)){try{Set-Content -LiteralPath $legacyStop -Value ([DateTimeOffset]::UtcNow.ToString('o')) -Encoding Ascii -ErrorAction SilentlyContinue}catch{}};try{Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue}catch{};try{Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue}catch{};$old=$null;try{$old=Read-BoundedJson $StatePath $MaxJsonBytes}catch{};$oldPid=0;try{$oldPid=[int](Get-OptionalProperty $old 'supervisor_pid' 0)}catch{};$deadline=[DateTimeOffset]::UtcNow.AddSeconds($ReplacementStopTimeoutSeconds);while($oldPid-gt 0-and(Test-ProcessAlive $oldPid)-and[DateTimeOffset]::UtcNow-lt$deadline){Start-Sleep -Milliseconds 250};if($oldPid-gt 0-and(Test-ProcessAlive $oldPid)){throw "Existing Recovery Supervisor process $oldPid did not stop within the bounded replacement window."}}
function Wait-InstalledSupervisorReady([string]$StatePath,[string]$ManifestSha){$deadline=[DateTimeOffset]::UtcNow.AddSeconds($InstallReadyTimeoutSeconds);do{$summary=Get-Summary $StatePath;$status=$summary.status;$supervisorPid=0;try{$supervisorPid=[int](Get-OptionalProperty $status 'supervisor_pid' 0)}catch{};$checked=Convert-ToUtc (Get-OptionalProperty $status 'last_check_at' $null);$state=[string](Get-OptionalProperty $status 'state' '');$capability=Get-OptionalProperty $status 'deferred_activation_worker_v1' $false;$statusManifest=[string](Get-OptionalProperty $status 'manifest_sha256' '');if($summary.installed-and$capability-eq$true-and$supervisorPid-gt 0-and(Test-ProcessAlive $supervisorPid)-and$null-ne$checked-and[DateTimeOffset]::UtcNow.Subtract($checked).TotalSeconds-le20-and$state-notin@('stopping','uninstalled','duplicate_supervisor')-and$statusManifest-eq$ManifestSha){Remove-LegacyInstallRoot;return $summary};Start-Sleep -Milliseconds 250}while([DateTimeOffset]::UtcNow-lt$deadline);throw 'Replacement Recovery Supervisor did not publish a fresh capability-bearing heartbeat within the bounded install window.'}
function Stop-ControlPlaneAgentForReplacement($OldManifest,$OldState,$NewPaths,[string]$NewPythonSha256,[string]$NewAgentSha256,[string]$NewNodeSha256){$dataRoot=[string](Get-OptionalProperty $OldManifest 'data_root' (Get-DataRoot));$oldMode=[string](Get-OptionalProperty $OldManifest 'mode' '');$oldPython=[string](Get-OptionalProperty $OldManifest 'control_plane_python_path' '');$oldAgent=[string](Get-OptionalProperty $OldManifest 'control_plane_node_agent_path' '');$oldNode=[string](Get-OptionalProperty $OldManifest 'control_plane_node_path' '');$oldPythonSha=[string](Get-OptionalProperty $OldManifest 'control_plane_python_sha256' '');$oldAgentSha=[string](Get-OptionalProperty $OldManifest 'control_plane_node_agent_sha256' '');$oldNodeSha=[string](Get-OptionalProperty $OldManifest 'control_plane_node_sha256' '');$manifestChanged=($null-ne$OldManifest-and($oldMode-ne[string]$NewPaths.runtime_mode-or-not(Test-PathEqual $oldPython ([string]$NewPaths.python_path))-or-not(Test-PathEqual $oldAgent ([string]$NewPaths.agent_path))-or[string]::IsNullOrWhiteSpace($oldNode)-or-not(Test-PathEqual $oldNode ([string]$NewPaths.node_path))-or$oldPythonSha-ne$NewPythonSha256-or$oldAgentSha-ne$NewAgentSha256-or$oldNodeSha-ne$NewNodeSha256));$candidatePids=@();$statePid=0;try{$statePid=[int](Get-OptionalProperty $OldState 'control_plane_agent_pid' 0)}catch{};if($statePid-gt0){$candidatePids+=@($statePid)};$lockPath=Join-Path $dataRoot 'control-plane-node.json.connected-agent.lock';$lock=$null;try{$lock=Read-BoundedJson $lockPath $MaxJsonBytes}catch{};$lockPid=0;try{$lockPid=[int](Get-OptionalProperty $lock 'pid' 0)}catch{};if($lockPid-gt0){$candidatePids+=@($lockPid)};foreach($candidatePid in @($candidatePids|Select-Object -Unique)){if(-not(Test-ProcessAlive $candidatePid)){continue};$process=$null;try{$process=Get-Process -Id $candidatePid -ErrorAction Stop;$processPath=[string]$process.Path;$cim=Get-CimInstance Win32_Process -Filter "ProcessId=$candidatePid" -ErrorAction Stop;$commandLine=[string]$cim.CommandLine}catch{throw 'Existing control-plane agent identity could not be verified for replacement.'};$isAgent=($commandLine-match'(?i)node_agent\.py')-and($commandLine-match'(?i)run-connected-agent');if(-not$isAgent){throw 'Existing connected-agent lock owner is not a recognized node-agent process.'};$newModePattern='--runtime-mode\s+'+[regex]::Escape([string]$NewPaths.runtime_mode);$matchesNew=(Test-PathEqual $processPath ([string]$NewPaths.python_path))-and($commandLine.IndexOf([string]$NewPaths.agent_path,[StringComparison]::OrdinalIgnoreCase)-ge0)-and($commandLine.IndexOf([string]$NewPaths.node_path,[StringComparison]::OrdinalIgnoreCase)-ge0)-and($commandLine-match$newModePattern);if($matchesNew){continue};if(-not$manifestChanged-and$candidatePid-ne$lockPid){continue};try{$process.Kill();if(-not$process.WaitForExit(5000)){throw 'Existing control-plane agent did not stop within the bounded replacement window.'}}catch{throw [string]$_.Exception.Message}}}
function Install-Supervisor{$i=Resolve-Inputs;$mode=if($Packaged){'packaged'}else{'development'};$agentPaths=Get-ControlPlaneAgentPaths ([pscustomobject]@{mode=$mode;app_root=$i.app_root;executable=$i.executable});if($null-eq$agentPaths-or[string]::IsNullOrWhiteSpace([string]$agentPaths.node_path)-or-not(Test-Path -LiteralPath ([string]$agentPaths.node_path) -PathType Leaf)-or-not(Test-Path -LiteralPath ([string]$agentPaths.python_path) -PathType Leaf)-or-not(Test-Path -LiteralPath ([string]$agentPaths.agent_path) -PathType Leaf)){throw 'Control-plane agent resources or node runtime are missing.'};$newPythonSha=Get-Sha256File ([string]$agentPaths.python_path);$newAgentSha=Get-Sha256File ([string]$agentPaths.agent_path);$newNodeSha=Get-Sha256File ([string]$agentPaths.node_path);$oldManifest=$null;try{$oldManifest=Read-BoundedJson (Get-InstalledManifest) $MaxJsonBytes}catch{};$oldData=[IO.Path]::GetFullPath((Get-DataRoot));$oldState=$null;try{$oldState=Read-BoundedJson (Join-Path $oldData 'recovery-supervisor-status.json') $MaxJsonBytes}catch{};Stop-ControlPlaneAgentForReplacement $oldManifest $oldState $agentPaths $newPythonSha $newAgentSha $newNodeSha;$data=$oldData;$statePath=Join-Path $data 'recovery-supervisor-status.json';$install=Get-InstallRoot;Stop-InstalledSupervisorForReplacement $statePath;New-Item -ItemType Directory -Path $install -Force|Out-Null;New-Item -ItemType Directory -Path $data -Force|Out-Null;$dst=Get-InstalledScript;$src=[IO.Path]::GetFullPath($PSCommandPath);if(-not(Test-PathEqual $src $dst)){Copy-Item -LiteralPath $src -Destination $dst -Force};$launcherSrc=Get-SourceLauncher;$launcherDst=Get-InstalledLauncher;if(-not(Test-Path -LiteralPath $launcherSrc -PathType Leaf)){throw 'Recovery Supervisor GUI launcher is missing.'};if(-not(Test-PathEqual $launcherSrc $launcherDst)){Copy-Item -LiteralPath $launcherSrc -Destination $launcherDst -Force};$args=if($Packaged){@('--recovery-host')}else{@($i.app_root,'--recovery-host')};$m=[ordered]@{schema_version=1;mode=$mode;executable=$i.executable;executable_sha256=Get-Sha256File $i.executable;app_root=$i.app_root;arguments=$args;data_root=$data;installed_script_sha256=Get-Sha256File $dst;installed_launcher_sha256=Get-Sha256File $launcherDst;installed_at=[DateTimeOffset]::UtcNow.ToString('o')};$m.control_plane_python_path=[string]$agentPaths.python_path;$m.control_plane_python_sha256=$newPythonSha;$m.control_plane_node_agent_path=[string]$agentPaths.agent_path;$m.control_plane_node_agent_sha256=$newAgentSha;$m.control_plane_node_path=[string]$agentPaths.node_path;$m.control_plane_node_sha256=$newNodeSha;Assert-Manifest ([pscustomobject]$m);Write-JsonAtomic (Get-InstalledManifest) $m;$manifestSha=Get-Sha256File (Get-InstalledManifest);Remove-Item -LiteralPath (Get-StopRequest) -Force -ErrorAction SilentlyContinue;$identity=[Security.Principal.WindowsIdentity]::GetCurrent().Name;$powershell=Join-Path ([Environment]::GetFolderPath('System')) 'WindowsPowerShell\v1.0\powershell.exe';if(-not(Test-Path -LiteralPath $powershell -PathType Leaf)){throw 'Windows PowerShell executable is missing.'};$taskArgs="-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$dst`" -Action Run";$a=New-ScheduledTaskAction -Execute $powershell -Argument $taskArgs;$logon=New-ScheduledTaskTrigger -AtLogOn -User $identity;$heartbeat=New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 1) -RepetitionDuration (New-TimeSpan -Days 3650);$p=New-ScheduledTaskPrincipal -UserId $identity -LogonType Interactive -RunLevel Limited;$s=New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -StartWhenAvailable -ExecutionTimeLimit ([TimeSpan]::Zero);Register-ScheduledTask -TaskName $TaskName -Action $a -Trigger @($logon,$heartbeat) -Principal $p -Settings $s -Description 'Independent same-user Recovery Host and policy-gated control-plane agent supervisor for WebMCP.' -Force|Out-Null;Start-ScheduledTask -TaskName $TaskName;Wait-InstalledSupervisorReady $statePath $manifestSha}
function Uninstall-Supervisor{$m=$null;try{$m=Read-BoundedJson (Get-InstalledManifest) $MaxJsonBytes}catch{};$data=if($m-and(Test-AbsoluteSafePath ([string]$m.data_root))){[string]$m.data_root}else{Get-DataRoot};$state=Join-Path $data 'recovery-supervisor-status.json';Ensure-Parent (Get-StopRequest);Set-Content -LiteralPath (Get-StopRequest) -Value ([DateTimeOffset]::UtcNow.ToString('o')) -Encoding Ascii;try{Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue}catch{};try{Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue}catch{};Write-JsonAtomic $state ([ordered]@{version=1;supervisor_pid=$null;state='uninstalled';last_check_at=[DateTimeOffset]::UtcNow.ToString('o');task_name=$TaskName});Start-Sleep -Milliseconds 250;try{Remove-Item -LiteralPath (Get-InstallRoot) -Recurse -Force -ErrorAction SilentlyContinue}catch{};Remove-LegacyInstallRoot;Get-Summary $state}
function Run-Supervisor([switch]$Single){$mp=Get-ManifestPath;$m=Read-BoundedJson $mp $MaxJsonBytes -Required;Assert-Manifest $m;$statePath=Get-StatePath $m;$state=New-State $m $statePath;$mutexName='Local\WebMcpRecoverySupervisor-'+(Get-Sha256Text ([string]$m.data_root)).Substring(0,20);$mutex=New-Object System.Threading.Mutex($false,$mutexName);$owned=$false;try{try{$owned=$mutex.WaitOne(0)}catch [System.Threading.AbandonedMutexException]{$owned=$true};if(-not$owned){$state.state='duplicate_supervisor';$state.last_error_code='SUPERVISOR_ALREADY_RUNNING';Write-JsonAtomic $statePath $state;return $state};do{if(Test-Path -LiteralPath (Get-StopRequest)){$state.state='stopping';Write-JsonAtomic $statePath $state;break};try{$state=Invoke-Cycle $m $statePath $state}catch{$state.state='cycle_error';$state.last_check_at=[DateTimeOffset]::UtcNow.ToString('o');$state.last_error_code='SUPERVISOR_CYCLE_FAILED';$state.last_error_message='Recovery Supervisor cycle failed; retrying on the next bounded poll.';try{Write-JsonAtomic $statePath $state}catch{}};if($Single){break};Start-Sleep -Seconds $PollSeconds}while($true);$state}finally{if($owned){try{$mutex.ReleaseMutex()}catch{}};$mutex.Dispose()}}

try{switch($Action){'Install'{Install-Supervisor|ConvertTo-Json -Depth 8 -Compress;exit 0};'Uninstall'{Uninstall-Supervisor|ConvertTo-Json -Depth 8 -Compress;exit 0};'Status'{$m=$null;try{$m=Read-BoundedJson (Get-InstalledManifest) $MaxJsonBytes}catch{};$data=if($m-and(Test-AbsoluteSafePath ([string]$m.data_root))){[string]$m.data_root}else{Get-DataRoot};Get-Summary (Join-Path $data 'recovery-supervisor-status.json')|ConvertTo-Json -Depth 8 -Compress;exit 0};'Once'{Run-Supervisor -Single|ConvertTo-Json -Depth 8 -Compress;exit 0};'Run'{Run-Supervisor|Out-Null;exit 0}}}catch{[ordered]@{ok=$false;action=$Action;code='RECOVERY_SUPERVISOR_FAILED';message=[string]$_.Exception.Message}|ConvertTo-Json -Compress;exit 1}

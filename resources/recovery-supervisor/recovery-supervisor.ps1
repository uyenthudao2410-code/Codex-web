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

function Get-DataRoot { Join-Path ([Environment]::GetFolderPath('ApplicationData')) 'web-mcp-assistant' }
function Get-InstallRoot { Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'WebMcpRecoverySupervisor' }
function Get-InstalledScript { Join-Path (Get-InstallRoot) 'recovery-supervisor.ps1' }
function Get-InstalledManifest { Join-Path (Get-InstallRoot) 'manifest.json' }
function Get-StopRequest { Join-Path (Get-InstallRoot) 'stop.request' }
function Get-Sha256File([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
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
function Get-OptionalProperty($Object,[string]$Name,$Default){if($null-eq$Object){return $Default};$property=$Object.PSObject.Properties[$Name];if($null-eq$property){return $Default};$property.Value}
function New-State($M,[string]$StatePath){$old=$null;try{$old=Read-BoundedJson $StatePath $MaxJsonBytes}catch{};[ordered]@{version=1;supervisor_pid=$PID;supervisor_started_at=[DateTimeOffset]::UtcNow.ToString('o');state='starting';last_check_at=$null;last_healthy_at=(Get-OptionalProperty $old 'last_healthy_at' $null);last_host_pid=(Get-OptionalProperty $old 'last_host_pid' $null);last_host_instance_id=(Get-OptionalProperty $old 'last_host_instance_id' $null);consecutive_failures=[int](Get-OptionalProperty $old 'consecutive_failures' 0);restart_attempts=@((Get-OptionalProperty $old 'restart_attempts' $null));next_attempt_after=(Get-OptionalProperty $old 'next_attempt_after' $null);suppressed_until=(Get-OptionalProperty $old 'suppressed_until' $null);last_error_code=$null;last_error_message=$null;last_spawned_pid=$null;manifest_sha256=Get-Sha256File (Get-ManifestPath);task_name=$TaskName}}
function Quote-Fixed([string]$V){if($V.Contains('"')-or$V.Contains("`r")-or$V.Contains("`n")){throw 'Unsafe fixed argument.'};if($V-match '\s'){'"'+$V+'"'}else{$V}}
function Start-RecoveryHostFixed($M){Assert-Manifest $M;if((Get-Sha256File ([string]$M.executable))-ne[string]$M.executable_sha256){throw 'Recovery Supervisor executable identity changed; reinstall is required.'};$psi=New-Object Diagnostics.ProcessStartInfo;$psi.FileName=[string]$M.executable;$psi.Arguments=(@($M.arguments)|ForEach-Object{Quote-Fixed ([string]$_)})-join' ';$psi.WorkingDirectory=[string]$M.app_root;$psi.UseShellExecute=$false;$psi.CreateNoWindow=$true;$psi.WindowStyle=[Diagnostics.ProcessWindowStyle]::Hidden;$psi.EnvironmentVariables['WEBCODEX_PROCESS_ROLE']='recovery-host';$p=[Diagnostics.Process]::Start($psi);if($null-eq$p){throw 'Fixed Recovery Host spawn failed.'};[int]$p.Id}
function Prune-Attempts($State,[DateTimeOffset]$Now){$cutoff=$Now.AddMinutes(-$RestartWindowMinutes);$State.restart_attempts=@($State.restart_attempts|Where-Object{$t=Convert-ToUtc $_;$null-ne$t-and$t-ge$cutoff})}
function Invoke-Cycle($M,[string]$StatePath,$State){$now=[DateTimeOffset]::UtcNow;$health=Invoke-RecoveryPing([string]$M.data_root);$lock=Get-LockStatus([string]$M.data_root);$State.last_check_at=$now.ToString('o');Prune-Attempts $State $now;if($health.healthy){$State.state='healthy';$State.consecutive_failures=0;$State.last_healthy_at=$now.ToString('o');$State.last_host_pid=[int]$health.owner_pid;$State.last_host_instance_id=[string]$health.instance_id;$State.next_attempt_after=$null;$State.suppressed_until=$null;$State.last_error_code=$null;$State.last_error_message=$null;Write-JsonAtomic $StatePath $State;return $State};$State.consecutive_failures=[int]$State.consecutive_failures+1;$State.last_error_code=[string]$health.code;$State.last_error_message='Recovery Host health check is not healthy.';if($health.owner_alive-or$lock.alive){$State.state='blocked_live_owner';$State.last_error_code='LIVE_OWNER_UNRESPONSIVE';$State.last_error_message='A Recovery Host owner is alive; supervisor will not kill or replace it.';Write-JsonAtomic $StatePath $State;return $State};$next=Convert-ToUtc $State.next_attempt_after;if($null-ne$next-and$now-lt$next){$State.state='starting';Write-JsonAtomic $StatePath $State;return $State};$sup=Convert-ToUtc $State.suppressed_until;if($null-ne$sup-and$now-lt$sup){$State.state='suppressed';Write-JsonAtomic $StatePath $State;return $State};if([int]$State.consecutive_failures-lt$FailureThreshold){$State.state='degraded';Write-JsonAtomic $StatePath $State;return $State};if(@($State.restart_attempts).Count-ge$RestartLimit){$State.state='suppressed';$State.suppressed_until=$now.AddMinutes($SuppressionMinutes).ToString('o');$State.last_error_code='CRASH_LOOP_SUPPRESSED';$State.last_error_message='Restart attempts exceeded bounded crash-loop limit.';Write-JsonAtomic $StatePath $State;return $State};try{$spawnedPid=Start-RecoveryHostFixed $M;$State.restart_attempts=@($State.restart_attempts)+@($now.ToString('o'));$State.last_spawned_pid=$spawnedPid;$State.next_attempt_after=$now.AddSeconds($StartupCooldownSeconds).ToString('o');$State.consecutive_failures=0;$State.state='restart_started';$State.last_error_code=$null;$State.last_error_message=$null}catch{$State.state='spawn_failed';$State.last_error_code='SPAWN_FAILED';$State.last_error_message=[string]$_.Exception.Message};Write-JsonAtomic $StatePath $State;$State}
function Get-Summary([string]$StatePath){$task=$null;try{$task=Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop}catch{};$status=$null;try{$status=Read-BoundedJson $StatePath $MaxJsonBytes}catch{};[ordered]@{version=1;installed=$null-ne$task;task_name=$TaskName;task_state=if($task){[string]$task.State}else{'NotInstalled'};status=$status}}
function Resolve-Inputs{$sourceRoot=Split-Path -Parent (Split-Path -Parent $PSScriptRoot);$root=if($AppRoot){[IO.Path]::GetFullPath($AppRoot)}else{[IO.Path]::GetFullPath($sourceRoot)};$exe=if($Executable){[IO.Path]::GetFullPath($Executable)}else{Join-Path $root 'node_modules\electron\dist\electron.exe'};if(-not(Test-AbsoluteSafePath $root)-or-not(Test-Path -LiteralPath $root -PathType Container)){throw 'Install app root invalid.'};if(-not(Test-AbsoluteSafePath $exe)-or-not(Test-Path -LiteralPath $exe -PathType Leaf)){throw 'Install executable invalid.'};[pscustomobject]@{app_root=$root;executable=[IO.Path]::GetFullPath($exe)}}
function Install-Supervisor{$i=Resolve-Inputs;$data=[IO.Path]::GetFullPath((Get-DataRoot));$install=Get-InstallRoot;New-Item -ItemType Directory -Path $install -Force|Out-Null;New-Item -ItemType Directory -Path $data -Force|Out-Null;$dst=Get-InstalledScript;$src=[IO.Path]::GetFullPath($PSCommandPath);if(-not(Test-PathEqual $src $dst)){Copy-Item -LiteralPath $src -Destination $dst -Force};$mode=if($Packaged){'packaged'}else{'development'};$args=if($Packaged){@('--recovery-host')}else{@($i.app_root,'--recovery-host')};$m=[ordered]@{schema_version=1;mode=$mode;executable=$i.executable;executable_sha256=Get-Sha256File $i.executable;app_root=$i.app_root;arguments=$args;data_root=$data;installed_script_sha256=Get-Sha256File $dst;installed_at=[DateTimeOffset]::UtcNow.ToString('o')};Assert-Manifest ([pscustomobject]$m);Write-JsonAtomic (Get-InstalledManifest) $m;Remove-Item -LiteralPath (Get-StopRequest) -Force -ErrorAction SilentlyContinue;$identity=[Security.Principal.WindowsIdentity]::GetCurrent().Name;$ps=Join-Path $PSHOME 'powershell.exe';$taskArgs="-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$dst`" -Action Run";$a=New-ScheduledTaskAction -Execute $ps -Argument $taskArgs;$logon=New-ScheduledTaskTrigger -AtLogOn -User $identity;$heartbeat=New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 1) -RepetitionDuration (New-TimeSpan -Days 3650);$p=New-ScheduledTaskPrincipal -UserId $identity -LogonType Interactive -RunLevel Limited;$s=New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -StartWhenAvailable -ExecutionTimeLimit ([TimeSpan]::Zero);Register-ScheduledTask -TaskName $TaskName -Action $a -Trigger @($logon,$heartbeat) -Principal $p -Settings $s -Description 'Independent same-user Recovery Host resurrection supervisor for WebMCP.' -Force|Out-Null;Start-ScheduledTask -TaskName $TaskName;Start-Sleep -Milliseconds 750;Get-Summary (Join-Path $data 'recovery-supervisor-status.json')}
function Uninstall-Supervisor{$m=$null;try{$m=Read-BoundedJson (Get-InstalledManifest) $MaxJsonBytes}catch{};$data=if($m-and(Test-AbsoluteSafePath ([string]$m.data_root))){[string]$m.data_root}else{Get-DataRoot};$state=Join-Path $data 'recovery-supervisor-status.json';Ensure-Parent (Get-StopRequest);Set-Content -LiteralPath (Get-StopRequest) -Value ([DateTimeOffset]::UtcNow.ToString('o')) -Encoding Ascii;try{Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue}catch{};try{Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue}catch{};Write-JsonAtomic $state ([ordered]@{version=1;supervisor_pid=$null;state='uninstalled';last_check_at=[DateTimeOffset]::UtcNow.ToString('o');task_name=$TaskName});Start-Sleep -Milliseconds 250;try{Remove-Item -LiteralPath (Get-InstallRoot) -Recurse -Force -ErrorAction SilentlyContinue}catch{};Get-Summary $state}
function Run-Supervisor([switch]$Single){$mp=Get-ManifestPath;$m=Read-BoundedJson $mp $MaxJsonBytes -Required;Assert-Manifest $m;$statePath=Get-StatePath $m;$state=New-State $m $statePath;$mutexName='Local\WebMcpRecoverySupervisor-'+(Get-Sha256Text ([string]$m.data_root)).Substring(0,20);$mutex=New-Object System.Threading.Mutex($false,$mutexName);$owned=$false;try{try{$owned=$mutex.WaitOne(0)}catch [System.Threading.AbandonedMutexException]{$owned=$true};if(-not$owned){$state.state='duplicate_supervisor';$state.last_error_code='SUPERVISOR_ALREADY_RUNNING';Write-JsonAtomic $statePath $state;return $state};do{if(Test-Path -LiteralPath (Get-StopRequest)){$state.state='stopping';Write-JsonAtomic $statePath $state;break};try{$state=Invoke-Cycle $m $statePath $state}catch{$state.state='cycle_error';$state.last_check_at=[DateTimeOffset]::UtcNow.ToString('o');$state.last_error_code='SUPERVISOR_CYCLE_FAILED';$state.last_error_message='Recovery Supervisor cycle failed; retrying on the next bounded poll.';try{Write-JsonAtomic $statePath $state}catch{}};if($Single){break};Start-Sleep -Seconds $PollSeconds}while($true);$state}finally{if($owned){try{$mutex.ReleaseMutex()}catch{}};$mutex.Dispose()}}

try{switch($Action){'Install'{Install-Supervisor|ConvertTo-Json -Depth 8 -Compress;exit 0};'Uninstall'{Uninstall-Supervisor|ConvertTo-Json -Depth 8 -Compress;exit 0};'Status'{$m=$null;try{$m=Read-BoundedJson (Get-InstalledManifest) $MaxJsonBytes}catch{};$data=if($m-and(Test-AbsoluteSafePath ([string]$m.data_root))){[string]$m.data_root}else{Get-DataRoot};Get-Summary (Join-Path $data 'recovery-supervisor-status.json')|ConvertTo-Json -Depth 8 -Compress;exit 0};'Once'{Run-Supervisor -Single|ConvertTo-Json -Depth 8 -Compress;exit 0};'Run'{Run-Supervisor|Out-Null;exit 0}}}catch{[ordered]@{ok=$false;action=$Action;code='RECOVERY_SUPERVISOR_FAILED';message=[string]$_.Exception.Message}|ConvertTo-Json -Compress;exit 1}

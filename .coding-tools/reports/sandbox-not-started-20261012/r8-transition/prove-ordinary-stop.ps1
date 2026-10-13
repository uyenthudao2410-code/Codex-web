$ErrorActionPreference='Stop'
$id=[guid]::NewGuid().ToString('N')
$server=Join-Path $PSScriptRoot ('server-before-ordinary-stop-'+$id+'.json')
Get-Content -LiteralPath 'E:\DEV\Codex-web\.coding-tools\reports\shared-write-exec-20261012\inspect-final-server-surface.py' -Raw|ssh.exe -T -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=yes svhome@100.116.112.22 python3 -B -|Set-Content -LiteralPath $server -Encoding utf8
if($LASTEXITCODE){throw 'SERVER_CENSUS_UNAVAILABLE'}
$s=Get-Content -LiteralPath $server -Raw|ConvertFrom-Json
if($s.current_generation_census.open_tasks -ne 0 -or $s.current_generation_census.unreleased_writers -ne 0 -or $s.current_generation_census.unsettled_current_generation_actions -ne 0){throw 'CENTRAL_WORK_PREVENTS_STOP'}
$base=Join-Path $env:TEMP 'wxc-wsb/state-aware'
$daemonPath=Join-Path $base 'daemon.json'
$d=Get-Content -LiteralPath $daemonPath -Raw|ConvertFrom-Json
if($d.active_sandbox_id -notmatch '^wsb:([a-f0-9]{8})$' -or $d.ready -ne $true -or -not(Get-Process -Id $d.pid -ErrorAction SilentlyContinue)){throw 'LIVE_READY_CACHED_SANDBOX_REQUIRED'}
$token=$Matches[1]
$recordPath=Join-Path $base ($token+'/record.json')
$r=Get-Content -LiteralPath $recordPath -Raw|ConvertFrom-Json
$writable=@($r.mapped_folders|Where-Object read_only -eq $false)
if($r.sandbox_id -ne $d.active_sandbox_id -or $r.state -ne 'started' -or $writable.Count -ne 1 -or $writable[0].host -ne 'E:\DEV\Codex-web'){throw 'EXACT_CURRENT_WORKSPACE_REQUIRED'}
$before=@{sandbox_id=$d.active_sandbox_id;daemon_pid=$d.pid;daemon_start_token=[string]$d.pid_creation_time;daemon_record_sha256=(Get-FileHash -LiteralPath $daemonPath -Algorithm SHA256).Hash.ToLowerInvariant();sandbox_record_sha256=(Get-FileHash -LiteralPath $recordPath -Algorithm SHA256).Hash.ToLowerInvariant();central_census=$s.current_generation_census}
$before|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $PSScriptRoot ('ordinary-stop-before-'+$id+'.json')) -Encoding utf8
& (Join-Path $PSScriptRoot 'invoke-packaged.ps1') -Operation stop *> (Join-Path $PSScriptRoot ('ordinary-stop-console-'+$id+'.txt'))
$exitCode=$LASTEXITCODE
$hosts=@(Get-Process -Name 'WindowsSandbox*','wxc-windows-sandbox-daemon' -ErrorAction SilentlyContinue|Select-Object Id,ProcessName)
$daemonGone=-not(Test-Path -LiteralPath $daemonPath)
$recordGone=-not(Test-Path -LiteralPath $recordPath)
$kernel=@(Get-Process -Name 'vmmemWindowsSandbox' -ErrorAction SilentlyContinue|Select-Object Id,ProcessName)
$confirmed=$exitCode -eq 0 -and $hosts.Count -eq 0 -and $daemonGone -and $recordGone
$report=@{operation='r8_live_cached_sandbox_ordinary_stop_proof';observed_at=(Get-Date -Format o);ok=$confirmed;before=$before;stop_process_exit=$exitCode;remaining_user_hosts=$hosts;daemon_record_absent=$daemonGone;sandbox_record_absent=$recordGone;kernel_aggregates=$kernel;kernel_ownership_inferred=$false;manual_kill=$false;canonical_manual_edit=$false}
$report|ConvertTo-Json -Depth 7|Set-Content -LiteralPath (Join-Path $PSScriptRoot ('ordinary-stop-proof-'+$id+'.json')) -Encoding utf8
$report|ConvertTo-Json -Depth 7 -Compress
if(-not $confirmed){throw 'ORDINARY_STOP_PROOF_INCOMPLETE'}

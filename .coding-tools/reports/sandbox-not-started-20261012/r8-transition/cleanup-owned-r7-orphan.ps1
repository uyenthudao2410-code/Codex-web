$ErrorActionPreference='Stop'
$candidate='E:\DEV\Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-machine-exec-lifecycle-1012-r8\win-unpacked'
$backend=Join-Path $candidate 'resources/resources/tools/mxc-windows-sandbox/wxc-exec.exe'
if((Get-FileHash -LiteralPath $backend -Algorithm SHA256).Hash.ToLowerInvariant() -ne '0ab60f0d5ed3ae87870536173335eea9f9cb469bae737ad6656695855232c4d3'){throw 'VERIFIED_BACKEND_REQUIRED'}
$base=Join-Path $env:TEMP 'wxc-wsb/state-aware'
$daemonPath=Join-Path $base 'daemon.json'
$recordPath=Join-Path $base '6973cf0f/record.json'
$daemon=Get-Content -LiteralPath $daemonPath -Raw|ConvertFrom-Json
$record=Get-Content -LiteralPath $recordPath -Raw|ConvertFrom-Json
$daemonHash=(Get-FileHash -LiteralPath $daemonPath -Algorithm SHA256).Hash
$recordHash=(Get-FileHash -LiteralPath $recordPath -Algorithm SHA256).Hash
$writable=@($record.mapped_folders|Where-Object read_only -eq $false)
if($daemon.active_sandbox_id -ne 'wsb:6973cf0f' -or $daemon.pid -ne 27616 -or $record.sandbox_id -ne 'wsb:6973cf0f' -or $writable.Count -ne 1 -or $writable[0].host -ne 'E:\DEV\Codex-web'){throw 'EXACT_R7_OWNED_MAPPING_REQUIRED'}
if(Get-Process -Id 27616 -ErrorAction SilentlyContinue){throw 'LIVE_OR_REUSED_DAEMON_PID'}
if(@(Get-Process -Name 'WindowsSandbox*','wxc-windows-sandbox-daemon' -ErrorAction SilentlyContinue).Count){throw 'LIVE_SANDBOX_OWNER_REQUIRES_REVIEW'}
$prior=Get-Content -LiteralPath 'E:\DEV\Codex-web\.coding-tools\reports\shared-write-exec-20261012-r7\shared-write-exec-receipt-r7-85d25996125b484fbb8ef1934846ca0b.ndjson' -Tail 1|ConvertFrom-Json
if($prior.ok -ne $true -or $prior.proofs.exec.receipt.job_id -ne 'd618111e6a4e4e9484a48c76121ef259' -or $prior.task_closed_verified -ne $true -or $prior.writer_released_verified -ne $true){throw 'ORIGINAL_R7_JOB_PROOF_REQUIRED'}
if((Get-FileHash -LiteralPath $daemonPath -Algorithm SHA256).Hash -ne $daemonHash -or (Get-FileHash -LiteralPath $recordPath -Algorithm SHA256).Hash -ne $recordHash){throw 'ORPHAN_RECORD_CHANGED'}
$id=[guid]::NewGuid().ToString('N')
$reportPath=Join-Path $PSScriptRoot ('r7-owned-orphan-cleanup-'+$id+'.json')
$config=@{version='0.10.0-alpha';phase='deprovision';sandboxId='wsb:6973cf0f'}|ConvertTo-Json -Compress
$encoded=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($config))
$out=Join-Path $PSScriptRoot ('orphan-cleanup-'+$id+'.stdout.json')
$err=Join-Path $PSScriptRoot ('orphan-cleanup-'+$id+'.stderr.txt')
$p=Start-Process -FilePath $backend -ArgumentList @('--experimental','--config-base64',$encoded) -WorkingDirectory (Join-Path $candidate 'resources/resources') -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $out -RedirectStandardError $err
$result=Get-Content -LiteralPath $out -Raw|ConvertFrom-Json
$confirmed=$p.ExitCode -eq 0 -and $null -ne $result.result -and -not(Test-Path -LiteralPath $daemonPath) -and -not(Test-Path -LiteralPath $recordPath)
$report=@{operation='supported_exact_r7_orphan_deprovision';observed_at=(Get-Date -Format o);ok=$confirmed;sandbox_id='wsb:6973cf0f';prior_daemon_pid=27616;prior_daemon_absent=$true;user_hosts_absent=$true;original_r7_job='d618111e6a4e4e9484a48c76121ef259';daemon_record_sha256=$daemonHash.ToLowerInvariant();sandbox_record_sha256=$recordHash.ToLowerInvariant();supported_result=$result;exit_code=$p.ExitCode;manual_state_edit=$false;nonce_saved=$false;report_path=$reportPath}
$report|ConvertTo-Json -Depth 6|Set-Content -LiteralPath $reportPath -Encoding utf8
$report|ConvertTo-Json -Depth 6 -Compress
if(-not $confirmed){throw 'SUPPORTED_ORPHAN_CLEANUP_UNCONFIRMED'}

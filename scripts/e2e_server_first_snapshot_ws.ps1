param([switch]$SyntaxOnly)

# Real-process, loopback-only acceptance for Server-First dirty SourceSnapshot
# validation on Windows. Build current debug server/runner binaries before running.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Assert-Canary([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw $Message }
}

function Invoke-Git([string]$Cwd, [string[]]$GitArgs) {
    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $output = & git -C $Cwd @GitArgs 2>&1
        $gitExitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    if ($gitExitCode -ne 0) { throw "git $($GitArgs -join ' ') failed: $($output -join [Environment]::NewLine)" }
    return ($output -join [Environment]::NewLine).Trim()
}

function Write-Utf8NoBom([string]$Path, [string]$Content) {
    [IO.File]::WriteAllText($Path, $Content, [Text.UTF8Encoding]::new($false))
}

function Normalize-Path([string]$Path) {
    return ([IO.Path]::GetFullPath($Path)).TrimEnd('\','/').Replace('\','/').ToLowerInvariant()
}

function Find-FreePort {
    $listener = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, 0)
    $listener.Start()
    try { return ([Net.IPEndPoint]$listener.LocalEndpoint).Port }
    finally { $listener.Stop() }
}

function Wait-Port([int]$Port, [int]$Seconds) {
    $deadline = [DateTime]::UtcNow.AddSeconds($Seconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        $client = [Net.Sockets.TcpClient]::new()
        try {
            $task = $client.ConnectAsync('127.0.0.1', $Port)
            if ($task.Wait(500) -and $client.Connected) { return $true }
        } catch {} finally { $client.Dispose() }
        Start-Sleep -Milliseconds 250
    }
    return $false
}

if ($SyntaxOnly) {
    Write-Host 'CANARY_SYNTAX_OK'
    exit 0
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$repoHead = Invoke-Git $repoRoot @('rev-parse','HEAD')
Assert-Canary ($repoHead -match '^[0-9a-f]{40}$') "unexpected repository HEAD: $repoHead"
$headPrefix = $repoHead.Substring(0, 12)
$serverBin = Join-Path $repoRoot 'target\debug\webcodex-server.exe'
$runnerBin = Join-Path $repoRoot 'target\debug\webcodex-runner.exe'
Assert-Canary (Test-Path $serverBin) 'current server binary is missing; build webcodex-server first'
Assert-Canary (Test-Path $runnerBin) 'current runner binary is missing; build webcodex-runner first'
$serverVersion = (& $serverBin --version 2>&1 | Out-String).Trim()
Assert-Canary ($LASTEXITCODE -eq 0) 'webcodex-server --version failed'
$runnerVersion = (& $runnerBin --version 2>&1 | Out-String).Trim()
Assert-Canary ($LASTEXITCODE -eq 0) 'webcodex-runner --version failed'
Assert-Canary ($serverVersion.Contains("commit $headPrefix")) ("stale server binary: $serverVersion")
Assert-Canary ($runnerVersion.Contains("commit $headPrefix")) ("stale runner binary: $runnerVersion")

$port = Find-FreePort
$token = 'local-canary-' + [Guid]::NewGuid().ToString('N')
$tempRoot = Join-Path ([IO.Path]::GetTempPath()) ('webcodex-server-first-canary-' + [Guid]::NewGuid().ToString('N'))
$baseRepo = Join-Path $tempRoot 'base'
$sourceRepo = Join-Path $tempRoot 'source'
$computeRepo = Join-Path $tempRoot 'compute'
$sourceProjects = Join-Path $tempRoot 'source-projects.d'
$computeProjects = Join-Path $tempRoot 'compute-projects.d'
$dataDir = Join-Path $tempRoot 'data'
$marker = Join-Path $tempRoot 'manifest-dir.txt'
$serverOut = Join-Path $tempRoot 'server.out.log'
$serverErr = Join-Path $tempRoot 'server.err.log'
$sourceOut = Join-Path $tempRoot 'source.out.log'
$sourceErr = Join-Path $tempRoot 'source.err.log'
$computeOut = Join-Path $tempRoot 'compute.out.log'
$computeErr = Join-Path $tempRoot 'compute.err.log'
$sourceToml = Join-Path $tempRoot 'source-agent.toml'
$computeToml = Join-Path $tempRoot 'compute-agent.toml'
$server = $null
$sourceRunner = $null
$computeRunner = $null
$failed = $false

function Invoke-ApiPost([string]$Path, [object]$Body, [int]$TimeoutSec = 15) {
    $json = $Body | ConvertTo-Json -Depth 30 -Compress
    return Invoke-RestMethod -Method Post -Uri ("http://127.0.0.1:$port$Path") -Headers @{ Authorization = "Bearer $token" } -ContentType 'application/json' -Body $json -TimeoutSec $TimeoutSec
}

function Get-Client([object]$Status, [string]$ClientId) {
    return @($Status.output.agents.clients | Where-Object { $_.client_id -eq $ClientId }) | Select-Object -First 1
}

function Stop-Tree($Process) {
    if ($null -eq $Process) { return }
    try {
        if (-not $Process.HasExited) { & taskkill.exe /PID $Process.Id /T /F 2>$null | Out-Null }
    } catch {}
}

try {
    New-Item -ItemType Directory -Force -Path $baseRepo, (Join-Path $baseRepo 'src'), $sourceProjects, $computeProjects, $dataDir | Out-Null
    Write-Utf8NoBom (Join-Path $baseRepo 'Cargo.toml') "[package]`nname = `"server-first-canary`"`nversion = `"0.1.0`"`nedition = `"2021`"`n"
    Write-Utf8NoBom (Join-Path $baseRepo '.gitignore') "target/`n"
    Write-Utf8NoBom (Join-Path $baseRepo 'src\lib.rs') "pub fn value() -> u8 { base_source_does_not_compile }`n"
    & git -C $baseRepo init -b main | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'git init failed' }
    Invoke-Git $baseRepo @('config','user.email','server-first-canary@example.invalid') | Out-Null
    Invoke-Git $baseRepo @('config','user.name','Server First Canary') | Out-Null
    & cargo generate-lockfile --quiet --manifest-path (Join-Path $baseRepo 'Cargo.toml')
    if ($LASTEXITCODE -ne 0) { throw 'cargo generate-lockfile failed' }
    Invoke-Git $baseRepo @('add','.') | Out-Null
    Invoke-Git $baseRepo @('commit','-q','-m','base') | Out-Null
    $baseHead = Invoke-Git $baseRepo @('rev-parse','HEAD')
    Assert-Canary ($baseHead -match '^[0-9a-f]{40}$') "unexpected base HEAD: $baseHead"

    & git clone -q $baseRepo $sourceRepo
    if ($LASTEXITCODE -ne 0) { throw 'source clone failed' }
    & git clone -q $baseRepo $computeRepo
    if ($LASTEXITCODE -ne 0) { throw 'compute clone failed' }
    Assert-Canary ((Invoke-Git $sourceRepo @('rev-parse','HEAD')) -eq $baseHead) 'source clone HEAD mismatch'
    Assert-Canary ((Invoke-Git $computeRepo @('rev-parse','HEAD')) -eq $baseHead) 'compute clone HEAD mismatch'

    Write-Utf8NoBom (Join-Path $sourceRepo 'src\lib.rs') "pub fn value() -> u8 { 7 }`n"
    $markerRust = $marker.Replace('\','/')
    $buildRs = @"
fn main() {
    std::fs::write(r#"$markerRust"#, std::env::var("CARGO_MANIFEST_DIR").unwrap()).unwrap();
    std::thread::sleep(std::time::Duration::from_secs(95));
}
"@
    Write-Utf8NoBom (Join-Path $sourceRepo 'build.rs') $buildRs

    $sourceStatusBefore = Invoke-Git $sourceRepo @('status','--porcelain=v1','--untracked-files=all')
    $computeStatusBefore = Invoke-Git $computeRepo @('status','--porcelain=v1','--untracked-files=all')
    Assert-Canary ($sourceStatusBefore -match 'src/lib.rs') 'source checkout was not dirty as expected'
    Assert-Canary ($sourceStatusBefore -match 'build.rs') 'source untracked build.rs missing from dirty state'
    Assert-Canary ([string]::IsNullOrEmpty($computeStatusBefore)) 'compute checkout must start clean'
    $sourceLibBefore = [IO.File]::ReadAllText((Join-Path $sourceRepo 'src\lib.rs'))
    $computeLibBefore = [IO.File]::ReadAllText((Join-Path $computeRepo 'src\lib.rs'))

    $sourcePath = $sourceRepo.Replace('\','/')
    $computePath = $computeRepo.Replace('\','/')
    Write-Utf8NoBom (Join-Path $sourceProjects 'canary.toml') "id = `"canary`"`npath = `"$sourcePath`"`nname = `"Source Canary`"`nallow_patch = true`n"
    Write-Utf8NoBom (Join-Path $computeProjects 'canary.toml') "id = `"canary`"`npath = `"$computePath`"`nname = `"Compute Canary`"`nallow_patch = true`n"

    $sourceProjectsToml = $sourceProjects.Replace('\','/')
    $computeProjectsToml = $computeProjects.Replace('\','/')
    Write-Utf8NoBom $sourceToml "server_url = `"http://127.0.0.1:$port`"`ntoken = `"$token`"`nclient_id = `"sf-source`"`ndisplay_name = `"SF Source`"`nowner = `"local-canary`"`nprojects_dir = `"$sourceProjectsToml`"`npoll_interval_ms = 250`ntransport = `"websocket`"`n`n[policy]`nallow_raw_shell = true`nallow_cwd_anywhere = false`nallowed_roots = [`"$sourcePath`"]`nmax_timeout_secs = 240`nmax_output_bytes = 262144`n`n[capabilities]`nserver_compute = false`n"
    Write-Utf8NoBom $computeToml "server_url = `"http://127.0.0.1:$port`"`ntoken = `"$token`"`nclient_id = `"sf-compute`"`ndisplay_name = `"SF Compute`"`nowner = `"local-canary`"`nprojects_dir = `"$computeProjectsToml`"`npoll_interval_ms = 250`ntransport = `"websocket`"`n`n[policy]`nallow_raw_shell = true`nallow_cwd_anywhere = false`nallowed_roots = [`"$computePath`"]`nmax_timeout_secs = 240`nmax_output_bytes = 262144`n`n[capabilities]`nserver_compute = true`n"

    $oldAddr = $env:WEBCODEX_ADDR
    $oldData = $env:WEBCODEX_DATA
    $oldToken = $env:WEBCODEX_TOKEN
    $env:WEBCODEX_ADDR = "127.0.0.1:$port"
    $env:WEBCODEX_DATA = $dataDir
    $env:WEBCODEX_TOKEN = $token
    try {
        $server = Start-Process -FilePath $serverBin -PassThru -RedirectStandardOutput $serverOut -RedirectStandardError $serverErr -WindowStyle Hidden
    } finally {
        if ($null -eq $oldAddr) { Remove-Item Env:WEBCODEX_ADDR -ErrorAction SilentlyContinue } else { $env:WEBCODEX_ADDR = $oldAddr }
        if ($null -eq $oldData) { Remove-Item Env:WEBCODEX_DATA -ErrorAction SilentlyContinue } else { $env:WEBCODEX_DATA = $oldData }
        if ($null -eq $oldToken) { Remove-Item Env:WEBCODEX_TOKEN -ErrorAction SilentlyContinue } else { $env:WEBCODEX_TOKEN = $oldToken }
    }
    Assert-Canary (Wait-Port $port 30) 'local server did not listen within 30s'

    $sourceRunner = Start-Process -FilePath $runnerBin -ArgumentList @('--config',$sourceToml) -PassThru -RedirectStandardOutput $sourceOut -RedirectStandardError $sourceErr -WindowStyle Hidden
    $computeRunner = Start-Process -FilePath $runnerBin -ArgumentList @('--config',$computeToml) -PassThru -RedirectStandardOutput $computeOut -RedirectStandardError $computeErr -WindowStyle Hidden

    $status = $null
    $deadline = [DateTime]::UtcNow.AddSeconds(45)
    while ([DateTime]::UtcNow -lt $deadline) {
        try {
            $candidate = Invoke-ApiPost '/api/runtime/status' @{} 10
            $sourceClient = Get-Client $candidate 'sf-source'
            $computeClient = Get-Client $candidate 'sf-compute'
            if ($null -ne $sourceClient -and $null -ne $computeClient -and [int]$candidate.output.agents.online_count -ge 2) { $status = $candidate; break }
        } catch {}
        Start-Sleep -Milliseconds 500
    }
    Assert-Canary ($null -ne $status) 'both local runners did not register online'
    $sourceClient = Get-Client $status 'sf-source'
    $computeClient = Get-Client $status 'sf-compute'
    Assert-Canary (-not [bool]$sourceClient.capabilities.server_compute) 'source Runner unexpectedly opted into server_compute'
    Assert-Canary ([bool]$computeClient.capabilities.server_compute) 'compute Runner did not advertise server_compute'
    Assert-Canary ([bool]$sourceClient.capabilities.source_snapshot_validation) 'source Runner missing source_snapshot_validation'
    Assert-Canary ([bool]$computeClient.capabilities.source_snapshot_validation) 'compute Runner missing source_snapshot_validation'

    $sourceRuntime = 'agent:sf-source:canary'
    $computeRuntime = 'agent:sf-compute:canary'
    $started = [Diagnostics.Stopwatch]::StartNew()
    $cargoResponse = Invoke-ApiPost '/api/tools/call' @{ tool = 'cargo_check'; params = @{ project = $sourceRuntime; timeout_secs = 180 } } 135
    $started.Stop()
    Assert-Canary ([bool]$cargoResponse.success) ('cargo_check call failed: ' + ($cargoResponse | ConvertTo-Json -Depth 12 -Compress))
    Assert-Canary ([bool]$cargoResponse.output.promoted_to_job) 'cargo_check did not promote to durable Job after sync window'
    $jobId = [string]$cargoResponse.output.job_id
    Assert-Canary (-not [string]::IsNullOrWhiteSpace($jobId)) 'cargo_check handoff did not return job_id'
    Assert-Canary ($started.Elapsed.TotalSeconds -ge 85 -and $started.Elapsed.TotalSeconds -lt 135) ("unexpected handoff latency: $([math]::Round($started.Elapsed.TotalSeconds,1))s")

    $jobStatusResponse = Invoke-ApiPost '/api/tools/call' @{ tool = 'job_status'; params = @{ job_id = $jobId } } 15
    Assert-Canary ([bool]$jobStatusResponse.success) 'initial job_status failed'
    Assert-Canary ([string]$jobStatusResponse.output.client_id -eq 'sf-compute') ('job was not dispatched to sf-compute: ' + [string]$jobStatusResponse.output.client_id)
    Assert-Canary ([string]$jobStatusResponse.output.project -eq $computeRuntime) ('job project was not compute runtime: ' + [string]$jobStatusResponse.output.project)
    $identity = $jobStatusResponse.output.validation.source_snapshot_identity
    Assert-Canary ($null -ne $identity) 'job_status missing safe source_snapshot_identity'
    Assert-Canary ([string]$identity.base_git_head -eq $baseHead) 'snapshot identity base HEAD mismatch'
    Assert-Canary ([string]$identity.snapshot_sha256 -match '^[0-9a-f]{64}$') 'snapshot identity digest is not 64 lowercase hex'
    Assert-Canary ([int]$identity.entry_count -eq 2) ('snapshot identity entry_count mismatch: ' + [string]$identity.entry_count)

    $jobLogResponse = Invoke-ApiPost '/api/tools/call' @{ tool = 'job_log'; params = @{ job_id = $jobId; tail_lines = 100 } } 15
    Assert-Canary ([bool]$jobLogResponse.success) 'initial job_log failed'
    $logIdentity = $jobLogResponse.output.validation.source_snapshot_identity
    Assert-Canary ($null -ne $logIdentity) 'job_log missing safe source_snapshot_identity'
    Assert-Canary ([string]$logIdentity.snapshot_sha256 -eq [string]$identity.snapshot_sha256) 'job_status/job_log snapshot digest mismatch'
    $serializedProof = (($jobStatusResponse | ConvertTo-Json -Depth 30 -Compress) + ($jobLogResponse | ConvertTo-Json -Depth 30 -Compress))
    Assert-Canary (-not $serializedProof.Contains('pub fn value() -> u8 { 7 }')) 'raw source leaked into durable status/log projection'

    $terminal = $jobStatusResponse
    $terminalDeadline = [DateTime]::UtcNow.AddSeconds(70)
    while ([DateTime]::UtcNow -lt $terminalDeadline) {
        $state = [string]$terminal.output.status
        if ($state -in @('completed','failed','stopped','lost','timeout','timed_out','cancelled')) { break }
        Start-Sleep -Seconds 1
        $terminal = Invoke-ApiPost '/api/tools/call' @{ tool = 'job_status'; params = @{ job_id = $jobId } } 15
    }
    Assert-Canary ([string]$terminal.output.status -eq 'completed') ('validation did not complete successfully: ' + [string]$terminal.output.status + ' error=' + [string]$terminal.output.error)
    Assert-Canary ([int]$terminal.output.exit_code -eq 0) ('validation exit code was not zero: ' + [string]$terminal.output.exit_code)
    $terminalIdentity = $terminal.output.validation.source_snapshot_identity
    Assert-Canary ([string]$terminalIdentity.snapshot_sha256 -eq [string]$identity.snapshot_sha256) 'terminal snapshot identity changed'

    $finalLog = Invoke-ApiPost '/api/tools/call' @{ tool = 'job_log'; params = @{ job_id = $jobId; tail_lines = 100 } } 15
    Assert-Canary ([bool]$finalLog.success) 'terminal job_log failed'
    Assert-Canary ([string]$finalLog.output.validation.source_snapshot_identity.snapshot_sha256 -eq [string]$identity.snapshot_sha256) 'terminal job_log identity changed'
    $finalProof = (($terminal | ConvertTo-Json -Depth 30 -Compress) + ($finalLog | ConvertTo-Json -Depth 30 -Compress))
    Assert-Canary (-not $finalProof.Contains('pub fn value() -> u8 { 7 }')) 'raw source leaked into terminal durable proof'

    Assert-Canary (Test-Path $marker) 'build.rs marker was not produced by validation'
    $manifestDir = ([IO.File]::ReadAllText($marker)).Trim()
    Assert-Canary (-not [string]::IsNullOrWhiteSpace($manifestDir)) 'materialized manifest path marker is empty'
    $manifestNorm = Normalize-Path $manifestDir
    Assert-Canary ($manifestNorm -ne (Normalize-Path $sourceRepo)) 'validation ran in authoritative source checkout'
    Assert-Canary ($manifestNorm -ne (Normalize-Path $computeRepo)) 'validation ran in authoritative compute checkout'
    $cleanupDeadline = [DateTime]::UtcNow.AddSeconds(15)
    while ((Test-Path $manifestDir) -and [DateTime]::UtcNow -lt $cleanupDeadline) { Start-Sleep -Milliseconds 250 }
    Assert-Canary (-not (Test-Path $manifestDir)) ('ephemeral materialized checkout was not removed: ' + $manifestDir)

    Assert-Canary ((Invoke-Git $sourceRepo @('status','--porcelain=v1','--untracked-files=all')) -eq $sourceStatusBefore) 'source authoritative Git status changed'
    Assert-Canary ((Invoke-Git $computeRepo @('status','--porcelain=v1','--untracked-files=all')) -eq $computeStatusBefore) 'compute authoritative Git status changed'
    Assert-Canary ([IO.File]::ReadAllText((Join-Path $sourceRepo 'src\lib.rs')) -eq $sourceLibBefore) 'source authoritative content changed'
    Assert-Canary ([IO.File]::ReadAllText((Join-Path $computeRepo 'src\lib.rs')) -eq $computeLibBefore) 'compute authoritative content changed'

    Write-Host ("CANARY_PASS source={0} target={1} job={2} base={3} snapshot={4} entries=2 handoff_secs={5} materialized={6}" -f $sourceRuntime,$computeRuntime,$jobId,$baseHead,[string]$identity.snapshot_sha256,[math]::Round($started.Elapsed.TotalSeconds,1),$manifestDir)
} catch {
    $failed = $true
    Write-Host ('CANARY_FAIL ' + $_.Exception.Message)
    foreach ($log in @($serverErr,$sourceErr,$computeErr)) {
        if (Test-Path $log) {
            Write-Host ('--- ' + [IO.Path]::GetFileName($log) + ' tail ---')
            Get-Content $log -Tail 60 -ErrorAction SilentlyContinue
        }
    }
} finally {
    Stop-Tree $computeRunner
    Stop-Tree $sourceRunner
    Stop-Tree $server
    Start-Sleep -Milliseconds 500
    if (Test-Path $tempRoot) { Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue }
}

if ($failed) { exit 1 }
exit 0

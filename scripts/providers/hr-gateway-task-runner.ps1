[CmdletBinding()]
param(
    [ValidateRange(15, 180)]
    [int]$ReadyTimeoutSeconds = 60
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($env:OS -ne "Windows_NT") {
    throw "HR_GATEWAY_TASK_RUNNER_WINDOWS_ONLY"
}

$providerRoot = Split-Path -Parent $PSCommandPath
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $providerRoot "..\.."))
$backendRoot = Join-Path $repoRoot "backend"
$runtimeRoot = Join-Path $env:LOCALAPPDATA "STA\HR-Gateway"
$receiptPath = Join-Path $runtimeRoot "runtime-receipt.json"
$gatewayPort = 3001

function Get-HrGatewaySourceFingerprint {
    $rootPrefix = $repoRoot.TrimEnd('\') + '\'
    $files = @(Get-ChildItem -LiteralPath $backendRoot -Recurse -File -ErrorAction Stop | Where-Object {
        $full = $_.FullName
        $relative = if ($full.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) { $full.Substring($rootPrefix.Length) } else { $full }
        $normalized = $relative.Replace('\', '/').ToLowerInvariant()
        $extensionAllowed = @('.js', '.cjs', '.mjs', '.json') -contains $_.Extension.ToLowerInvariant()
        $extensionAllowed -and
            -not $normalized.Contains('/node_modules/') -and
            -not $normalized.Contains('/tests/') -and
            -not $normalized.Contains('/logs/') -and
            -not $normalized.Contains('/certs/') -and
            -not $normalized.Contains('/coverage/') -and
            -not $_.Name.StartsWith('.env', [System.StringComparison]::OrdinalIgnoreCase)
    } | Sort-Object FullName)
    if ($files.Count -eq 0) { throw "HR_GATEWAY_SOURCE_FINGERPRINT_EMPTY" }

    $manifest = foreach ($file in $files) {
        $full = [System.IO.Path]::GetFullPath($file.FullName)
        if (-not $full.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "HR_GATEWAY_SOURCE_PATH_OUTSIDE_CHECKOUT"
        }
        $relative = $full.Substring($rootPrefix.Length).Replace('\', '/')
        $hash = (Get-FileHash -LiteralPath $full -Algorithm SHA256).Hash.ToLowerInvariant()
        "$relative`t$hash"
    }
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes(($manifest -join "`n"))
        $digest = $sha.ComputeHash($bytes)
        return -join ($digest | ForEach-Object { $_.ToString('x2') })
    } finally {
        $sha.Dispose()
    }
}

function Get-ProcessCreationIso {
    param([Parameter(Mandatory)] [int]$ProcessId)
    $process = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction SilentlyContinue
    if (-not $process) { return $null }
    return $process.CreationDate.ToUniversalTime().ToString('o')
}

function Write-RuntimeReceipt {
    param([Parameter(Mandatory)] [hashtable]$Receipt)
    New-Item -ItemType Directory -Path $runtimeRoot -Force | Out-Null
    $Receipt.event = 'hr.local.gateway-runtime'
    $Receipt.capturedAt = [DateTimeOffset]::UtcNow.ToString('o')
    $Receipt.workspace = $repoRoot
    $Receipt.port = $gatewayPort
    $Receipt.hosting = 'WINDOWS_SCHEDULED_TASK'
    $Receipt.authority = 'LOCAL_ONLY'
    $Receipt.gatePromotion = $false
    $json = $Receipt | ConvertTo-Json -Depth 5
    $temporary = "$receiptPath.tmp.$PID"
    Set-Content -LiteralPath $temporary -Value $json -Encoding UTF8
    Move-Item -LiteralPath $temporary -Destination $receiptPath -Force
}

function Test-GatewayHealth {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$gatewayPort/health" -Method Get -TimeoutSec 2
        return [int]$response.StatusCode -ge 200 -and [int]$response.StatusCode -lt 300
    } catch {
        return $false
    }
}

New-Item -ItemType Directory -Path $runtimeRoot -Force | Out-Null
$sourceFingerprint = Get-HrGatewaySourceFingerprint
$existingListener = @(Get-NetTCPConnection -LocalPort $gatewayPort -State Listen -ErrorAction SilentlyContinue)
if ($existingListener.Count -gt 0) {
    Write-RuntimeReceipt -Receipt @{
        state = 'blocked'
        healthStatus = 'not_checked'
        sourceFingerprint = $sourceFingerprint
        gatewayPid = $null
        gatewayCreationDate = $null
        errorCode = 'HR_GATEWAY_PORT_ALREADY_IN_USE'
    }
    exit 21
}

$node = (Get-Command node.exe -ErrorAction Stop).Source
$stamp = [DateTimeOffset]::UtcNow.ToString('yyyyMMdd-HHmmss')
$stdoutPath = Join-Path $runtimeRoot "gateway-$stamp.stdout.log"
$stderrPath = Join-Path $runtimeRoot "gateway-$stamp.stderr.log"
$child = $null
try {
    $child = Start-Process -FilePath $node -ArgumentList @('server.js') -WorkingDirectory $backendRoot -PassThru -WindowStyle Hidden -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
    $creationDate = Get-ProcessCreationIso -ProcessId $child.Id
    if (-not $creationDate) { throw 'HR_GATEWAY_PROCESS_IDENTITY_UNAVAILABLE' }

    Write-RuntimeReceipt -Receipt @{
        state = 'starting'
        healthStatus = 'pending'
        sourceFingerprint = $sourceFingerprint
        gatewayPid = $child.Id
        gatewayCreationDate = $creationDate
        stdoutLog = [System.IO.Path]::GetFileName($stdoutPath)
        stderrLog = [System.IO.Path]::GetFileName($stderrPath)
        errorCode = $null
    }

    $deadline = [DateTimeOffset]::UtcNow.AddSeconds($ReadyTimeoutSeconds)
    $ready = $false
    do {
        if ($child.HasExited) { break }
        if (Test-GatewayHealth) {
            $listener = @(Get-NetTCPConnection -LocalPort $gatewayPort -State Listen -ErrorAction SilentlyContinue | Where-Object { [int]$_.OwningProcess -eq $child.Id })
            if ($listener.Count -gt 0) {
                $ready = $true
                break
            }
        }
        Start-Sleep -Milliseconds 500
    } while ([DateTimeOffset]::UtcNow -lt $deadline)

    if (-not $ready) {
        if (-not $child.HasExited) { Stop-Process -Id $child.Id -Force -ErrorAction SilentlyContinue }
        Write-RuntimeReceipt -Receipt @{
            state = 'failed'
            healthStatus = 'not_ready'
            sourceFingerprint = $sourceFingerprint
            gatewayPid = $child.Id
            gatewayCreationDate = $creationDate
            errorCode = 'HR_GATEWAY_NOT_READY'
        }
        exit 22
    }

    Write-RuntimeReceipt -Receipt @{
        state = 'ready'
        healthStatus = 'ready'
        healthCheckedAt = [DateTimeOffset]::UtcNow.ToString('o')
        sourceFingerprint = $sourceFingerprint
        gatewayPid = $child.Id
        gatewayCreationDate = $creationDate
        stdoutLog = [System.IO.Path]::GetFileName($stdoutPath)
        stderrLog = [System.IO.Path]::GetFileName($stderrPath)
        errorCode = $null
    }

    $child.WaitForExit()
    $exitCode = $child.ExitCode
    Write-RuntimeReceipt -Receipt @{
        state = 'exited'
        healthStatus = 'stopped'
        sourceFingerprint = $sourceFingerprint
        gatewayPid = $child.Id
        gatewayCreationDate = $creationDate
        gatewayExitCode = $exitCode
        errorCode = 'HR_GATEWAY_PROCESS_EXITED'
    }
    exit $exitCode
} catch {
    if ($child -and -not $child.HasExited) {
        Stop-Process -Id $child.Id -Force -ErrorAction SilentlyContinue
    }
    Write-RuntimeReceipt -Receipt @{
        state = 'failed'
        healthStatus = 'failed'
        sourceFingerprint = $sourceFingerprint
        gatewayPid = if ($child) { $child.Id } else { $null }
        gatewayCreationDate = if ($child) { Get-ProcessCreationIso -ProcessId $child.Id } else { $null }
        errorCode = 'HR_GATEWAY_TASK_RUNNER_FAILED'
    }
    exit 23
}

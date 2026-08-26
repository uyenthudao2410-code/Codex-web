[CmdletBinding()]
param(
    [ValidateSet('Status', 'Register', 'Ensure', 'Start', 'Stop', 'Unregister')]
    [string]$Action = 'Status',
    [ValidateRange(15, 180)]
    [int]$ReadyTimeoutSeconds = 60
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($env:OS -ne 'Windows_NT') {
    throw 'HR_GATEWAY_RUNTIME_PROVIDER_WINDOWS_ONLY'
}

$providerRoot = Split-Path -Parent $PSCommandPath
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $providerRoot '..\..'))
$backendRoot = Join-Path $repoRoot 'backend'
$runnerPath = Join-Path $providerRoot 'hr-gateway-task-runner.ps1'
$runtimeRoot = Join-Path $env:LOCALAPPDATA 'STA\HR-Gateway'
$receiptPath = Join-Path $runtimeRoot 'runtime-receipt.json'
$taskName = 'STA-HR-Gateway-Local'
$gatewayPort = 3001
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$powershellPath = (Get-Command powershell.exe -ErrorAction Stop).Source
$expectedTaskArguments = "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$runnerPath`""

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
    if ($files.Count -eq 0) { throw 'HR_GATEWAY_SOURCE_FINGERPRINT_EMPTY' }

    $manifest = foreach ($file in $files) {
        $full = [System.IO.Path]::GetFullPath($file.FullName)
        if (-not $full.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw 'HR_GATEWAY_SOURCE_PATH_OUTSIDE_CHECKOUT'
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

function Get-ManagedTask {
    return Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
}

function Test-TaskIdentityOwned {
    param($Task)
    if (-not $Task) { return $false }
    $actions = @($Task.Actions)
    if ($actions.Count -ne 1) { return $false }
    $actualExecute = [System.IO.Path]::GetFullPath([string]$actions[0].Execute)
    $expectedExecute = [System.IO.Path]::GetFullPath($powershellPath)
    return $actualExecute.Equals($expectedExecute, [System.StringComparison]::OrdinalIgnoreCase) -and
        ([string]$actions[0].Arguments).Equals($expectedTaskArguments, [System.StringComparison]::Ordinal)
}

function Test-TaskConfigurationCurrent {
    param($Task)
    if (-not (Test-TaskIdentityOwned -Task $Task)) { return $false }
    if (-not ([string]$Task.Principal.UserId).Equals($currentUser, [System.StringComparison]::OrdinalIgnoreCase)) { return $false }
    if ([string]$Task.Principal.RunLevel -ne 'Limited') { return $false }
    if ([int]$Task.Settings.RestartCount -ne 5) { return $false }
    if ([string]$Task.Settings.RestartInterval -ne 'PT1M') { return $false }
    if ([string]$Task.Settings.ExecutionTimeLimit -ne 'PT0S') { return $false }
    return $true
}

function Assert-TaskIdentityOwned {
    param($Task)
    if ($Task -and -not (Test-TaskIdentityOwned -Task $Task)) {
        throw 'HR_GATEWAY_RUNTIME_TASK_NAME_COLLISION'
    }
}

function Register-HrGatewayTask {
    $existing = Get-ManagedTask
    Assert-TaskIdentityOwned -Task $existing
    if ($existing -and (Test-TaskConfigurationCurrent -Task $existing)) { return $existing }
    if ($existing -and [string]$existing.State -eq 'Running') {
        Stop-ScheduledTask -TaskName $taskName -ErrorAction Stop
        Start-Sleep -Milliseconds 500
    }

    $actionSpec = New-ScheduledTaskAction -Execute $powershellPath -Argument $expectedTaskArguments -WorkingDirectory $repoRoot
    $triggerSpec = New-ScheduledTaskTrigger -AtLogOn -User $currentUser
    $principalSpec = New-ScheduledTaskPrincipal -UserId $currentUser -LogonType Interactive -RunLevel Limited
    $settingsSpec = New-ScheduledTaskSettingsSet -RestartCount 5 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -StartWhenAvailable -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
    Register-ScheduledTask -TaskName $taskName -Action $actionSpec -Trigger $triggerSpec -Principal $principalSpec -Settings $settingsSpec -Description 'STA local HR Gateway only; current checkout port 3001.' -Force | Out-Null
    $registered = Get-ManagedTask
    if (-not $registered -or -not (Test-TaskConfigurationCurrent -Task $registered)) {
        throw 'HR_GATEWAY_RUNTIME_TASK_REGISTRATION_INCOMPLETE'
    }
    return $registered
}

function Get-ProcessCreationIso {
    param([Parameter(Mandatory)] [int]$ProcessId)
    $process = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction SilentlyContinue
    if (-not $process) { return $null }
    return $process.CreationDate.ToUniversalTime().ToString('o')
}

function Get-GatewayListenerState {
    $connections = @(Get-NetTCPConnection -LocalPort $gatewayPort -State Listen -ErrorAction SilentlyContinue)
    if ($connections.Count -eq 0) { return $null }
    $pids = @($connections | ForEach-Object { [int]$_.OwningProcess } | Sort-Object -Unique)
    if ($pids.Count -ne 1) { throw 'HR_GATEWAY_LISTENER_IDENTITY_AMBIGUOUS' }

    $all = @(Get-CimInstance Win32_Process -ErrorAction Stop)
    $byId = @{}
    foreach ($process in $all) { $byId[[int]$process.ProcessId] = $process }
    $owner = $byId[$pids[0]]
    if (-not $owner) { throw 'HR_GATEWAY_LISTENER_PROCESS_MISSING' }

    $chain = @()
    $current = $owner
    $guard = 0
    while ($current -and $guard -lt 20) {
        if ($current.CommandLine) { $chain += [string]$current.CommandLine }
        $parentId = [int]$current.ParentProcessId
        if ($parentId -le 0 -or $parentId -eq [int]$current.ProcessId) { break }
        $current = $byId[$parentId]
        $guard++
    }
    $joined = ($chain -join ' ').ToLowerInvariant().Replace('\', '/')
    $rootMarker = $repoRoot.ToLowerInvariant().Replace('\', '/').TrimEnd('/')
    $runnerMarker = $runnerPath.ToLowerInvariant().Replace('\', '/')
    $fromCheckout = $joined.Contains($rootMarker)
    $runtimeMarker = $joined.Contains($runnerMarker) -or $joined.Contains('node server.js') -or $joined.Contains('npm --prefix backend run start') -or $joined.Contains('runtime:backend')
    $mixedSupervisor = $joined.Contains('scripts/start-runtime.cjs')
    return [pscustomobject][ordered]@{
        pid = [int]$owner.ProcessId
        creationDate = $owner.CreationDate.ToUniversalTime().ToString('o')
        owned = [bool]($fromCheckout -and $runtimeMarker)
        mixedSupervisor = [bool]$mixedSupervisor
    }
}

function Wait-GatewayPortFree {
    param([Parameter(Mandatory)] [int]$TimeoutSeconds)
    $deadline = [DateTimeOffset]::UtcNow.AddSeconds($TimeoutSeconds)
    do {
        if (-not (Get-GatewayListenerState)) { return $true }
        Start-Sleep -Milliseconds 250
    } while ([DateTimeOffset]::UtcNow -lt $deadline)
    return $false
}

function Stop-CheckoutGatewayListener {
    param([Parameter(Mandatory)] $Listener)
    if (-not $Listener.owned) { throw 'HR_GATEWAY_PORT_IN_USE_UNOWNED' }
    if ($Listener.mixedSupervisor) { throw 'HR_GATEWAY_MIXED_SUPERVISOR_ACTIVE' }

    $current = Get-GatewayListenerState
    if (-not $current) { return $false }
    if ($current.pid -ne $Listener.pid -or $current.creationDate -ne $Listener.creationDate) {
        throw 'HR_GATEWAY_LISTENER_IDENTITY_CHANGED'
    }
    if (-not $current.owned) { throw 'HR_GATEWAY_PORT_IN_USE_UNOWNED' }
    if ($current.mixedSupervisor) { throw 'HR_GATEWAY_MIXED_SUPERVISOR_ACTIVE' }

    & taskkill.exe /pid ([string]$current.pid) /T /F *> $null
    if ($LASTEXITCODE -ne 0 -and (Get-GatewayListenerState)) {
        throw 'HR_GATEWAY_LISTENER_TERMINATION_FAILED'
    }
    if (-not (Wait-GatewayPortFree -TimeoutSeconds 10)) {
        throw 'HR_GATEWAY_PORT_RELEASE_TIMEOUT'
    }
    return $true
}

function Read-RuntimeReceipt {
    if (-not (Test-Path -LiteralPath $receiptPath)) { return $null }
    try {
        return Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json
    } catch {
        return $null
    }
}

function Remove-RuntimeReceipt {
    if (Test-Path -LiteralPath $receiptPath) { Remove-Item -LiteralPath $receiptPath -Force }
}

function Test-ReceiptProcessIdentity {
    param($Receipt)
    if (-not $Receipt -or -not $Receipt.gatewayPid -or -not $Receipt.gatewayCreationDate) { return $false }
    $currentCreation = Get-ProcessCreationIso -ProcessId ([int]$Receipt.gatewayPid)
    return $currentCreation -and $currentCreation.Equals([string]$Receipt.gatewayCreationDate, [System.StringComparison]::OrdinalIgnoreCase)
}

function Stop-ReceiptGatewayProcess {
    $receipt = Read-RuntimeReceipt
    if (-not (Test-ReceiptProcessIdentity -Receipt $receipt)) { return $false }
    $listener = Get-GatewayListenerState
    if (-not $listener) { return $false }
    if ($listener.pid -ne [int]$receipt.gatewayPid) { return $false }
    if (-not $listener.owned) { throw 'HR_GATEWAY_RECEIPT_PROCESS_NOT_OWNED' }
    if ($listener.mixedSupervisor) { throw 'HR_GATEWAY_MIXED_SUPERVISOR_ACTIVE' }
    return Stop-CheckoutGatewayListener -Listener $listener
}

function Get-ProviderStatus {
    $sourceFingerprint = Get-HrGatewaySourceFingerprint
    $task = Get-ManagedTask
    Assert-TaskIdentityOwned -Task $task
    $receipt = Read-RuntimeReceipt
    $listener = Get-GatewayListenerState
    $receiptProcessCurrent = Test-ReceiptProcessIdentity -Receipt $receipt
    $receiptSourceCurrent = [bool]($receipt -and [string]$receipt.sourceFingerprint -eq $sourceFingerprint)
    $listenerMatchesReceipt = [bool]($listener -and $receipt -and [int]$receipt.gatewayPid -eq [int]$listener.pid)
    $taskConfigurationCurrent = Test-TaskConfigurationCurrent -Task $task
    $ready = [bool]($task -and $taskConfigurationCurrent -and $receipt -and [string]$receipt.state -eq 'ready' -and [string]$receipt.healthStatus -eq 'ready' -and $receiptProcessCurrent -and $receiptSourceCurrent -and $listenerMatchesReceipt -and $listener.owned -and -not $listener.mixedSupervisor)

    return [ordered]@{
        event = 'hr.local.gateway-runtime-provider'
        capturedAt = [DateTimeOffset]::UtcNow.ToString('o')
        action = $Action.ToLowerInvariant()
        taskName = $taskName
        taskRegistered = [bool]$task
        taskState = if ($task) { [string]$task.State } else { $null }
        taskConfigurationCurrent = [bool]$taskConfigurationCurrent
        workspace = $repoRoot
        sourceFingerprint = $sourceFingerprint
        receiptSourceFingerprint = if ($receipt) { [string]$receipt.sourceFingerprint } else { $null }
        receiptSourceCurrent = [bool]$receiptSourceCurrent
        receiptState = if ($receipt) { [string]$receipt.state } else { $null }
        receiptHealthStatus = if ($receipt) { [string]$receipt.healthStatus } else { $null }
        receiptProcessCurrent = [bool]$receiptProcessCurrent
        gatewayPid = if ($listener) { [int]$listener.pid } else { $null }
        gatewayListenerOwned = if ($listener) { [bool]$listener.owned } else { $false }
        mixedSupervisor = if ($listener) { [bool]$listener.mixedSupervisor } else { $false }
        port = $gatewayPort
        portListening = [bool]$listener
        ready = $ready
        hosting = 'WINDOWS_SCHEDULED_TASK'
        authority = 'LOCAL_ONLY'
        gatePromotion = $false
    }
}

function Wait-ProviderReady {
    param([Parameter(Mandatory)] [int]$TimeoutSeconds)
    $deadline = [DateTimeOffset]::UtcNow.AddSeconds($TimeoutSeconds)
    do {
        $status = Get-ProviderStatus
        if ($status.ready) { return $status }
        Start-Sleep -Milliseconds 500
    } while ([DateTimeOffset]::UtcNow -lt $deadline)
    throw 'HR_GATEWAY_RUNTIME_NOT_READY'
}

function Stop-ManagedTaskAndGateway {
    $task = Get-ManagedTask
    Assert-TaskIdentityOwned -Task $task
    if ($task -and [string]$task.State -eq 'Running') {
        Stop-ScheduledTask -TaskName $taskName -ErrorAction Stop
        Start-Sleep -Milliseconds 500
    }
    Stop-ReceiptGatewayProcess | Out-Null
}

function Ensure-HrGatewayRuntime {
    $initial = Get-ProviderStatus
    if ($initial.ready) { return $initial }

    $task = Register-HrGatewayTask
    if ([string]$task.State -eq 'Running') {
        Stop-ScheduledTask -TaskName $taskName -ErrorAction Stop
        Start-Sleep -Milliseconds 500
    }
    Stop-ReceiptGatewayProcess | Out-Null

    $listener = Get-GatewayListenerState
    if ($listener) {
        Stop-CheckoutGatewayListener -Listener $listener | Out-Null
    }
    Remove-RuntimeReceipt

    Start-ScheduledTask -TaskName $taskName -ErrorAction Stop
    return Wait-ProviderReady -TimeoutSeconds $ReadyTimeoutSeconds
}

switch ($Action) {
    'Register' { Register-HrGatewayTask | Out-Null }
    'Ensure' { Ensure-HrGatewayRuntime | Out-Null }
    'Start' {
        $task = Get-ManagedTask
        if (-not $task) { throw 'HR_GATEWAY_RUNTIME_TASK_NOT_REGISTERED' }
        Assert-TaskIdentityOwned -Task $task
        $status = Get-ProviderStatus
        if (-not $status.ready) {
            if (Get-GatewayListenerState) { throw 'HR_GATEWAY_PORT_ALREADY_IN_USE' }
            Remove-RuntimeReceipt
            Start-ScheduledTask -TaskName $taskName -ErrorAction Stop
            Wait-ProviderReady -TimeoutSeconds $ReadyTimeoutSeconds | Out-Null
        }
    }
    'Stop' { Stop-ManagedTaskAndGateway }
    'Unregister' {
        Stop-ManagedTaskAndGateway
        $task = Get-ManagedTask
        if ($task) {
            Assert-TaskIdentityOwned -Task $task
            Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction Stop
        }
    }
    default { }
}

Get-ProviderStatus | ConvertTo-Json -Depth 5

$ErrorActionPreference = 'Stop'
function Write-FeatureReceipt($state, $restartNeeded) {
    $receipt = [pscustomobject]@{
        feature = 'Containers-DisposableClientVM'
        state = $state
        restartNeeded = [bool]$restartNeeded
        observedAt = [DateTimeOffset]::UtcNow.ToString('o')
        automaticRestart = $false
    }
    $receipt | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'windows-sandbox-feature-result.json') -Encoding UTF8
    $receipt
}
$principal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Open PowerShell as Administrator before running this script.'
}
$feature = Get-WindowsOptionalFeature -Online -FeatureName Containers-DisposableClientVM
if ($feature.State -eq 'Enabled') {
    Write-FeatureReceipt 'Enabled' $false
    exit 0
}
$result = Enable-WindowsOptionalFeature -Online -FeatureName Containers-DisposableClientVM -All -NoRestart
$after = Get-WindowsOptionalFeature -Online -FeatureName Containers-DisposableClientVM
Write-FeatureReceipt ([string]$after.State) $result.RestartNeeded
# Restart is a separate operator action; no automatic restart occurs here.

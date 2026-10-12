param([Parameter(Mandatory)][string]$TransportSha256)
$ErrorActionPreference = 'Stop'
$r11CanaryRoot = 'E:\Github\Tools-Codex-web\.coding-tools\reports\unified-setup-20261011\executor-repair\candidate-r11'
$r11CanaryTransport = Join-Path $r11CanaryRoot 'live-canary-contract-sync\root-canary-ssh.py'
if ((Get-FileHash -LiteralPath $r11CanaryTransport -Algorithm SHA256).Hash.ToLower() -ne $TransportSha256) { throw 'FROZEN_CANARY_TRANSPORT_CHANGED' }
$r11NativeHelper = Join-Path $r11CanaryRoot 'native-live-correlation\native-preflight.cjs'
if ((Get-FileHash -LiteralPath $r11NativeHelper -Algorithm SHA256).Hash.ToLower() -ne 'adef853e95c6103f1d822bb3cfaea9827d2ae4f2d38bfba8d79c3c1a90a4cbd4') { throw 'FROZEN_NATIVE_PREFLIGHT_CHANGED' }
$r11NativePreflight = (& node $r11NativeHelper | ConvertFrom-Json)
if ($LASTEXITCODE -ne 0 -or -not $r11NativePreflight.ok) { throw 'FRESH_NATIVE_PREFLIGHT_FAILED' }
$r11Renewal = (Get-Content -LiteralPath (Join-Path $r11CanaryRoot 'authority-renewal-next\remote-receipts\renew-20261011T162210220806Z.json') -Raw | ConvertFrom-Json).public_receipts[0]
if (-not $r11Renewal.ok -or $r11Renewal.approval_id -ne 'call_flEpmLChKJPZsbnlAAXR5byS') { throw 'NEW_APPROVED_RENEWAL_REQUIRED' }
$r11CanaryPins = Get-Content -LiteralPath (Join-Path $r11CanaryRoot 'live-canary-contract-sync\pins.template.json') -Raw | ConvertFrom-Json
foreach ($name in @('requested_at_ms','expires_at_ms','context_id','pilot_id','service_instance_id')) { $r11CanaryPins.$name = $r11Renewal.$name }
foreach ($name in @('activation_epoch','runtime_instance_id','mcp_server_instance_id','contract_version','native_tool_contract_sha256')) { $r11CanaryPins.$name = $r11NativePreflight.$name }
$r11CanaryPins.native_preflight = $r11NativePreflight.native_preflight
$r11CanaryPins.native_preflight | Add-Member receipt_sha256 $r11NativePreflight.receipt_sha256
$r11CanaryPinsFile = Join-Path $r11CanaryRoot ('live-canary-contract-sync\pins-live-' + $r11NativePreflight.observed_at_ms + '.json')
$r11PinsBytes = [Text.UTF8Encoding]::new($false).GetBytes(($r11CanaryPins | ConvertTo-Json -Depth 15) + "`n")
$r11PinsStream = [IO.File]::Open($r11CanaryPinsFile, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
try { $r11PinsStream.Write($r11PinsBytes, 0, $r11PinsBytes.Length); $r11PinsStream.Flush($true) } finally { $r11PinsStream.Dispose() }
$r11Prepared = (& python -B $r11CanaryTransport prepare --pins $r11CanaryPinsFile --native-preflight $r11NativePreflight.receipt_path --expected-native-preflight-sha256 $r11NativePreflight.receipt_sha256 | ConvertFrom-Json)
if ($LASTEXITCODE -ne 0 -or -not $r11Prepared.ok) { $r11Prepared | ConvertTo-Json -Depth 10; throw 'CANARY_PREPARATION_FAILED' }
@{phase='root_canary_packet';manifest_path=$r11Prepared.manifest_path;pins_path=$r11CanaryPinsFile;native_preflight_path=$r11NativePreflight.receipt_path;native_preflight_sha256=$r11NativePreflight.receipt_sha256} | ConvertTo-Json -Compress
foreach ($phase in @('stage','preflight','dispatch')) {
    $r11PhaseReceipt = (& python -B $r11CanaryTransport $phase --manifest $r11Prepared.manifest_path --execute | ConvertFrom-Json)
    $r11PhaseCode = $LASTEXITCODE
    $r11PhaseReceipt | ConvertTo-Json -Depth 12
    if ($r11PhaseCode -ne 0 -or -not $r11PhaseReceipt.ok) { throw 'CANARY_PHASE_FAILED_RECONCILE_NO_REPLAY' }
}

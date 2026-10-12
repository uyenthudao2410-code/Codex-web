$ErrorActionPreference = 'Stop'
$r11EvidenceRoot = 'E:\Github\Tools-Codex-web\.coding-tools\reports\unified-setup-20261011\executor-repair\candidate-r11'
$r11RenewTransport = Join-Path $r11EvidenceRoot 'authority-renewal-next\root-ssh-next.py'
$r11RenewRemote = '/home/svhome/.local/lib/codex-control-plane/incoming/r11-approved-20261011T161810185934Z'
$r11RenewalFile = Join-Path $r11EvidenceRoot 'authority-renewal-next\remote-receipts\renew-20261011T162210220806Z.json'

function Get-R11RecoveryReceipt {
    if ((Get-FileHash -LiteralPath $r11RenewTransport -Algorithm SHA256).Hash.ToLower() -ne '5e6ab36c5c9979c1c1a8f20556e3496fad66377d49c3cd14407b6857bfe69591') { throw 'RENEWAL_TRANSPORT_CHANGED' }
    $wrapper = (& python -B $r11RenewTransport observe --remote-dir $r11RenewRemote | ConvertFrom-Json)
    if ($LASTEXITCODE -ne 0 -or $wrapper.ssh_returncode -ne 0 -or $wrapper.remote_dir -ne $r11RenewRemote -or $wrapper.public_receipts.Count -ne 1) { throw 'READ_ONLY_SERVER_OBSERVATION_FAILED' }
    $public = $wrapper.public_receipts[0]
    if (-not $public.ok -or $public.service_instance_id -ne 'cp_339c7a19bc2443eeab35583addfef543' -or $public.admission -ne 'recovery') { throw 'EXACT_R11_RECOVERY_REQUIRED' }
    # The frozen observer omits these constant identity labels. Preserve the raw
    # receipt and explicitly record that labels come from the pinned SSH target
    # and common.inspect()'s verified user-service identity, not extra telemetry.
    $public | Add-Member host '100.116.112.22'
    $public | Add-Member service 'codex-control-plane.service'
    $public | Add-Member root_receipt_derivation @{
        transport_receipt = $wrapper.receipt_path
        transport_sha256 = (Get-FileHash -LiteralPath $wrapper.receipt_path -Algorithm SHA256).Hash.ToLower()
        host_service_source = 'pinned SSH target and verified r11 user-service inspection'
    }
    $receipt = Join-Path $r11EvidenceRoot ('server-recovery-observed-' + (Get-Date -Format yyyyMMddTHHmmssfff) + '.json')
    if (Test-Path -LiteralPath $receipt) { throw 'EXCLUSIVE_RECEIPT_ALREADY_EXISTS' }
    $public | ConvertTo-Json -Depth 15 | Set-Content -LiteralPath $receipt -Encoding utf8
    return @{ path = $receipt; sha256 = (Get-FileHash -LiteralPath $receipt -Algorithm SHA256).Hash.ToLower(); observation = $public }
}

function Invoke-R11ResumePhase {
    param([string]$Helper, [string]$HelperSha256, [string]$Phase, [string[]]$ExtraFlags = @())
    if (-not [IO.Path]::IsPathRooted($Helper) -or (Get-FileHash -LiteralPath $Helper -Algorithm SHA256).Hash.ToLower() -ne $HelperSha256) { throw 'PINNED_RESUME_HELPER_CHANGED' }
    $server = Get-R11RecoveryReceipt
    $renewalSha = (Get-FileHash -LiteralPath $r11RenewalFile -Algorithm SHA256).Hash.ToLower()
    & node $Helper $Phase --operator-approved-r11-resume "--helper-sha256=$HelperSha256" "--server=$($server.path)" "--server-sha256=$($server.sha256)" "--renewal=$r11RenewalFile" "--renewal-sha256=$renewalSha" @ExtraFlags
    if ($LASTEXITCODE -ne 0) { throw 'RESUME_PHASE_FAILED_RECONCILE_NO_REPLAY' }
}

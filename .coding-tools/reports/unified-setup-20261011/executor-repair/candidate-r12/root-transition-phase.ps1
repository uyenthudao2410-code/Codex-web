param([Parameter(Mandatory)][ValidateSet('policy','agent','refresh','finalize','proof')][string]$Phase)
$ErrorActionPreference = 'Stop'
$r12Root = $PSScriptRoot
$r12Driver = Join-Path $r12Root 'authority-renewal\root-ssh-r12.py'
$r12Windows = Join-Path $r12Root 'activation-windows\transition-r12.cjs'
$r12Remote = '/home/svhome/.local/lib/codex-control-plane/incoming/r11-approved-20261011T194141943554Z'
if ((Get-FileHash -LiteralPath $r12Windows -Algorithm SHA256).Hash.ToLower() -ne '71972c3aa7f88cb625d44507ef5e3b69ca6921a21d6f2520bde0fff5119f5927') { throw 'FROZEN_WINDOWS_HELPER_CHANGED' }
if ((Get-FileHash -LiteralPath $r12Driver -Algorithm SHA256).Hash.ToLower() -ne 'ab4dfbdb2dd2b57ab0f02fd0383c11a66274e74a08746624f5f87ae8d4fdcfd3') { throw 'FROZEN_SERVER_HELPER_CHANGED' }
$r12Renewal = Join-Path $r12Root 'authority-renewal\remote-receipts\renew-20261011T194215534172Z.json'
$r12RenewalPublic = (Get-Content -LiteralPath $r12Renewal -Raw | ConvertFrom-Json).public_receipts[0]
if (-not $r12RenewalPublic.ok -or $r12RenewalPublic.approval_id -ne 'call_1KzUkF0gMn6uVpHd3QisTzXF' -or $r12RenewalPublic.expires_at_ms -ne 1791751335200) { throw 'EXACT_APPROVED_RENEWAL_REQUIRED' }
$r12Observation = (& python -B $r12Driver observe --remote-dir $r12Remote | ConvertFrom-Json)
if ($LASTEXITCODE -ne 0 -or -not $r12Observation.public_receipts[0].ok) { throw 'FRESH_SERVER_OBSERVATION_FAILED' }
$r12Args = @($r12Windows,$Phase,'--attempt=r12-rollout-20261012-0240','--operator-approved-r12',
  '--manifest-sha256=20a507338148c9d108e7ad0f75f2a8e3ac04940ca216f329c83147563c99f679',
  ('--server='+$r12Observation.receipt_path),('--server-sha256='+(Get-FileHash -LiteralPath $r12Observation.receipt_path -Algorithm SHA256).Hash.ToLower()),
  ('--renewal='+$r12Renewal),('--renewal-sha256='+(Get-FileHash -LiteralPath $r12Renewal -Algorithm SHA256).Hash.ToLower()))
& node @r12Args
if ($LASTEXITCODE -ne 0) { throw 'PHASE_REFUSED_INSPECT_EXACT_STATE_NO_REPLAY' }

# Guarded r9d → r9e transition

Completed on 12 October 2026. The exact r9e runtime is READY/OPEN on
`activation-mv53i8gp-f06eeb5b46a11d2cf7ebdc9445606937`; both shortcuts now
target r9e. The preparation sequence below is historical evidence; do not
replay the old stop/retirement against the current installation.

The single ordinary stop returned a full snapshot. The initial evidence
harness incorrectly inspected lightweight fields at its top level and saved
`packaged-stop-failure-1791799666037.json`. That failure and the original
producer `ordinary-stop-operation-result-1791799660638.json` are preserved.
The additive `confirm-stopped` operation independently read the lightweight
snapshot and canonical census from the exact original owner, verified the
producer and failure, and saved hashes of both in
`packaged-confirm-stopped-receipt-1791800009046.json`. It performed no stop.
Retirement consumed that confirmation while retaining exact owner/package,
fresh central idle, native stopped, no live Sandbox and canonical idle gates.
No cleanup/acceptance receipt was fabricated or edited.

The supported full refresh initially reported HANDOFF/VERIFYING. One explicit
completion call returned `RUNTIME_BUSY` while the existing activation worker
was finishing; the worker reached READY/OPEN two seconds later. No completion
retry or policy replacement was needed. Final observer and live renderer
receipts under this report prove readiness and five Autocad labels rendered
from fresh actual authority/registry/policy data. They do not claim a direct
screenshot of the native window.

No server mutation, package overlay, installation spoof, acceptance/proof injection,
or durable runtime-state deletion is part of these helpers.

## Verified package

- Candidate: `E:\DEV\Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-machine-folder-access-1012-r9e\win-unpacked`
- EXE SHA-256: `e7bb35634d7e765c24c156fb6a12ce9e707f3b26a4596329a2fa4dbb0e7c5f05`
- app.asar SHA-256: `0b119f1b740faa1713c9a004015c20bfee66668aa8707e1cfab67a1c07b3e901`
- Adapter SHA-256: `3147cb5d6a4f1a9ca908a240f7955b8598cdde0e4258e031a348eae77d8521d9`
- Exact source: 91 app files, 298 resources, 9 control-plane adapters.
- Isolated packaged smoke passed and production descriptor stayed stable.
- Package deltas from r9d: renderer/app.js, renderer/index.html, plus three UI
  icons regenerated through the normal build command from docs/ICON.png.
  All electron service/native code, resources, adapters and executor files match r9d.

## Old owner pin

- Host PID `3476`, start token `134362696871111330`
- Instance `dbf2536afedb8b4e554a29fc9e88cb50`
- Installation `bdf474c17024f7686b83920b289de5422d6129db4bbf8a93659eb744ccaaadba`
- Epoch `activation-mv514if9-7a4fabe0ce77708f8be03ff43a6518db`

## Sequence

All paths below are absolute. `$serverCensus` must be a newly captured read-only
server census under the r10 report directory, observed within 120 seconds.
Current-generation task/writer/action counts and current-device live
task/writer/queued/dispatch counts must be zero. Two historical quarantined
UNKNOWN actions stay preserved and are not required to be erased/settled.

```powershell
$transition = 'E:\DEV\Codex-web\.coding-tools\reports\workspace-display-20261012-r10\r9e-transition'
$serverCensus = '<fresh absolute server-work-census path under r10>'
& "$transition\invoke-packaged.ps1" -Operation stop -ServerCensusPath $serverCensus
```

Inspect the resulting `packaged-stop-receipt-*.json`. It must have `ok=true`,
`mcpRunning=false` and a safe stopped census. The actual ordinary-stop result is
also saved immediately as `ordinary-stop-operation-result-*.json` before diagnostic
confirmation. On a stop failure, observe the existing owner/fence; do not bypass
cleanup or substitute another operation.

Refresh central idle evidence after stop, then:

```powershell
$stopReceipt = '<exact absolute packaged-stop-receipt path>'
$serverCensus = '<fresh absolute server-work-census path under r10>'
& "$transition\invoke-packaged.ps1" -Operation retire -ServerCensusPath $serverCensus -StopReceiptPath $stopReceipt
```

Retirement requires the confirmed stop receipt within 15 minutes, exact owner,
nativeAlive/mcpRunning false, no Sandbox/daemon/vmmemWSB/wxc-exec process, and
supported idle ledger census with historical acceptance preserved. It stops exact
UI recovery/host/supervisor ownership and does not replay runtime.stop.

```powershell
$retirement = '<exact absolute packaged-retire-receipt path>'
& "$transition\launch-r9e.ps1" -Operation InstallSupervisor -RetirementReceiptPath $retirement -Apply
$install = '<exact absolute install_r9e_supervisor receipt path>'
& "$transition\launch-r9e.ps1" -Operation LaunchUi -RetirementReceiptPath $retirement -InstallReceiptPath $install -Apply
& "$transition\invoke-packaged.ps1" -Operation status
& "$transition\invoke-packaged.ps1" -Operation refresh
```

Use the new exact epoch from the refresh result; if activation requires the
supported completion observation, call `complete -Epoch <new epoch>`.
Renew existing policies through their supported API only after current exact
workspace/generation identity has been inspected:

```powershell
& "$transition\invoke-packaged.ps1" -Operation metadata
& "$transition\invoke-packaged.ps1" -Operation files
& "$transition\invoke-packaged.ps1" -Operation exec
& "$transition\invoke-packaged.ps1" -Operation observe -Epoch '<new exact activation epoch>'
$readyReceipt = '<exact absolute final-machine-observation path>'
& "$transition\update-coding-tools-shortcuts-r9e.ps1" -TargetPath 'E:\DEV\Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-machine-folder-access-1012-r9e\win-unpacked\Coding Tools MCP.exe' -ExpectedEpoch '<new exact activation epoch>' -ReadyReceiptPath $readyReceipt -Apply
```

Shortcut application requires an exact READY/OPEN observer receipt observed within
120 seconds, verified r9e package hashes and both original r9d shortcut hashes.
The preparatory dry-run created guarded backups under this report; it changed
neither shortcut. Preserved properties are checked after each saved link.

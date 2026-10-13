# Prepared r6 → r7 local transition

Prepared only. Root must first close the original r6 task, release its writer,
verify settled actions and authorize this transition. Historical acceptance is
preserved. The workspace generation remains
`generation_a420c8bfcfcb4e42b5bb7fc5e5cec097`.

## Exact candidates

- r6: `E:\DEV\Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-machine-exec-lifecycle-1012-r6\win-unpacked`
- r7: `E:\DEV\Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-machine-exec-lifecycle-1012-r7\win-unpacked`
- EXE SHA for both: `a18ba16a640c30ad67758d6ba19aaf7044d947cea2f8026796b6e88f930243a8`
- app.asar SHA for both: `69bac603b0dab1ad27f86fa114da140b059a93c695a4b7dfdbe24b53b3c007ae`
- r7 adapter SHA: `3147cb5d6a4f1a9ca908a240f7955b8598cdde0e4258e031a348eae77d8521d9`

EXE/app.asar hashes alone do not distinguish these packages. The scripts also
verify candidate paths and the packaged adapter hash.

## Root command sequence after authorization

Use the selected candidate executable with `ELECTRON_RUN_AS_NODE=1` for Node
observers/operations, then restore that environment variable. A GUI-subsystem
executable must be waited on: use `Start-Process -WindowStyle Hidden -Wait
-PassThru` with separate unique stdout/stderr files. Do not launch a shortcut.

1. Run the existing read-only r6 observer for epoch
   `activation-mv4u5k6v-cfeabc74ae10012ae61eab8d4c87e8b4`; confirm idle after the
   original task closed. Its receipt is historical r6 evidence.
2. Run `packaged-operations.cjs retire <r6-directory>` using the r6 EXE.
   The prepared copy requires exact r6 Host PID `25028`, instance
   `8b8992a71407cd61f37317ae0b438cb4`, installation and READY epoch, an independent
   quiescent census, exact UI/process identity, then the reviewed stop/fence.
   Read the unique `packaged-retire-receipt-*.json`; require `ok=true`, exact host
   terminated/exited and stopped census safe.
3. With that exact receipt, run:

   ```powershell
   .\launch-r7.ps1 -Operation InstallSupervisor -Apply -RetirementReceiptPath <retirement-receipt>
   ```

   This invokes the shipped r7 supervisor Install flow, validates the resulting
   manifest and preserves its unique `install_r7_supervisor-*.json` receipt.
4. Run:

   ```powershell
   .\launch-r7.ps1 -Operation LaunchUi -Apply -RetirementReceiptPath <retirement-receipt> -InstallReceiptPath <install-receipt>
   ```

   UI launch is hidden. Its process ID proves launch only. Obtain fresh r7
   packaged status before relying on it.
5. Using the r7 EXE, run `packaged-operations.cjs status <r7-directory>`, then
   `packaged-operations.cjs refresh <r7-directory>`. Read the new epoch from its
   receipt; do not reuse the r6 epoch. If connector freshness is pending, obtain
   the supported current-process discovery/compatibility bootstrap and ACK.
   Run `complete <r7-directory> <new-epoch>` only for that exact eligible epoch.
6. Run `status <r7-directory>`. Require READY, admission open, current source
   receipts and fresh central authority. Existing policies are inspected first;
   the optional `metadata`, `files`, `exec` operations accept only the exact
   existing generation and are used only to resolve a demonstrated policy
   mismatch. No workspace replacement or pilot transfer is in this script.
7. Using the r7 EXE, run
   `observe-r7-machine.cjs <r7-directory> <new-epoch>`. This observer verifies
   exact package/adapter, current Host/epoch, read-only canonical ledger, idle
   resources and preserved acceptance. It writes a unique receipt in this
   transition directory.
8. Within 120 seconds of that successful READY/OPEN observer receipt, run:

   ```powershell
   .\update-coding-tools-shortcuts-r7.ps1 -Apply -TargetPath '<r7-directory>\Coding Tools MCP.exe' -ExpectedEpoch <new-epoch> -ReadyReceiptPath <observer-receipt>
   ```

   Only the two Coding Tools MCP shortcuts are changed. Current r6 links are
   hash-guarded and backed up here. Other link properties and the legacy Trợ lý
   Web MCP link remain intact. Re-read both shortcuts after applying.
9. Root runs a new real shared-MCP cold command to prove r7 behavior, observes
   its original Job/receipt, closes the task and releases its writer. No replay
   or reconstructed success is part of this preparation.

All prepared scripts are checked for syntax only. Preparation does not run
retirement, service installation, UI launch, activation, permission changes or
shortcut updates. Existing r6 evidence is not overwritten.

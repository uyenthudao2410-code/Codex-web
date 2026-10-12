# Prepared r10 native identity and local phase observation

This packet is prepared and statically checked only. The helper main, runtime IPC and host process observation have not been run by the preparing worker. It does not activate a runtime, execute a canary, change authority, probe the backend, stop a process, clean a VM or operate a service.

## Reviewed target

- Repository: `E:\Github\Tools-Codex-web`, dirty `main` at `2c554f59cb7b8ffc86ce5e0e28076c792777642f`.
- Profile: `C:\Users\daoth\AppData\Roaming\web-mcp-assistant`.
- Candidate: `dist/windows-candidate-mxc-wsb-cbe1774-setup-exec-contract-1011-r10/win-unpacked`.
- Executable SHA256: `6e34a6705a647aaddda0d24f2152904006a504ab7a29ba516b686c6de29ef09f`.
- `app.asar` SHA256: `c39a614d40f551f0ddef4e579bcd8ef5d8d3ad365bbd43e22693df8c1f9672e9`.
- Parity receipt: `../candidate-parity-20261011T115907669Z.json`, SHA256 `c9f6fe1313b6004519a61bebf3f8f173a74cfd1d563bef48fce87908ed72f57c`.

The helper verifies these pins, the four packaged IPC module hashes, packaged runtime paths, installation descriptor, and Recovery Host owner PID plus process creation token. It then uses the existing packaged `RecoveryIpcClient.identityObservation()` read API. It accepts only fresh, ready, current MCP identity matching the reviewed r10 epoch and host instance. The prior r9 epoch is explicitly rejected.

## Root invocation after r10 activation

First review `native-observer-manifest.json` and the hashes of its files. Obtain the expected epoch, Recovery Host instance and installation ID from a fresh successful r10 activation/descriptor receipt. Never guess these values or copy the predecessor r9 identity. This helper must run through the pinned packaged executable with `ELECTRON_RUN_AS_NODE=1`; ordinary `node.exe` cannot supply the packaged ASAR/runtime context.

Replace the three placeholders below with the reviewed public identity values. Choose `cold` before the cold canary or `warm` before the warm canary. `observe` collects neutral observation without making a phase assertion.

```powershell
$r10ObserverExe = 'E:\Github\Tools-Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-setup-exec-contract-1011-r10\win-unpacked\Coding Tools MCP.exe'
$r10ObserverFile = 'E:\Github\Tools-Codex-web\.coding-tools\reports\unified-setup-20261011\executor-repair\candidate-r10\mcp-acceptance\observe-r10-native-local.cjs'
$r10ExpectedEpoch = '<fresh r10 activation epoch>'
$r10ExpectedHost = '<fresh 32-character lowercase hex Recovery Host instance>'
$r10ExpectedInstallation = '<fresh 64-character lowercase hex installation ID>'
$r10ObserverPhase = 'cold'
$r10PreviousRunAsNode = [Environment]::GetEnvironmentVariable('ELECTRON_RUN_AS_NODE', 'Process')
try {
    [Environment]::SetEnvironmentVariable('ELECTRON_RUN_AS_NODE', '1', 'Process')
    & $r10ObserverExe $r10ObserverFile "--expected-epoch=$r10ExpectedEpoch" "--expected-host-instance=$r10ExpectedHost" "--expected-installation-id=$r10ExpectedInstallation" "--phase=$r10ObserverPhase"
    $r10ObserverExitCode = $LASTEXITCODE
} finally {
    [Environment]::SetEnvironmentVariable('ELECTRON_RUN_AS_NODE', $r10PreviousRunAsNode, 'Process')
}
```

The helper requires exactly those four arguments. Every invocation writes a new `native-local-<UTC>-<random>.json` using exclusive creation and prints its path and SHA256. Success emits only selected public identity and host metadata. Failure emits a sanitized code and an immutable failure receipt; it does not print descriptor authentication, nonce, environment, raw error or command output. Exit code zero alone does not prove a cold or warm phase: review the receipt and require `ok=true` and `requested_phase_observed=true` for the selected phase.

## Local observation and proof limits

The fixed read-only PowerShell query lists names, PIDs and process creation tokens for `WindowsSandbox*`, `vmmemWindowsSandbox` and `wxc-windows-sandbox-daemon`. Creation tokens can be null if the OS denies access. The helper verifies the four packaged backend file hashes from the pinned parity receipt. It checks only existence and regular-file status of `%TEMP%\wxc-wsb\state-aware\daemon.json`; it never opens or hashes that record, which contains a private nonce.

- A cold hint requires no matching Sandbox process, no daemon process and no daemon record.
- A warm hint requires a matching Sandbox process, exactly one daemon process and a regular daemon record.
- These are host-wide observation hints. They do not establish VM ownership, a manager lease, reuse of a particular VM, successful execution or cleanup.
- A failed phase hint calls for root diagnosis. It does not authorize this helper to stop processes or clean a VM.

## Handoff to the central canary

Retain and review the emitted immutable observation. Put its exact SHA256 into `native_observation_sha256` in the root-reviewed canary pin document. Copy the following public fields from the same receipt:

| Observation identity field | Canary pin field |
| --- | --- |
| `mcp_process_instance_id` | `process_instance_id` |
| `mcp_server_instance_id` | `server_instance_id` |
| `activation_epoch_id` | `activation_epoch_id` |
| `tool_contract_sha256` | `native_contract_sha256` |

Use a fresh observation and separate reviewed pin document for warm. Follow `README-v2.md` and the immutable v2 canary packet for central preflight, its single reviewed execution, and terminal task cleanup. Native Job correlation with `verify-r10-native-job.py` remains required before acceptance. Neither the phase label nor the local observation replaces that correlation or proves timeout cleanup.

## Existing static evidence

`node --check observe-r10-native-local.cjs` passed. `check-native-observer-static.cjs` passed 15 pure validation cases, including stale/future identity, wrong host/epoch, readiness, invalid IDs/hash, phase arguments, selected-field filtering and static assertions for read-only IPC/exclusive evidence creation. `native-observer-static-proof.jsonl` states `helper_main_invoked=false`, `runtime_ipc_called=false`, `host_processes_observed=false` and `live_operations=false`. These checks do not prove that the live package, IPC or VM observation will succeed.

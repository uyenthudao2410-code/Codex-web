# Additive r10 observer v2: verify regular source bytes against packaged parity

Primary helper sealed at `2026-10-11T13:03:09Z`, SHA256 `752e72712de32c1e27570916db6ae4a63d03fd1915ea04d50a3fd960c46f5e06`.

## Corrected observation boundary

Root's v1 invocation produced `native-local-2026-10-11T12-57-35-829Z-4e0193a7.json` with `ENOENT`. V1's first virtual ASAR subfile operation is a raw filesystem hash of `app.asar/electron/services/runtimePaths.js`, before descriptor access or IPC. The receipt has no stage, so it cannot positively locate the failed read. Root separately reported that the existing packaged observer CLI succeeded; this packet does not infer that packaged `require()` lacks ASAR support.

V2 removes the virtual ASAR filesystem hash boundary. It verifies regular repository transport module bytes against both fixed SHA256 pins and the immutable candidate parity manifest before importing them. All nine transitive modules were verified: `runtimePaths`, `runtimeIdentity`, `recoveryIpc`, `recoveryHostLauncher`, `processIdentity`, `pathSemantics`, `deviceIdentity`, `jsonStore` and `commandRunner`. The pinned archive, executable, parity receipt and source-freeze receipt remain required.

This uses the same byte-verified transport approach as the successful activation helper. `createRuntimePaths()` still receives the exact candidate `app.asar`, candidate resource root, candidate executable, fixed profile and `runtimeMode: 'packaged'`. Installation, current Recovery Host descriptor, owner process identity, fresh activation epoch and MCP identity remain checked. No development runtime adapter or development installation identity is selected.

## Root invocation

Executable:

`E:\Github\Tools-Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-setup-exec-contract-1011-r10\win-unpacked\Coding Tools MCP.exe`

Helper:

`E:\Github\Tools-Codex-web\.coding-tools\reports\unified-setup-20261011\executor-repair\candidate-r10\mcp-acceptance\observe-r10-native-local-v2.cjs`

Run the executable with a copied child environment containing `ELECTRON_RUN_AS_NODE=1`, working directory `E:\Github\Tools-Codex-web`, and exactly these four arguments after the helper path:

```text
--expected-epoch=<fresh reviewed r10 activation epoch>
--expected-host-instance=<fresh reviewed 32-character lowercase hex host instance>
--expected-installation-id=<fresh reviewed 64-character lowercase hex installation ID>
--phase=cold
```

Use the complete values from the fresh successful r10 activation/descriptor receipt. The root-provided epoch at sealing was `activation-mv3tn5og-8def0602e3d318e0c42052c6eefc00ba`; the helper does not hardcode it as proof of freshness. For warm, obtain a fresh local observation and use `--phase=warm`. `--phase=observe` collects neutral metadata without claiming cold or warm.

Use Python `subprocess.run()` or another existing root wrapper that captures the GUI executable's stdout. Direct PowerShell `&` did not expose stdout in the root's v1 invocation, although the helper created its receipt. Every v2 attempt creates a new immutable `native-local-<UTC>-<random>.json` with exclusive creation. Review the emitted receipt path/hash and JSON, and require exit code zero, `ok=true` and `requested_phase_observed=true` for the chosen phase. Failures include a fixed sanitized `boundary` and error code, without raw paths from an exception, authentication, nonce, environment or stderr.

## Handoff and limits

The receipt's `transport` records the verified module closure and `virtual_asar_file_read=false`. Its runtime paths and descriptor refer to the packaged candidate. Use the receipt hash as `native_observation_sha256` in the reviewed central canary pins. Map `mcp_process_instance_id` to `process_instance_id`, `mcp_server_instance_id` to `server_instance_id`, `activation_epoch_id` unchanged, and `tool_contract_sha256` to `native_contract_sha256`.

The fixed host query reads only selected process names, PIDs and creation tokens. The daemon record is checked by `lstat` only; its nonce is never read or hashed. Cold/warm observations are host-wide hints and do not prove VM ownership, manager lease, reuse, execution or cleanup. Native Job correlation remains mandatory before acceptance. Follow the immutable `README-v2.md` central canary procedure for its single reviewed cold/warm attempts and terminal task cleanup.

Worker proof is preparation only: syntax passed, 15 pure validation cases passed, and nine actual transport file hashes matched the pinned packaged parity. An initial checker run failed because its literal hash-string assertion missed a quote; only that new checker was corrected, and the final checker passed. Worker did not invoke helper main, runtime IPC, host observation, activation, exec, policy, probe, stop or service operations. V1 helper, v1 manifest, v1 failure receipt and central canary packets remain preserved.

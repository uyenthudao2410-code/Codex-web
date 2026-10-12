# Additive r10 observer v3: read raw archive with Electron original-fs

Primary helper sealed at `2026-10-11T13:05:44.401Z`, SHA256 `1800ec6dfd07532e39ca6b05b3cd4c98561cb8cd8da3c1d119beb82e5314eb29`.

## Diagnosed and corrected read boundary

Root's v2 attempt failed at `IMMUTABLE_PACKAGE_PROVENANCE` with `ENOENT`, retained in `native-local-2026-10-11T13-03-38-830Z-5b12d99e.json`. Root's separate read-only `observer-provenance-diagnosis.json` confirmed that `fs.readFileSync()` of the raw `app.asar` root failed inside Electron, while executable, parity, source freeze and Git checks passed. The existing packaged observer CLI also succeeded. These observations identify a raw archive filesystem boundary; they do not show a missing package or a failure of packaged `require()`.

V3 makes one additional transport correction to v2: only hashing the exact pinned raw archive uses `require('original-fs').readFileSync(archive)`. This require is lazy and is not invoked by static checks. Normal filesystem operations remain in use for source modules, public evidence, backend files and daemon-record existence. It never reads the daemon nonce or exports Recovery descriptor authentication.

The remaining v2 guards are preserved: the actual observer executable is the exact packaged r10 executable; archive/executable/parity/source-freeze hashes are pinned; all nine regular source transport module hashes must equal the immutable packaged parity manifest; and runtime paths explicitly select the packaged candidate and fixed profile. The descriptor, installation ID, Recovery Host owner PID/creation token, fresh epoch and current MCP identity must match. This is a byte-verified packaged transport observation, with no development runtime selection.

## Root invocation

Executable:

`E:\Github\Tools-Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-setup-exec-contract-1011-r10\win-unpacked\Coding Tools MCP.exe`

Helper:

`E:\Github\Tools-Codex-web\.coding-tools\reports\unified-setup-20261011\executor-repair\candidate-r10\mcp-acceptance\observe-r10-native-local-v3.cjs`

Use the root's existing Python subprocess wrapper to capture stdout from the GUI executable. Copy the environment and set `ELECTRON_RUN_AS_NODE=1` in that child environment only. Use working directory `E:\Github\Tools-Codex-web`. Pass exactly these four arguments after the helper path, using complete reviewed values from a fresh successful r10 activation/descriptor receipt:

```text
--expected-epoch=<fresh reviewed r10 activation epoch>
--expected-host-instance=<fresh reviewed 32-character lowercase hex host instance>
--expected-installation-id=<fresh reviewed 64-character lowercase hex installation ID>
--phase=cold
```

The epoch supplied by root at sealing was `activation-mv3tn5og-8def0602e3d318e0c42052c6eefc00ba`; the helper still verifies the live identity and does not hardcode that value as evidence. Use a fresh separate observation for `--phase=warm`. `--phase=observe` makes no cold/warm assertion. Direct PowerShell `&` did not expose stdout on the first attempt, so root should retain the captured JSON and review its emitted immutable receipt.

Require exit code zero, `ok=true`, and `requested_phase_observed=true` for the selected cold/warm phase. A failure records a fixed sanitized `boundary` and error code. It does not print raw exceptions, descriptor tokens, nonce, environment or stderr. Each invocation exclusively creates a new `native-local-<UTC>-<random>.json`; prior receipts are preserved.

## Acceptance handoff and proof limits

Use the current receipt SHA256 as `native_observation_sha256` in the reviewed central canary pins. Copy `mcp_process_instance_id` to `process_instance_id`, `mcp_server_instance_id` to `server_instance_id`, `activation_epoch_id` unchanged, and `tool_contract_sha256` to `native_contract_sha256` from that same receipt.

Cold/warm checks observe host-wide Sandbox/daemon process metadata and daemon-record existence only. They do not prove VM ownership, manager lease, reuse, successful execution or cleanup. Native Job correlation remains mandatory before canary acceptance. Follow `README-v2.md` for the central preflight, single reviewed cold/warm execution and terminal task cleanup. A phase observation or successful canary does not prove timeout cleanup.

Worker proof is static only: syntax passed; 15 pure validation cases passed; nine actual source transport hashes matched pinned package entries; static assertions confirmed the exact archive-only original-fs read and the exact packaged executable guard. The worker has not invoked v3 main, IPC or host observation. Root is responsible for the live result. Original v1/v2 helpers, manifests, static evidence, failure receipts and canary packets remain preserved. No source/package edits, service operations, authority changes, execution, cleanup, commit or push were performed by the worker.

# Authorized parallel native-first transition

Prepared for the existing r9e Windows owner and the final `parallel-native-1012-r1` candidate. This additive plan supersedes the earlier exclusive workspace handoff proposal; historical receipts and UNKNOWN actions remain unchanged.

## Required proof

- Final candidate exact source/package parity and isolated packaged smoke must agree on EXE/ASAR hashes. Runtime helpers independently recheck current source and packaged resources.
- A fresh Ubuntu receipt must contain `ok`, `fenced`, `live_work_idle`, and `historical_unknown_preserved` set to true, an `observed_at_ms` no older than 120 seconds, and both exact `targets` below. Root coordinates the supported deployment fence and authority grants.
- The old descriptor must still be PID `38436`, start token `134362736855547600`, instance `b81bbad41b65c71f1bb4f21b0bdb8d10`, installation `2e511714fe3f1f64484f11778e1fe2a5c46bb5d5873f02047144b417f7996d0a`.
- Local canonical Backup-API/query-only census must have no active work. Historical pending acceptance is retained. Unknown remote historical file reads do not become rejected, completed or retried merely to satisfy this handoff.

## Exact targets

| Root | Workspace | Generation |
|---|---|---|
| `E:\DEV\Codex-web` | `workspace_f93b5bac9dc74fae9cea66f44c4ebc94` | `generation_a420c8bfcfcb4e42b5bb7fc5e5cec097` |
| `E:\DEV\Autocad` | `workspace_bc86004be2684b958ab7a9a6f9530cd7` | `generation_03f9c04f1b14414fa4bfa7d91cc8ea7a` |

## Operations

Run `packaged-operations.cjs` using the exact selected EXE with `ELECTRON_RUN_AS_NODE=1` and absolute `--parity-proof` and `--smoke-proof` paths. Mutating modes additionally require `--apply`.

1. `stop` under r9e requires `--server-fence`. It performs exactly one supported ordinary stop and saves `ordinary-stop-result` immediately. If the response is uncertain, use `stopped-observation`; never repeat the original stop.
2. `retire` under r9e requires `--stop-receipt` referring to that producer receipt. Recheck exact stopped census, suppress the exact supervisor/UI, wait for the exact owned UI to exit, then terminate only the verified old Recovery Host generation. Registry, policy, node configuration and durable history fingerprints must remain unchanged.
3. Run `install-launch.ps1 -Operation InstallSupervisor -Apply` with parity, smoke and exact retirement receipts. It installs the final candidate's supported Recovery Supervisor only after the pinned old host exited.
4. Run `install-launch.ps1 -Operation LaunchUi -Apply` with the same receipts and the new supervisor installation receipt. Launch is not a READY claim.
5. Run `refresh` under the final candidate. It uses supported full-clean refresh, preserving historical acceptance, and creates a new durable epoch. If connector acknowledgement is pending, capture it and use exact `complete --epoch <id>` when its supported bootstrap is eligible.
6. Coordinate fresh additive grants on Ubuntu. Run `policies` under the final candidate only when both targets' authority is current. Per-target native prefix approvals are retained only from the same ID/generation. Policy synchronization starts no VM.
7. Verify both exact targets independently, fresh read/edit/exec receipts, actual terminal native Jobs and current UI/Recovery/MCP source receipts. Selection is the default destination for new tasks; existing tasks retain their bound targets. Shared Windows Sandbox execution is serialized by the executor lane.
8. Capture final local and server census, live READY/OPEN identity and package hashes. Update shortcuts only with fresh verified readiness and guarded original shortcut identities.

No production operation was performed while preparing these helpers. Root must explicitly announce final package and server coordination ready before execution.

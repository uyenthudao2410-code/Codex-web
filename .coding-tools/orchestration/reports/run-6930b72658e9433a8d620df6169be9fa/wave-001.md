# Orchestration Wave 1

- Run: `6930b72658e9433a8d620df6169be9fa`
- Wave: `e03a9f98afcc44c1bca2504c304931ad`
- Objective: Diagnose exactly one genuine independently fixable safety bug in crates/webcodex-core/src/shell_protocol.rs around process_uses_shell_command_mode / validate_process_argv. Do not mutate source. Verify whether model-facing run_process can bypass the explicit 'no shell command modes' contract through real command-execution modes that the current detector misses, especially cmd.exe /K and PowerShell -EncodedCommand/-EncodedCommand variants. Inspect direct tests in this file and any maintained comments only. Require a concrete reachable argv that current code accepts but the shell executable would execute as command text, and a focused cargo test -p webcodex-core oracle. Confirm the file is clean relative to HEAD. If these forms are intentionally allowed or not actually command modes, reject the candidate instead of inventing one. Keep P5 closed.
- Mode: `mcp_only`
- Base HEAD: `b7af2598297870e816dd131b0f73e0f77d7608d5`
- Worktree fingerprint: `95a5f650b31f8bace44966d9439235ec229f09129ad06a72c643c15039e13359`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 18552 | 2026-08-18T23:41:55.406Z | run_started |  | PREFLIGHT |  |
| 18553 | 2026-08-18T23:42:00.615Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 18554 | 2026-08-18T23:43:29.993Z | managed_process_admitted |  |  | owner=default |
| 18555 | 2026-08-18T23:43:30.218Z | managed_process_started |  |  | owner=default |
| 18556 | 2026-08-18T23:43:30.593Z | managed_process_terminal |  |  | owner=default |
| 18557 | 2026-08-18T23:43:47.771Z | managed_process_admitted |  |  | owner=default |
| 18558 | 2026-08-18T23:43:47.987Z | managed_process_started |  |  | owner=default |
| 18559 | 2026-08-18T23:43:48.323Z | managed_process_terminal |  |  | owner=default |
| 18560 | 2026-08-18T23:44:17.464Z | managed_process_admitted |  |  | owner=default |
| 18561 | 2026-08-18T23:44:17.743Z | managed_process_started |  |  | owner=default |
| 18562 | 2026-08-18T23:44:18.119Z | managed_process_terminal |  |  | owner=default |
| 18563 | 2026-08-18T23:44:55.674Z | state_transition | PREFLIGHT | ABORTED | reason=Read-only diagnosis proved a genuine structured-process safety defect on a clean file. process_uses_shell_command_mode blocks cmd /C and PowerShell -Command but misses cmd /K and PowerShell -EncodedCommand, while host CLI help confirms both execute command text. No source mutation occurred; terminalizing diagnostic lineage before representative implementation. |
| 18564 | 2026-08-18T23:44:55.980Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| - | - | - | - | - | - |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `13`
- Chain head: `1888f99ce21165c4b9ba3c423803f237ab5a4818fb8b99d6fd7618bcac1e8cbe`

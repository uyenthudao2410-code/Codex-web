# Orchestration Wave 1

- Run: `b0b0cb59d0924aa3833d2b4b72f64803`
- Wave: `27fdbb5f13cc4cc8a867c3ae1d223e42`
- Objective: Wave A only: selectively adapt upstream WebCodex #113 commit 2a77ba69be09eb4902b41939b619d18539a1bb8b and only the missing low-level lifecycle invariants from #112 commit ea97ca7d977c87bfc2566ec563655a3c8abcc240 into the current Codex-web Rust execution substrate. Preserve existing EOCL, Recovery Host, public smart-v3 tool count=8, current worktree review behavior, and all unrelated concurrent work. Required behavior: structured child stdout/stderr are continuously drained immediately after successful spawn even when no Server/model log consumer exists, retained output remains bounded and UTF-8 safe, stop/timeout/shutdown reap the same execution without redispatch, pre-spawn rejection may be NotStarted, but after successful spawn any unproven interruption/lost-record/shutdown/stop race must never reuse NotStarted and must be OutcomeUnknown where applicable; observed terminal timeout is TimedOut and observed terminal completion/nonzero exit is Completed. Do not touch P5 epoch state. Do not implement Wave B/C/D in this run. Localize exact current source/tests and return the smallest coherent implementation plan and focused oracle.
- Objective revision: `1`
- Objective SHA-256: `4a9ec4772d6510b4eb7a83c5dd98b17427715b73febc6f34fb0a32e3491bac3c`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `3538c761f174f8f609090b31ef368c064df0a5fc`
- Worktree fingerprint: `f902fff278e1e46344ba58044ba0bcd752b1642bc255c46609185d311c45f7bf`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 26990 | 2026-08-22T09:58:26.270Z | run_started |  | PREFLIGHT |  |
| 26991 | 2026-08-22T09:58:57.120Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 26992 | 2026-08-22T09:59:50.438Z | managed_process_admitted |  |  | owner=default |
| 26993 | 2026-08-22T09:59:50.682Z | managed_process_started |  |  | owner=default |
| 26994 | 2026-08-22T09:59:51.539Z | managed_process_terminal |  |  | owner=default |
| 26995 | 2026-08-22T10:00:00.416Z | managed_process_admitted |  |  | owner=default |
| 26996 | 2026-08-22T10:00:00.685Z | managed_process_started |  |  | owner=default |
| 26997 | 2026-08-22T10:00:01.516Z | managed_process_terminal |  |  | owner=default |
| 26998 | 2026-08-22T10:01:16.698Z | managed_process_admitted |  |  | owner=default |
| 26999 | 2026-08-22T10:01:16.907Z | managed_process_started |  |  | owner=default |
| 27000 | 2026-08-22T10:01:17.519Z | managed_process_terminal |  |  | owner=default |
| 27001 | 2026-08-22T10:02:05.487Z | managed_process_admitted |  |  | owner=default |
| 27002 | 2026-08-22T10:02:05.806Z | managed_process_started |  |  | owner=default |
| 27003 | 2026-08-22T10:02:06.497Z | managed_process_terminal |  |  | owner=default |
| 27004 | 2026-08-22T10:02:14.262Z | managed_process_admitted |  |  | owner=default |
| 27005 | 2026-08-22T10:02:14.480Z | managed_process_started |  |  | owner=default |
| 27006 | 2026-08-22T10:02:14.830Z | managed_process_terminal |  |  | owner=default |
| 27007 | 2026-08-22T10:02:20.288Z | managed_process_admitted |  |  | owner=default |
| 27008 | 2026-08-22T10:02:20.487Z | managed_process_started |  |  | owner=default |
| 27009 | 2026-08-22T10:02:20.815Z | managed_process_terminal |  |  | owner=default |
| 27010 | 2026-08-22T10:02:28.390Z | managed_process_admitted |  |  | owner=default |
| 27011 | 2026-08-22T10:02:28.771Z | managed_process_started |  |  | owner=default |
| 27012 | 2026-08-22T10:02:29.122Z | managed_process_terminal |  |  | owner=default |
| 27013 | 2026-08-22T10:02:36.472Z | managed_process_admitted |  |  | owner=default |
| 27014 | 2026-08-22T10:02:36.673Z | managed_process_started |  |  | owner=default |
| 27015 | 2026-08-22T10:02:37.039Z | managed_process_terminal |  |  | owner=default |
| 27016 | 2026-08-22T10:02:43.801Z | managed_process_admitted |  |  | owner=default |
| 27017 | 2026-08-22T10:02:44.013Z | managed_process_started |  |  | owner=default |
| 27018 | 2026-08-22T10:02:44.454Z | managed_process_terminal |  |  | owner=default |
| 27019 | 2026-08-22T10:03:00.595Z | managed_process_admitted |  |  | owner=default |
| 27020 | 2026-08-22T10:03:00.806Z | managed_process_started |  |  | owner=default |
| 27021 | 2026-08-22T10:03:01.147Z | managed_process_terminal |  |  | owner=default |
| 27022 | 2026-08-22T10:03:07.456Z | managed_process_admitted |  |  | owner=default |
| 27023 | 2026-08-22T10:03:07.673Z | managed_process_started |  |  | owner=default |
| 27024 | 2026-08-22T10:03:08.197Z | managed_process_terminal |  |  | owner=default |
| 27039 | 2026-08-22T10:06:25.214Z | state_transition | PREFLIGHT | ABORTED | reason=Terminalize the clean prepare-only Wave A lineage before repairing the newly observed cross-session task/run objective-binding regression. This run has zero source mutations and zero proofs; a fresh Wave A lineage will be opened after the provenance control plane is fixed and proven. |
| 27040 | 2026-08-22T10:06:25.569Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

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
- Events checked: `37`
- Chain head: `eb7c69c3a3d91406fdbe948dd84d80569c071fcce69820d984beed9edfe3ea1b`

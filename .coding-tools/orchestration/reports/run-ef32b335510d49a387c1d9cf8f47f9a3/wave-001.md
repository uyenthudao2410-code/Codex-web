# Orchestration Wave 1

- Run: `ef32b335510d49a387c1d9cf8f47f9a3`
- Wave: `9f856e37c5094c3aa42df19317c19540`
- Objective: Pre-P3 treatment-mechanism and cohort eligibility audit after frozen manifest commit bc17700e. Read only. Identify the exact source/runtime control that causes real LOCAL_FIRST_V1 versus SERVER_FIRST_DETERMINISTIC_V1 compute placement, including server_compute/local fallback/capacity behavior and how to invoke it without changing model routing. Identify existing real project backlog or verification tasks that are genuinely representative, portable, exact-source reproducible, no GUI/device/secret affinity, strong-oracle, and safe-fallback eligible. Do not enroll, execute, tag, or inspect any treatment outcome yet. Do not modify files.
- Mode: `mcp_only`
- Base HEAD: `bc17700e475ce74c96a9547117aade58823f0811`
- Worktree fingerprint: `e8c159440c324c40eb2c8f2f3d85416a377d64be6d5c466ea3d0bd1089609264`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 15791 | 2026-08-17T20:21:28.564Z | run_started |  | PREFLIGHT |  |
| 15792 | 2026-08-17T20:21:33.724Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 15793 | 2026-08-17T20:22:37.686Z | managed_process_admitted |  |  | owner=default |
| 15794 | 2026-08-17T20:22:37.930Z | managed_process_started |  |  | owner=default |
| 15795 | 2026-08-17T20:22:38.286Z | managed_process_terminal |  |  | owner=default |
| 15796 | 2026-08-17T20:22:54.139Z | managed_process_admitted |  |  | owner=default |
| 15797 | 2026-08-17T20:22:54.379Z | managed_process_started |  |  | owner=default |
| 15798 | 2026-08-17T20:22:55.027Z | managed_process_terminal |  |  | owner=default |
| 15799 | 2026-08-17T20:23:11.191Z | managed_process_admitted |  |  | owner=default |
| 15800 | 2026-08-17T20:23:11.439Z | managed_process_started |  |  | owner=default |
| 15801 | 2026-08-17T20:23:11.953Z | managed_process_terminal |  |  | owner=default |
| 15802 | 2026-08-17T20:23:41.081Z | managed_process_admitted |  |  | owner=default |
| 15803 | 2026-08-17T20:23:41.313Z | managed_process_started |  |  | owner=default |
| 15804 | 2026-08-17T20:23:41.844Z | managed_process_terminal |  |  | owner=default |
| 15805 | 2026-08-17T20:24:24.683Z | managed_process_admitted |  |  | owner=default |
| 15806 | 2026-08-17T20:24:24.919Z | managed_process_started |  |  | owner=default |
| 15807 | 2026-08-17T20:24:25.336Z | managed_process_terminal |  |  | owner=default |
| 15808 | 2026-08-17T20:24:54.269Z | managed_process_admitted |  |  | owner=default |
| 15809 | 2026-08-17T20:24:54.536Z | managed_process_started |  |  | owner=default |
| 15810 | 2026-08-17T20:24:54.900Z | managed_process_terminal |  |  | owner=default |
| 15811 | 2026-08-17T20:25:20.956Z | managed_process_admitted |  |  | owner=default |
| 15812 | 2026-08-17T20:25:21.385Z | managed_process_started |  |  | owner=default |
| 15813 | 2026-08-17T20:25:21.769Z | managed_process_terminal |  |  | owner=default |
| 15814 | 2026-08-17T20:26:03.811Z | managed_process_admitted |  |  | owner=default |
| 15815 | 2026-08-17T20:26:04.051Z | managed_process_started |  |  | owner=default |
| 15816 | 2026-08-17T20:26:04.605Z | managed_process_terminal |  |  | owner=default |
| 15817 | 2026-08-17T20:31:38.625Z | managed_process_admitted |  |  | owner=default |
| 15818 | 2026-08-17T20:31:38.871Z | managed_process_started |  |  | owner=default |
| 15819 | 2026-08-17T20:31:39.322Z | managed_process_terminal |  |  | owner=default |
| 15820 | 2026-08-17T20:31:51.491Z | managed_process_admitted |  |  | owner=default |
| 15821 | 2026-08-17T20:31:51.720Z | managed_process_started |  |  | owner=default |
| 15822 | 2026-08-17T20:31:52.771Z | managed_process_terminal |  |  | owner=default |
| 15823 | 2026-08-17T20:32:04.956Z | managed_process_admitted |  |  | owner=default |
| 15824 | 2026-08-17T20:32:05.238Z | managed_process_started |  |  | owner=default |
| 15825 | 2026-08-17T20:32:05.953Z | managed_process_terminal |  |  | owner=default |
| 15826 | 2026-08-17T20:32:23.934Z | managed_process_admitted |  |  | owner=default |
| 15827 | 2026-08-17T20:32:24.203Z | managed_process_started |  |  | owner=default |
| 15828 | 2026-08-17T20:32:24.595Z | managed_process_terminal |  |  | owner=default |
| 15829 | 2026-08-17T20:33:00.489Z | state_transition | PREFLIGHT | ABORTED | reason=Read-only pre-P3 mechanism/topology audit complete. Production runtime adapter performs real server-preferred structured validation dispatch with eligibility revalidation and local fallback; current workstation has no live webcodex server/runner topology, and local debug server/runner binaries are stale at commit 3a3abaff72a8 versus frozen-manifest HEAD bc17700e. The one raw ExceptionGroup arose before managed-process admission from a compound probe and did not reproduce with a minimal compound command or individual binary calls, so it is classified as a non-durable tool-call wrapper artifact, not a live P0 product regression. No files modified and no P3 treatment enrolled. |
| 15830 | 2026-08-17T20:33:00.758Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

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
- Events checked: `40`
- Chain head: `3bc949b4d53410e4c0b3ba0117d4f2f8f865b94ee095185a9db1293698747e6b`

# Orchestration Wave 1

- Run: `098643a972ab4ec78dd86f230cd4c87e`
- Wave: `fe928148d2d44aea8c43b9b72f2459e5`
- Objective: Diagnose the live Recovery Tunnel failure shown by the operator after configuring a distinct recoveryTunnelId. Read-only investigation only. Identify whether the failure is caused by tunnel ID/account provisioning, Runtime API Key/auth, proxy/network, tunnel-client invocation, process lifecycle, or missing recovery-specific configuration. Preserve fail-closed behavior and do not mutate source/config/runtime yet. Return the exact local evidence paths/status fields and the smallest next proof needed.
- Mode: `mcp_only`
- Base HEAD: `415cb658f43cbd1d2456f65bf5649ed52b87ab25`
- Worktree fingerprint: `e36cfde19a34657b747f3f908be079df0b9a3da7beebb6f2cd13992806447c0d`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 7027 | 2026-08-16T10:33:06.285Z | run_started |  | PREFLIGHT |  |
| 7028 | 2026-08-16T10:33:09.425Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 7029 | 2026-08-16T10:33:23.220Z | managed_process_admitted |  |  | owner=default |
| 7030 | 2026-08-16T10:33:23.414Z | managed_process_started |  |  | owner=default |
| 7031 | 2026-08-16T10:33:23.810Z | managed_process_terminal |  |  | owner=default |
| 7032 | 2026-08-16T10:33:44.327Z | managed_process_admitted |  |  | owner=default |
| 7033 | 2026-08-16T10:33:44.544Z | managed_process_started |  |  | owner=default |
| 7034 | 2026-08-16T10:33:45.450Z | managed_process_terminal |  |  | owner=default |
| 7035 | 2026-08-16T10:33:57.352Z | managed_process_admitted |  |  | owner=default |
| 7036 | 2026-08-16T10:33:57.524Z | managed_process_started |  |  | owner=default |
| 7037 | 2026-08-16T10:33:58.116Z | managed_process_terminal |  |  | owner=default |
| 7038 | 2026-08-16T10:34:45.325Z | managed_process_admitted |  |  | owner=default |
| 7039 | 2026-08-16T10:34:45.609Z | managed_process_started |  |  | owner=default |
| 7040 | 2026-08-16T10:34:45.994Z | managed_process_terminal |  |  | owner=default |
| 7041 | 2026-08-16T10:34:52.559Z | managed_process_admitted |  |  | owner=default |
| 7042 | 2026-08-16T10:34:52.773Z | managed_process_started |  |  | owner=default |
| 7043 | 2026-08-16T10:34:53.132Z | managed_process_terminal |  |  | owner=default |
| 7044 | 2026-08-16T10:35:07.405Z | managed_process_admitted |  |  | owner=default |
| 7045 | 2026-08-16T10:35:07.639Z | managed_process_started |  |  | owner=default |
| 7046 | 2026-08-16T10:35:08.048Z | managed_process_terminal |  |  | owner=default |
| 7047 | 2026-08-16T10:35:14.598Z | managed_process_admitted |  |  | owner=default |
| 7048 | 2026-08-16T10:35:14.816Z | managed_process_started |  |  | owner=default |
| 7049 | 2026-08-16T10:35:15.184Z | managed_process_terminal |  |  | owner=default |
| 7050 | 2026-08-16T10:35:21.739Z | managed_process_admitted |  |  | owner=default |
| 7051 | 2026-08-16T10:35:21.955Z | managed_process_started |  |  | owner=default |
| 7052 | 2026-08-16T10:35:22.772Z | managed_process_terminal |  |  | owner=default |
| 7053 | 2026-08-16T10:35:55.550Z | failure_observed | PREFLIGHT | PREFLIGHT | failure_class=BASE_DRIFT |
| 7054 | 2026-08-16T10:35:55.666Z | state_transition | PREFLIGHT | REPLAN | reason=BASE_DRIFT; failure_class=BASE_DRIFT |
| 7055 | 2026-08-16T10:35:55.789Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

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
- Events checked: `80`
- Chain head: `179eb5ad157300a163b96251ed6b63fb344a06959da2eb0b963c551d64b03e42`

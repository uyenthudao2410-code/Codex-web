# Orchestration Wave 1

- Run: `f37bb11763e146e1a30b21ce2506d239`
- Wave: `ca1bc25fc6a447548add6fcbadc8081f`
- Objective: Close the remaining exact ChatWeb controller-token measurement gap end-to-end. Determine whether this repository's Electron/ChatWeb host has any authoritative exact token source for the current ChatGPT controller turn, and identify the smallest secure implementation that makes exact controller usage reach the existing canonical ingress without estimation, identity spoofing, or weakening fail-closed semantics. Preserve rolling_5m and the accepted dashboard fixes. Read only in this phase.
- Mode: `mcp_only`
- Base HEAD: `17fcaa360fe4e8d8f5305574b5eb9c2243fd0a02`
- Worktree fingerprint: `1b768ad3cd4d6f6134b7ed60797ddaf37e65320fc4af83d962f664e3002ea19d`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 21841 | 2026-08-19T11:57:21.557Z | run_started |  | PREFLIGHT |  |
| 21842 | 2026-08-19T11:57:22.534Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 21843 | 2026-08-19T11:57:26.006Z | managed_process_admitted |  |  | owner=default |
| 21844 | 2026-08-19T11:57:26.263Z | managed_process_started |  |  | owner=default |
| 21845 | 2026-08-19T11:57:29.280Z | managed_process_terminal |  |  | owner=default |
| 21846 | 2026-08-19T11:57:40.665Z | managed_process_admitted |  |  | owner=chatweb |
| 21847 | 2026-08-19T11:57:40.923Z | managed_process_started |  |  | owner=chatweb |
| 21848 | 2026-08-19T11:57:41.354Z | managed_process_terminal |  |  | owner=chatweb |
| 21849 | 2026-08-19T11:57:48.742Z | managed_process_admitted |  |  | owner=chatweb |
| 21850 | 2026-08-19T11:57:49.182Z | managed_process_started |  |  | owner=chatweb |
| 21851 | 2026-08-19T11:57:50.296Z | managed_process_terminal |  |  | owner=chatweb |
| 21852 | 2026-08-19T11:59:32.368Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 21853 | 2026-08-19T12:00:15.440Z | state_transition | PREFLIGHT | ABORTED | reason=Diagnosis complete: current ChatWeb turn is exactly correlated but has zero controller UsageEvents; Electron host exposes timing/identity only and no authoritative token source. Continue with a separate bounded fail-closed observability bugfix so missing exact controller usage is explicit without fabricating counts. |
| 21854 | 2026-08-19T12:00:15.792Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

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
- Events checked: `14`
- Chain head: `b3951f533e50353dc6fd1ee714ad130806cdae6d0e0cb16a91809012627f579b`

# Orchestration Wave 2

- Run: `073c28d3b76a4a2ba513fe896e13b4ce`
- Wave: `01c3b28b9387429798d1b0a270364f2a`
- Objective: Diagnose the recovery path while the foreground Electron/UI is intentionally left OFF. Do not run any start/restart/kill command and do not manually wake the app. Inspect source and persisted orchestration/runtime evidence only. Determine whether Recovery Supervisor/Recovery Host is designed to auto-reconnect or relaunch the foreground app after it is stopped, what trigger/cadence/ownership conditions control that behavior, and whether the current code contains a defect that would explain the app not reopening automatically after the previous shutdown. Focus on recovery supervisor, recovery host, recovery plane, runtime restart ticket handling, and tests. If a concrete defect is found, return a minimal patch plan but do not execute the patch yet.
- Mode: `bounded_candidate`
- Base HEAD: `885260b404c2c64df1b1afa835963045ac55dbf6`
- Worktree fingerprint: `75133755916f1706ce3ded5977f2ec9ba6ba9ace4798254cae0f7d9ae45bd3aa`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| fba39d953ac6499f9174425afbb4779f | CODEX:luna | luna | luna | gpt-5.6-luna | high | blocked |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 13564 | 2026-08-17T10:28:36.080Z | wave_replanned |  | PREFLIGHT | reason=Previous execute attempt was rejected before mutation because deep_single_lane was incompatible with the Luna route. Replan only changes the execution mode to bounded_candidate; scope, objective, safety constraints, and verification remain unchanged. |
| 13565 | 2026-08-17T10:28:36.448Z | managed_process_admitted |  |  | owner=default |
| 13566 | 2026-08-17T10:28:36.727Z | managed_process_started |  |  | owner=default |
| 13567 | 2026-08-17T10:28:38.139Z | managed_process_terminal |  |  | owner=default |
| 13568 | 2026-08-17T10:28:38.289Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 13569 | 2026-08-17T10:28:38.430Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 13570 | 2026-08-17T10:28:38.578Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 13571 | 2026-08-17T10:28:38.739Z | route_selected | READY | READY | reason=explicit_request; requested=luna; resolved=luna |
| 13572 | 2026-08-17T10:28:38.862Z | state_transition | READY | ROUTED | reason=route_selected |
| 13573 | 2026-08-17T10:28:39.158Z | delegation_started | ROUTED | ROUTED | authority_owner=CODEX:luna |
| 13574 | 2026-08-17T10:28:39.361Z | model_dispatch_started | ROUTED | ROUTED |  |
| 13575 | 2026-08-17T10:28:39.994Z | model_dispatch_finished | ROUTED | ROUTED | failure_class=PROMPT_TOO_LARGE; status=error |
| 13576 | 2026-08-17T10:28:40.255Z | delegation_finished | ROUTED | ROUTED | reason=PROMPT_TOO_LARGE; status=blocked |
| 13577 | 2026-08-17T10:28:40.438Z | failure_observed | ROUTED | ROUTED | failure_class=PROMPT_TOO_LARGE |
| 13578 | 2026-08-17T10:28:40.555Z | state_transition | ROUTED | REPLAN | reason=PROMPT_TOO_LARGE; failure_class=PROMPT_TOO_LARGE |
| 13579 | 2026-08-17T10:28:40.687Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

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
- Events checked: `59`
- Chain head: `a4ce1f7f9a7e866bec820b68ffccf4fbe374d690d6003df20d62ba30654d07ab`

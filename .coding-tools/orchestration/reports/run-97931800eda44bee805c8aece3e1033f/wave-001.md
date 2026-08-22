# Orchestration Wave 1

- Run: `97931800eda44bee805c8aece3e1033f`
- Wave: `ca5e6e06cbd84ffba25b7469b1b3cfd1`
- Objective: Diagnose the single failing T2.1 TruthSnapshot integration regression after the call-site change from unsupported wave= to wave_id=. Read only the current source and tests; identify the exact likely failing assertion/setup and the smallest corrective change. Do not mutate files, do not run package/release/restart, and do not expand beyond resources/coding-tools-mcp/coding_tools_mcp/mcp_http_handler.py, truth_snapshot.py, orchestration_ledger.py, orchestration_control.py, and resources/coding-tools-mcp/tests/test_truth_snapshot.py plus any directly referenced test helper.
- Objective revision: `1`
- Objective SHA-256: `0de6f96140cabf1b7e7c18718cac3a2ac34c4fefbdbfc46bef51130101b3c33c`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `9eb05072e54ffca9576e23c2d4a4f4e14034bddc`
- Worktree fingerprint: `87e50fccecdb18418e080235a97bea53a8178d724ef8c1eedfe1fa287a692e4f`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 26271 | 2026-08-21T08:17:33.065Z | run_started |  | PREFLIGHT |  |
| 26272 | 2026-08-21T08:17:34.074Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 26273 | 2026-08-21T08:17:50.813Z | managed_process_admitted |  |  | owner=default |
| 26274 | 2026-08-21T08:17:51.179Z | managed_process_started |  |  | owner=default |
| 26275 | 2026-08-21T08:17:51.961Z | managed_process_terminal |  |  | owner=default |
| 26316 | 2026-08-21T16:53:49.494Z | failure_observed | PREFLIGHT | PREFLIGHT | failure_class=BASE_DRIFT |
| 26317 | 2026-08-21T16:53:49.668Z | state_transition | PREFLIGHT | REPLAN | reason=BASE_DRIFT; failure_class=BASE_DRIFT |
| 26318 | 2026-08-21T16:53:49.842Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

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
- Events checked: `27`
- Chain head: `91d8f90c113403e39fbfee1e99f2aa47cb9bb21ed5b3692600189c0e0e4deb65`

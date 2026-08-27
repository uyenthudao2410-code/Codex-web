# Orchestration Wave 2

- Run: `8b8e5b92bf814969bbd21f1577056275`
- Wave: `a497621109d94f67b3216c8b0c74b1cd`
- Objective: At exact Git HEAD 898d57454f9a5113d8aa3f56d1650e4b3e0d6924, produce a read-only deterministic proof for the exact live supervisor replacement test that previously failed at teardown. Do not modify source, do not clean/reset/revert, do not touch ledger.sqlite3 manually, do not restart runtime, do not push/tag/release/deploy. If the focused test passes, leave this wave at ACCEPTING for ChatWeb Sol final acceptance.
- Objective revision: `2`
- Objective SHA-256: `d97e5862b9a589456777f96882de7af6bc803888ca4bdab8dc67b49303463672`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `898d57454f9a5113d8aa3f56d1650e4b3e0d6924`
- Worktree fingerprint: `f0f534fc13eb8768dd1f47c07466cf557157d03e175f0c3ef5383ceb67c4b197`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 30778 | 2026-08-26T13:29:40.428Z | wave_replanned |  | PREFLIGHT | reason=The prior full npm test proof failed only during Windows teardown with EPERM in removeTempTree for the real Coding MCP replacement fixture, while the immediately preceding same-HEAD npm test passed. New evidence strategy: run the exact failing test case alone to distinguish the functional supervisor assertions from a nondeterministic cleanup-handle race; do not replay the unchanged full command. |
| 30779 | 2026-08-26T13:29:40.604Z | observation_span_recorded |  |  |  |
| 30780 | 2026-08-26T13:29:41.873Z | observation_span_recorded |  |  |  |
| 30781 | 2026-08-26T13:29:42.039Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 30782 | 2026-08-26T13:29:42.353Z | managed_process_admitted |  |  | owner=default |
| 30783 | 2026-08-26T13:29:42.604Z | managed_process_started |  |  | owner=default |
| 30784 | 2026-08-26T13:29:53.278Z | managed_process_terminal |  |  | owner=default |
| 30785 | 2026-08-26T13:29:53.435Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 30786 | 2026-08-26T13:29:53.566Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 30787 | 2026-08-26T13:29:53.711Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 30788 | 2026-08-26T13:29:53.856Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 30789 | 2026-08-26T13:29:53.986Z | state_transition | READY | ROUTED | reason=route_selected |
| 30790 | 2026-08-26T13:29:54.185Z | observation_span_recorded |  |  |  |
| 30791 | 2026-08-26T13:29:55.003Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=7886eaf6f58443b9a28f118879c13503 |
| 30792 | 2026-08-26T13:29:55.135Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 30793 | 2026-08-26T13:29:55.951Z | observation_span_recorded |  |  |  |
| 30794 | 2026-08-26T13:29:56.195Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=7886eaf6f58443b9a28f118879c13503 |
| 30795 | 2026-08-26T13:29:56.338Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 30796 | 2026-08-26T13:29:57.279Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=89af4ce87f328d17f2d2b48d07158ae33bee724be5e1018570d55ed4a6e23342 |
| 30797 | 2026-08-26T13:29:57.663Z | managed_process_admitted |  |  | owner=default |
| 30798 | 2026-08-26T13:29:57.920Z | managed_process_started |  |  | owner=default |
| 30799 | 2026-08-26T13:30:08.643Z | managed_process_terminal |  |  | owner=default |
| 30800 | 2026-08-26T13:30:18.121Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=89af4ce87f328d17f2d2b48d07158ae33bee724be5e1018570d55ed4a6e23342 |
| 30801 | 2026-08-26T13:30:18.400Z | observation_span_recorded |  |  |  |
| 30802 | 2026-08-26T13:30:18.520Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 30803 | 2026-08-26T13:45:57.119Z | quality_outcome_recorded |  |  |  |
| 30804 | 2026-08-26T13:45:57.234Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 30805 | 2026-08-26T13:45:57.425Z | observation_span_recorded |  |  |  |
| 30806 | 2026-08-26T13:45:57.621Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 89af4ce87f328d17f2d2b48d07158ae33bee724be5e1018570d55ed4a6e23342 | False | 20453 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 653532dc7e624fb8acc212bc846162f6 | accepted | 898d57454f9a5113d8aa3f56d1650e4b3e0d6924 | d5d412b62bef86f6b3dba820127ebc5d994b2a469ac673a9d43a35fbb092e049 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `56`
- Chain head: `648d9eae3cd8283c36399c68d09e3e46aa66b3c965fc2791e03c1b3f452c8072`

# Orchestration Wave 1

- Run: `143f79f738424bf0b4b6c597dc1e58c6`
- Wave: `9bf82ce8a7a147778c4e3f6acc1fc712`
- Objective: Selectively commit and push the accepted P0.2 current-session closure evidence on main. Preconditions: current source HEAD is acaa3582052ab6836ade7b55bd1ff2178ebc5117 and docs/PRODUCTION_CLOSURE_ROLLOUT.md has accepted P0.2 closure changes. Stage only docs/PRODUCTION_CLOSURE_ROLLOUT.md, .coding-tools/orchestration/ledger.sqlite3, and report directories run-c6235e7dfefe4df9938bf6d0b4c11bca, run-1151d304b5864708ad6f694d9fd91b6c, run-dfc0f3be347540989489dbf10574b48f, run-44add57e789e4b14bcef1588f0e371b9, run-f8219ca3acf8470ca39a86bedf546dad, run-0d3dc1349077416680946c08c76875ef, run-f64f9aac35d8459e903524953b3e0943, run-cb0a385d21464d02a9cb557a46433dea. Explicitly exclude .coding-tools/evaluation/chatweb-host-observations.jsonl, .coding-tools/performance.json, .coding-tools/task-history.json, .coding-tools/task-state.json, SQLite -wal/-shm, run-6ed664ad4eb2419ab27ca659519933a4 and all other unrelated report directories. Before commit require git diff --cached --name-only contains only the allowlist prefixes and includes ledger.sqlite3 and the living plan; require git diff --check --cached PASS. Commit message: docs: close P0.2 installed recovery acceptance. Push main to origin. After push print HEAD and origin/main plus concise status. Do not stage/reset/clean unrelated changes.
- Mode: `mcp_only`
- Base HEAD: `acaa3582052ab6836ade7b55bd1ff2178ebc5117`
- Worktree fingerprint: `f49d7a1f6ef5e3261f5ef0d871708cf55139f9f2ea2f124400f512bc953c1856`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 13068 | 2026-08-17T09:07:04.038Z | run_started |  | PREFLIGHT |  |
| 13069 | 2026-08-17T09:07:04.579Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 13070 | 2026-08-17T09:07:04.814Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 13071 | 2026-08-17T09:07:04.996Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 13072 | 2026-08-17T09:07:05.233Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 13073 | 2026-08-17T09:07:05.418Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 13074 | 2026-08-17T09:07:05.765Z | state_transition | READY | ROUTED | reason=route_selected |
| 13075 | 2026-08-17T09:07:06.439Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=78cad12b5a2d4ee3a7a783b467a500df |
| 13076 | 2026-08-17T09:07:06.610Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 13077 | 2026-08-17T09:07:07.123Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=78cad12b5a2d4ee3a7a783b467a500df |
| 13078 | 2026-08-17T09:07:07.293Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 13079 | 2026-08-17T09:07:07.677Z | proof_cache_miss |  |  | reason=cold; stage_id=check:6a5eb1aba724c541; input_fingerprint=f493a59b8171d6dc04679b6b789a7d6b24f2ed46ef5b8b066af2f965fc8e4677 |
| 13080 | 2026-08-17T09:07:08.100Z | managed_process_admitted |  |  | owner=default |
| 13081 | 2026-08-17T09:07:08.608Z | managed_process_started |  |  | owner=default |
| 13082 | 2026-08-17T09:07:09.409Z | managed_process_terminal |  |  | owner=default |
| 13083 | 2026-08-17T09:07:10.439Z | proof_recorded |  |  | stage_id=check:6a5eb1aba724c541; status=failed; cache_hit=False; input_fingerprint=f493a59b8171d6dc04679b6b789a7d6b24f2ed46ef5b8b066af2f965fc8e4677 |
| 13084 | 2026-08-17T09:07:10.633Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 13085 | 2026-08-17T09:07:10.818Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 13086 | 2026-08-17T09:07:11.043Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:6a5eb1aba724c541 | failed | f493a59b8171d6dc04679b6b789a7d6b24f2ed46ef5b8b066af2f965fc8e4677 | False | 1712 | 128 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `63`
- Chain head: `3a6ae1aa9e8b37ea20ece7e13cce08c8527c058e728b95fefd7302871c363547`

# Orchestration Wave 1

- Run: `b433f3b24cd049a4a10b3ebe90e50bf3`
- Wave: `4428515f7a1348c8bc4ec5bac75ff040`
- Objective: Forensic-only execution for the accidental secondary orchestration ledger. Run bounded READ-ONLY SQLite comparison between canonical .coding-tools/orchestration/ledger.sqlite3 and resources/coding-tools-mcp/.coding-tools/orchestration/ledger.sqlite3. Do not modify either database or any repository file. Report integrity_check, schema/table counts, DB size, run/wave/event/proof/checkpoint and P5 table counts where present, min/max timestamps/sequence where available, and set differences of durable primary identifiers (run_id, wave_id, event_id, proof_id, checkpoint_id, experiment_id/assignment_id where applicable). For any identifiers unique to the nested DB, return only bounded content-free provenance fields needed to classify them: ids, status, task_id, timestamps, provenance/type flags and workspace/source identity hashes if present; do not dump prompts, stdout/stderr, secrets, raw payloads, or large metadata. Determine whether the nested ledger contains unique real project evidence, duplicate rows, or only test/synthetic/empty schema evidence. Do not delete/migrate/archive/edit/commit/push/restart or alter P5 state.
- Objective revision: `1`
- Objective SHA-256: `54eea1eeaba4540632ddf2e4c5b19364d009f44c88e722d5a133f584811a7765`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `6d45e5bb00451f6d4418ed0b4e7c1dad185b0ac0`
- Worktree fingerprint: `3f772125e2ee9ee0241440aa9afbe1fe02c393b08d367e8b1634999b9fc3b755`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 27148 | 2026-08-22T13:52:02.936Z | run_started |  | PREFLIGHT |  |
| 27149 | 2026-08-22T13:52:03.220Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 27150 | 2026-08-22T13:52:03.386Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 27151 | 2026-08-22T13:52:03.536Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 27152 | 2026-08-22T13:52:03.676Z | state_transition | READY | ROUTED | reason=route_selected |
| 27153 | 2026-08-22T13:52:04.552Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=98be3ec89325435b8b8b94d45e8c5a98 |
| 27154 | 2026-08-22T13:52:04.703Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 27155 | 2026-08-22T13:52:05.468Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=98be3ec89325435b8b8b94d45e8c5a98 |
| 27156 | 2026-08-22T13:52:05.621Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 27157 | 2026-08-22T13:52:06.301Z | proof_cache_miss |  |  | reason=cold; stage_id=check:1cb5a1418ac98ef1; input_fingerprint=5e227bfac519e1f43f389c88e530c7d39fd1bc9bb91cae80051b36e5ce743cfe |
| 27158 | 2026-08-22T13:52:06.466Z | failure_observed | PROVING | PROVING | failure_class=PERMISSION_REQUIRED |
| 27159 | 2026-08-22T13:52:06.616Z | state_transition | PROVING | REPLAN | reason=PERMISSION_REQUIRED; failure_class=PERMISSION_REQUIRED |
| 27160 | 2026-08-22T13:52:06.777Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

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
- Events checked: `44`
- Chain head: `59aee1fe0789a7a2822109b3793c353ec84e7de10a0520299ba2f96ff6e60572`

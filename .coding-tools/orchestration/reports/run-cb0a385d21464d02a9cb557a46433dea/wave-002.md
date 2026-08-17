# Orchestration Wave 2

- Run: `cb0a385d21464d02a9cb557a46433dea`
- Wave: `f9e3b31a99c64d098aa2741ff2a158b0`
- Objective: Resume and finish the isolated compute-first/server-first measurement hardening on branch automation/compute-placement-evaluation-20260817 without touching main/Recovery/installer/external Windows state. Preserve the existing uncommitted Python evaluation-plane WIP in this worktree and treat it as candidate code to validate, not as accepted proof. Complete the smallest coherent implementation that makes local_only versus server_preferred compute placement causally measurable: first ensure tests import the worktree-local coding_tools_mcp package; keep delayed controller observation and actual placement ledger evidence fail-closed and content-free; wire a real study-only compute placement policy into WebCodex read-only Cargo validation with production default server_preferred unchanged; expose actual policy/placement/fallback evidence in validation results without leaking runner/project secrets; correct stale shadow-only semantics if live dispatch proves that field is false; add focused Rust/Python/schema tests; do not change model routing authority and keep automatic activation false. Do not commit, push, tag, release, restart runtime, edit .coding-tools evidence, or touch resources/recovery-supervisor, recovery tests, installer/package files, tmp/P0.2 files, or external system state.
- Mode: `mcp_only`
- Base HEAD: `acaa3582052ab6836ade7b55bd1ff2178ebc5117`
- Worktree fingerprint: `d616be680020a4a08fc31fc3faebeb18de79383ed04796edf35604d5e0d7e857`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 13045 | 2026-08-17T09:05:48.094Z | wave_replanned |  | PREFLIGHT | reason=Concurrent unrelated compute-placement/runtime-evidence activity changed the worktree fingerprint after preflight while Git source HEAD remained acaa3582052ab6836ade7b55bd1ff2178ebc5117. This new wave is fenced to the current snapshot and modifies only docs/PRODUCTION_CLOSURE_ROLLOUT.md; it preserves all unrelated concurrent source/evidence changes. |
| 13046 | 2026-08-17T09:05:48.566Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 13047 | 2026-08-17T09:05:48.817Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 13048 | 2026-08-17T09:05:49.022Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 13049 | 2026-08-17T09:05:49.249Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 13050 | 2026-08-17T09:05:49.433Z | state_transition | READY | ROUTED | reason=route_selected |
| 13051 | 2026-08-17T09:05:49.909Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=ff74eb107b9a44a38da63d29c1ffd935 |
| 13052 | 2026-08-17T09:05:50.086Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 13053 | 2026-08-17T09:05:50.602Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=ff74eb107b9a44a38da63d29c1ffd935 |
| 13054 | 2026-08-17T09:05:50.736Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 13055 | 2026-08-17T09:05:51.138Z | proof_cache_miss |  |  | reason=cold; stage_id=check:cec25b3c7ab79e8e; input_fingerprint=709aaab83d71f8d2d2911a83e354387be069c0181f89e8bc8d2d7e375dc22a3e |
| 13056 | 2026-08-17T09:05:51.474Z | managed_process_admitted |  |  | owner=default |
| 13057 | 2026-08-17T09:05:51.786Z | managed_process_started |  |  | owner=default |
| 13058 | 2026-08-17T09:05:52.294Z | managed_process_terminal |  |  | owner=default |
| 13059 | 2026-08-17T09:05:52.645Z | proof_recorded |  |  | stage_id=check:cec25b3c7ab79e8e; status=passed; cache_hit=False; input_fingerprint=709aaab83d71f8d2d2911a83e354387be069c0181f89e8bc8d2d7e375dc22a3e |
| 13060 | 2026-08-17T09:05:52.771Z | proof_cache_miss |  |  | reason=cold; stage_id=check:c44800151188b679; input_fingerprint=33003cd268d36379fcd163b774ee06c11813e0551af47d4542b87c300bf7c468 |
| 13061 | 2026-08-17T09:05:53.035Z | managed_process_admitted |  |  | owner=default |
| 13062 | 2026-08-17T09:05:53.310Z | managed_process_started |  |  | owner=default |
| 13063 | 2026-08-17T09:05:53.738Z | managed_process_terminal |  |  | owner=default |
| 13064 | 2026-08-17T09:05:54.083Z | proof_recorded |  |  | stage_id=check:c44800151188b679; status=passed; cache_hit=False; input_fingerprint=33003cd268d36379fcd163b774ee06c11813e0551af47d4542b87c300bf7c468 |
| 13065 | 2026-08-17T09:05:54.532Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 13066 | 2026-08-17T09:06:05.294Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 13067 | 2026-08-17T09:06:05.748Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:cec25b3c7ab79e8e | passed | 709aaab83d71f8d2d2911a83e354387be069c0181f89e8bc8d2d7e375dc22a3e | False | 1218 | 0 |
| check:c44800151188b679 | passed | 33003cd268d36379fcd163b774ee06c11813e0551af47d4542b87c300bf7c468 | False | 1036 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 71c449326e804ff180ba8149cf199876 | accepted | acaa3582052ab6836ade7b55bd1ff2178ebc5117 | 8291752ffbf0d7171e48c9643234498a8050a86ff73492d6e082a5fdb4029f86 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `28`
- Chain head: `9d3828639581c6a2fc03c00744dae04cb63a1688f4e1b7cd3f7a2ff7883679dc`

# Orchestration Wave 1

- Run: `c0e53aa707614fdc83e1a51a7e3e7d4a`
- Wave: `94e5d0d53ff9445b9377c58cff2226da`
- Objective: Design the final non-linker-heavy R2B behavior oracle on the current accepted implementation. Do not modify files or run commands in prepare. Inspect only the server-first compute placement adapter, Cargo validation dispatch wiring, existing server_first_* tests, webcodex-core placement policy/tests, and Cargo target layout. Determine whether the four required behaviors (distinct opted-in exact target dispatch; source runner never chosen as compute target; ineligible candidates fall back to source; offload excludes cargo_fmt/short/sandboxed validation) can be proven by an existing small package/target. If not, identify the smallest pure helper boundary that can be moved or exposed to webcodex-core for lightweight tests without changing runtime semantics. Preserve all unrelated WIP and do not propose the root monolithic test binary.
- Mode: `mcp_only`
- Base HEAD: `48e91a1cc12e9d6fe9c71f053404476132007468`
- Worktree fingerprint: `17c1bd723884734432cf64b695efcad0d50dec34660ec2b42ca856c0916ca9e6`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 8750 | 2026-08-16T14:36:07.826Z | run_started |  | PREFLIGHT |  |
| 8751 | 2026-08-16T14:36:13.073Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 8752 | 2026-08-16T14:37:58.649Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 8753 | 2026-08-16T14:37:58.798Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 8754 | 2026-08-16T14:37:58.905Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 8755 | 2026-08-16T14:37:59.185Z | state_transition | READY | ROUTED | reason=route_selected |
| 8756 | 2026-08-16T14:37:59.585Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=5884fd3c3170450891d1c3f8a9870217 |
| 8757 | 2026-08-16T14:37:59.697Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 8758 | 2026-08-16T14:38:00.188Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=5884fd3c3170450891d1c3f8a9870217 |
| 8759 | 2026-08-16T14:38:00.319Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 8760 | 2026-08-16T14:38:00.737Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:810e75f0d3dee10e; input_fingerprint=66d62399f3af0e001489d9a859e40ac75ef5d41c275a4ec97ee194c83dc4ea11 |
| 8761 | 2026-08-16T14:38:01.032Z | managed_process_admitted |  |  | owner=default |
| 8762 | 2026-08-16T14:38:01.256Z | managed_process_started |  |  | owner=default |
| 8763 | 2026-08-16T14:38:06.836Z | managed_process_terminal |  |  | owner=default |
| 8764 | 2026-08-16T14:38:07.088Z | proof_recorded |  |  | stage_id=check:810e75f0d3dee10e; status=failed; cache_hit=False; input_fingerprint=66d62399f3af0e001489d9a859e40ac75ef5d41c275a4ec97ee194c83dc4ea11 |
| 8765 | 2026-08-16T14:38:07.221Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 8766 | 2026-08-16T14:38:07.358Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 8767 | 2026-08-16T14:38:07.521Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:810e75f0d3dee10e | failed | 66d62399f3af0e001489d9a859e40ac75ef5d41c275a4ec97ee194c83dc4ea11 | False | 6072 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `50`
- Chain head: `24afe0f64236a2cc0eee21d43aa0e2eeb45f0f31649dfeba38e623a42816a5b0`
